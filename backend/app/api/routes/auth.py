from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from app.db.database import get_db
from app.schemas.usuario import UsuarioRegistro, UsuarioLogin
from app.models.usuario import Usuario, PerfilUsuario

router = APIRouter(prefix="/auth", tags=["Autenticación"])

# Configuración del contexto para encriptar contraseñas con bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


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
    db.commit()
    db.refresh(nuevo_usuario)
    
    # 5. Crear automáticamente su perfil de usuario vacío enlazado
    nuevo_perfil = PerfilUsuario(usuario_id=nuevo_usuario.id_usuario)
    db.add(nuevo_perfil)
    db.commit()
    
    return {
        "mensaje": "Usuario registrado exitosamente",
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
    if not db_user or not pwd_context.verify(user.password, db_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Correo o contraseña incorrectos."
        )
    
    return {
        "mensaje": "Inicio de sesión exitoso",
        "usuario": {
            "id_usuario": db_user.id_usuario,
            "nombre": db_user.nombre,
            "correo": db_user.correo,
            "carrera": db_user.carrera
        }
    }