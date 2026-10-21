from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.usuario import Usuario, PerfilUsuario
from app.schemas.perfil import PerfilUpdate, PerfilOut

router = APIRouter(prefix="/perfil", tags=["Perfil de Usuario"])


@router.get("/{usuario_id}", response_model=PerfilOut)
def obtener_perfil(usuario_id: int, db: Session = Depends(get_db)):
    """
    Obtiene los datos personales y el perfil extendido (habilidades, bio, intereses) de un usuario.
    """
    usuario = db.query(Usuario).filter(Usuario.id_usuario == usuario_id).first()
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado."
        )
    
    perfil = db.query(PerfilUsuario).filter(PerfilUsuario.usuario_id == usuario_id).first()
    if not perfil:
        perfil = PerfilUsuario(usuario_id=usuario_id, datos_crudos={}, atributos_dinamicos={})
        db.add(perfil)
        db.commit()
        db.refresh(perfil)
    
    return PerfilOut(
        usuario_id=usuario.id_usuario,
        nombre=usuario.nombre,
        correo=usuario.correo,
        carrera=usuario.carrera,
        estado_geografico=usuario.estado_geografico,
        municipio=usuario.municipio,
        rol_sistema=usuario.rol_sistema,
        datos_crudos=perfil.datos_crudos or {},
        atributos_dinamicos=perfil.atributos_dinamicos or {}
    )


@router.put("/{usuario_id}", response_model=PerfilOut)
def actualizar_perfil(usuario_id: int, datos: PerfilUpdate, db: Session = Depends(get_db)):
    """
    Actualiza la información dinámica del perfil del usuario dentro de la columna JSON 'datos_crudos'.
    """
    usuario = db.query(Usuario).filter(Usuario.id_usuario == usuario_id).first()
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado."
        )
    
    perfil = db.query(PerfilUsuario).filter(PerfilUsuario.usuario_id == usuario_id).first()
    if not perfil:
        perfil = PerfilUsuario(usuario_id=usuario_id, datos_crudos={}, atributos_dinamicos={})
        db.add(perfil)
        db.commit()
        db.refresh(perfil)
    
    # Fusionar los datos actuales con los nuevos datos enviados
    datos_actuales = dict(perfil.datos_crudos or {})
    nuevos_datos = datos.model_dump(exclude_unset=True)
    datos_actuales.update(nuevos_datos)
    
    # Asignar de nuevo el diccionario para que SQLAlchemy detecte el cambio en el campo JSON
    perfil.datos_crudos = datos_actuales
    
    db.commit()
    db.refresh(perfil)
    
    return PerfilOut(
        usuario_id=usuario.id_usuario,
        nombre=usuario.nombre,
        correo=usuario.correo,
        carrera=usuario.carrera,
        estado_geografico=usuario.estado_geografico,
        municipio=usuario.municipio,
        rol_sistema=usuario.rol_sistema,
        datos_crudos=perfil.datos_crudos or {},
        atributos_dinamicos=perfil.atributos_dinamicos or {}
    )