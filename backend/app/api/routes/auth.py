from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from app.db.database import get_db
from app.schemas.usuario import UsuarioRegistro, UsuarioLogin
from app.models.usuario import Usuario, PerfilUsuario
from app.core.security import create_access_token, get_current_user

router = APIRouter(prefix="/auth", tags=["Autenticación"])

# Configuración del contexto para encriptar contraseñas con bcrypt
pwd_context = CryptContext(schemes=["bcrypt_sha256", "bcrypt"], deprecated="auto")


@router.post("/registro")
def registrar_usuario(user: UsuarioRegistro, db: Session = Depends(get_db)):
    # 1. Validar que el correo no esté registrado previamente
    usuario_existente = db.query(Usuario).filter(Usuario.correo == user.correo).first()
    if usuario_existente:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El correo ya se encuentra registrado."
        )
    
    # 2. Hashear la contraseña recibida
    hashed_password = pwd_context.hash(user.password)
    
    # 3. Crear el objeto Usuario con sus campos
    nuevo_usuario = Usuario(
        nombre=user.nombre,
        correo=user.correo,
        carrera=user.carrera,
        estado_geografico=getattr(user, "estado_geografico", None),
        municipio=getattr(user, "municipio", None),
        password_hash=hashed_password
    )
    
    # 4. Insertar y confirmar el usuario en MySQL
    db.add(nuevo_usuario)
    db.flush()
    db.add(PerfilUsuario(usuario_id=nuevo_usuario.id_usuario))
    token = create_access_token(nuevo_usuario.id_usuario)
    db.commit()
    db.refresh(nuevo_usuario)
    
    return {
        "mensaje": "Usuario registrado exitosamente",
        "access_token": token,
        "token_type": "bearer",
        "usuario": {
            "id_usuario": nuevo_usuario.id_usuario,
            "nombre": nuevo_usuario.nombre,
            "correo": nuevo_usuario.correo,
            "carrera": nuevo_usuario.carrera
        }
    }


@router.post("/login")
def login_usuario(user: UsuarioLogin, db: Session = Depends(get_db)):
    # 1. Buscar el usuario en la base de datos por correo
    db_user = db.query(Usuario).filter(Usuario.correo == user.correo).first()
    
    # 2. Comprobar que el usuario exista y que la contraseña coincida con el hash
    replacement = None
    verified = False
    if db_user:
        scheme = pwd_context.identify(db_user.password_hash)
        if scheme == "bcrypt" and len(user.password.encode("utf-8")) > 72:
            raise HTTPException(422, "La cuenta usa bcrypt heredado: más de 72 bytes no pueden verificarse sin truncamiento. Requiere restablecimiento seguro de contraseña.")
        if scheme:
            try:
                verified, replacement = pwd_context.verify_and_update(user.password, db_user.password_hash)
            except (ValueError, TypeError):
                verified = False
    if not verified:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Correo o contraseña incorrectos."
        )
    
    if db_user.estado_cuenta != "Activa":
        raise HTTPException(status_code=403, detail="Cuenta inactiva.")
    if replacement:
        db_user.password_hash = replacement
        db.commit()
    return {
        "mensaje": "Inicio de sesión exitoso",
        "access_token": create_access_token(db_user.id_usuario),
        "token_type": "bearer",
        "usuario": {
            "id_usuario": db_user.id_usuario,
            "nombre": db_user.nombre,
            "correo": db_user.correo,
            "carrera": db_user.carrera
        }
    }


@router.get("/me")
def obtener_sesion(actor: Usuario = Depends(get_current_user)):
    return {"id_usuario": actor.id_usuario, "nombre": actor.nombre,
            "correo": actor.correo, "carrera": actor.carrera}
