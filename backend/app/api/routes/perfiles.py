from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import Optional
from app.db.database import get_db
from app.models.usuario import Usuario, PerfilUsuario
from app.schemas.perfil import PerfilPublicoOut, PerfilUpdate, PerfilOut

router = APIRouter(prefix="/perfil", tags=["Perfil de Usuario"])


def crear_perfil_publico(usuario, perfil):
    datos_crudos = perfil.datos_crudos or {} if perfil else {}
    configuracion = datos_crudos.get("visibilidad", {})
    visibilidad = {
        "fortalezas": True,
        "intereses": True,
        "disponibilidad": True,
        "reforzar": False,
        "correo": False,
        **configuracion,
    }
    datos_publicos = {
        "visibilidad": visibilidad,
        "semestre": datos_crudos.get("semestre", 1),
        "pausado": bool(datos_crudos.get("pausado", False)),
    }
    for campo in ("fortalezas", "intereses", "disponibilidad", "reforzar", "bio"):
        if campo == "bio" or visibilidad.get(campo, False):
            if campo in datos_crudos:
                datos_publicos[campo] = datos_crudos[campo]

    return PerfilPublicoOut(
        usuario_id=usuario.id_usuario,
        nombre=usuario.nombre,
        carrera=usuario.carrera,
        estado_geografico=usuario.estado_geografico,
        municipio=usuario.municipio,
        correo=usuario.correo if visibilidad["correo"] else None,
        datos_crudos=datos_publicos,
        atributos_dinamicos={},
    )


@router.get("/estudiantes/", response_model=list[PerfilPublicoOut])
def listar_estudiantes(
    q: str = Query("", max_length=100),
    exclude_id: Optional[int] = Query(None, gt=0),
    limit: int = Query(100, ge=1, le=200),
    db: Session = Depends(get_db),
):
    query = db.query(Usuario, PerfilUsuario).outerjoin(
        PerfilUsuario, PerfilUsuario.usuario_id == Usuario.id_usuario
    ).filter(Usuario.estado_cuenta == "Activa")

    if exclude_id:
        query = query.filter(Usuario.id_usuario != exclude_id)
    if q.strip():
        termino = f"%{q.strip()}%"
        query = query.filter(
            (Usuario.nombre.ilike(termino)) | (Usuario.carrera.ilike(termino))
        )

    estudiantes = []
    for usuario, perfil in query.order_by(Usuario.id_usuario.desc()).limit(limit).all():
        perfil_publico = crear_perfil_publico(usuario, perfil)
        if perfil_publico.datos_crudos["pausado"]:
            continue
        estudiantes.append(perfil_publico)
    return estudiantes


@router.get("/publico/{usuario_id}", response_model=PerfilPublicoOut)
def obtener_perfil_publico(usuario_id: int, db: Session = Depends(get_db)):
    usuario = db.query(Usuario).filter(Usuario.id_usuario == usuario_id).first()
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado.",
        )

    perfil = db.query(PerfilUsuario).filter(PerfilUsuario.usuario_id == usuario_id).first()
    perfil_publico = crear_perfil_publico(usuario, perfil)
    if perfil_publico.datos_crudos["pausado"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Este perfil no está disponible.",
        )
    return perfil_publico


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
    
    nuevos_datos = datos.model_dump(exclude_unset=True)
    datos_crudos = nuevos_datos.pop("datos_crudos", None)
    nombre = nuevos_datos.pop("nombre", None)
    carrera = nuevos_datos.pop("carrera", None)

    if nombre is not None:
        usuario.nombre = nombre
    if carrera is not None:
        usuario.carrera = carrera

    # Fusionar los datos actuales con los nuevos datos enviados
    datos_actuales = dict(perfil.datos_crudos or {})
    if datos_crudos is not None:
        datos_actuales.update(datos_crudos)
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