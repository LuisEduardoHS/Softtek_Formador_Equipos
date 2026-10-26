from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import Optional
from app.db.database import get_db
from app.models.usuario import Usuario, PerfilUsuario
from app.schemas.perfil import PerfilPublicoOut, PerfilUpdate, PerfilOut
from app.schemas.profile_data import safe_profile_data
from app.core.security import get_current_user, require_self
from fastapi.concurrency import run_in_threadpool
from app.schemas.ai_integration import ProfileInterpretRequest, ProfileReviewed
from app.services.ai.profile_parser import ProfileParser
from app.services.ai.ollama_client import OllamaClient, OllamaServiceError
from app.services.ai.schemas import StructuredProfile
from app.services.ai.integration import content_revision, utc_now, process_profile_embedding, PROFILE_CONFIRMED_STATES

router = APIRouter(prefix="/perfil", tags=["Perfil de Usuario"])


def _own_profile(db: Session, actor: Usuario) -> PerfilUsuario:
    perfil = db.get(PerfilUsuario, actor.id_usuario)
    if perfil is None:
        perfil = PerfilUsuario(usuario_id=actor.id_usuario, datos_crudos={}, atributos_dinamicos={})
        db.add(perfil)
        db.flush()
    return perfil


def _private_profile(usuario: Usuario, perfil: PerfilUsuario) -> PerfilOut:
    structured = None
    if perfil.perfil_estado_ia in PROFILE_CONFIRMED_STATES:
        try:
            structured = StructuredProfile.model_validate(perfil.perfil_estructurado_ia).model_dump(mode="json")
        except (ValueError, TypeError):
            pass  # A damaged legacy structure is not usable confirmed evidence.
    return PerfilOut(
        usuario_id=usuario.id_usuario, nombre=usuario.nombre, correo=usuario.correo,
        carrera=usuario.carrera, estado_geografico=usuario.estado_geografico,
        municipio=usuario.municipio, rol_sistema=usuario.rol_sistema,
        datos_crudos=safe_profile_data(perfil.datos_crudos),
        atributos_dinamicos=perfil.atributos_dinamicos if isinstance(perfil.atributos_dinamicos, dict) else {},
        perfil_estructurado_ia=structured,
        perfil_estado_ia=perfil.perfil_estado_ia,
    )


@router.post("/interpretar")
async def interpretar_perfil(payload: ProfileInterpretRequest,
                            db: Session = Depends(get_db),
                            actor: Usuario = Depends(get_current_user)):
    perfil = _own_profile(db, actor)
    raw = safe_profile_data(perfil.datos_crudos)
    raw["borrador_texto_ia"] = payload.model_dump()
    perfil.datos_crudos = raw
    perfil.perfil_borrador_ia = None
    previous_state = perfil.perfil_estado_ia
    previous_revision = perfil.perfil_fuente_revision
    perfil.perfil_estado_ia = "interpretando"
    db.commit()
    description = (f"Habilidades declaradas: {payload.fortalezas}\n"
                   f"Áreas que desea reforzar: {payload.reforzar}\n"
                   f"Intereses: {payload.intereses}")
    try:
        parsed = await run_in_threadpool(
            ProfileParser(ai=OllamaClient(timeout=60)).parse_profile, description
        )
    except OllamaServiceError as error:
        db.refresh(perfil, with_for_update=True)
        # Do not overwrite a confirmation made while this request was running.
        if perfil.perfil_estado_ia == "interpretando" and perfil.perfil_fuente_revision == previous_revision:
            perfil.perfil_estado_ia = (previous_state if previous_state in PROFILE_CONFIRMED_STATES
                                      else "interpretacion_pendiente")
        db.commit()
        raise HTTPException(status_code=503, detail="La interpretación no está disponible. Conservamos el borrador; puedes revisar manualmente y reintentar.") from error
    db.refresh(perfil, with_for_update=True)
    if perfil.perfil_estado_ia != "interpretando" or perfil.perfil_fuente_revision != previous_revision:
        raise HTTPException(409, "El perfil cambió durante el análisis. Conservamos los datos actuales; revisa o reintenta.")
    perfil.perfil_borrador_ia = parsed.model_dump(mode="json")
    perfil.perfil_estado_ia = "pendiente_revision"
    db.commit()
    return {
        "fortalezas": [{"nombre": value, "nivel": None} for value in parsed.habilidades],
        "reforzar": parsed.areas_mejora, "intereses": parsed.intereses,
        "experiencia": parsed.experiencia, "resumen_publico": parsed.resumen_publico,
        "estado": "pendiente_revision", "origen": "ia_sin_confirmar",
    }


@router.post("/confirmar", response_model=PerfilOut)
async def confirmar_perfil(payload: ProfileReviewed,
                          db: Session = Depends(get_db),
                          actor: Usuario = Depends(get_current_user)):
    perfil = _own_profile(db, actor)
    actor.nombre = payload.nombre
    if payload.carrera is not None:
        actor.carrera = payload.carrera
    structured = payload.structured()
    confirmed = structured.model_dump(mode="json")
    perfil.perfil_estructurado_ia = confirmed
    perfil.resumen_publico_ia = structured.resumen_publico
    perfil.perfil_fuente_revision = content_revision(confirmed)
    perfil.perfil_confirmado_at = utc_now()
    perfil.perfil_estado_ia = "pendiente_embedding"
    perfil.embedding_perfil = None
    perfil.perfil_embedding_fuente_revision = None
    raw = safe_profile_data(perfil.datos_crudos)
    raw.update({"fortalezas": [item.model_dump() for item in payload.fortalezas],
                "reforzar": payload.reforzar, "intereses": payload.intereses,
                "experiencia": payload.experiencia,
                "disponibilidad": payload.disponibilidad,
                "visibilidad": payload.visibilidad, "pausado": payload.pausado,
                "consentimiento_recomendaciones": payload.consentimiento_recomendaciones,
                "bio": payload.resumen_publico})
    perfil.datos_crudos = raw
    revision = perfil.perfil_fuente_revision
    db.commit()
    await process_profile_embedding(db, perfil, structured, expected_revision=revision)
    db.commit()
    db.refresh(perfil)
    return _private_profile(actor, perfil)


@router.post("/embedding/reintentar", response_model=PerfilOut)
async def reintentar_embedding_perfil(db: Session = Depends(get_db),
                                     actor: Usuario = Depends(get_current_user)):
    perfil = _own_profile(db, actor)
    if perfil.perfil_estado_ia == "sin_contenido":
        raise HTTPException(409, "Agrega habilidades, intereses o experiencia y confirma el perfil antes de generar el análisis.")
    if (not perfil.perfil_estructurado_ia or not perfil.perfil_confirmado_at or not perfil.perfil_fuente_revision
            or perfil.perfil_estado_ia not in {"listo", "pendiente_embedding"}):
        raise HTTPException(status_code=409, detail="Primero confirma el perfil.")
    structured = StructuredProfile.model_validate(perfil.perfil_estructurado_ia)
    revision = perfil.perfil_fuente_revision
    db.commit()
    await process_profile_embedding(db, perfil, structured, expected_revision=revision)
    db.commit()
    return _private_profile(actor, perfil)


def crear_perfil_publico(usuario, perfil):
    datos_crudos = safe_profile_data(perfil.datos_crudos if perfil else {})
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
    actor: Usuario = Depends(get_current_user),
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
def obtener_perfil_publico(usuario_id: int, db: Session = Depends(get_db),
                          actor: Usuario = Depends(get_current_user)):
    usuario = db.query(Usuario).filter(Usuario.id_usuario == usuario_id).first()
    if not usuario or usuario.estado_cuenta != "Activa":
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
def obtener_perfil(usuario_id: int, db: Session = Depends(get_db),
                   actor: Usuario = Depends(get_current_user)):
    """
    Obtiene los datos personales y el perfil extendido (habilidades, bio, intereses) de un usuario.
    """
    require_self(usuario_id, actor)
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
    
    return _private_profile(usuario, perfil)


@router.put("/{usuario_id}", response_model=PerfilOut)
def actualizar_perfil(usuario_id: int, datos: PerfilUpdate, db: Session = Depends(get_db),
                      actor: Usuario = Depends(get_current_user)):
    """
    Actualiza la información dinámica del perfil del usuario dentro de la columna JSON 'datos_crudos'.
    """
    require_self(usuario_id, actor)
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
    previous_raw = perfil.datos_crudos if isinstance(perfil.datos_crudos, dict) else {}
    datos_actuales = dict(previous_raw)
    if datos_crudos is not None:
        datos_actuales.update(datos_crudos)
    datos_actuales.update(nuevos_datos)
    
    # Asignar de nuevo el diccionario para que SQLAlchemy detecte el cambio en el campo JSON
    semantic_keys = {"fortalezas", "habilidades", "intereses", "reforzar", "bio", "experiencia", "disponibilidad"}
    semantic_changed = any(datos_actuales.get(key) != previous_raw.get(key)
                           for key in semantic_keys)
    perfil.datos_crudos = datos_actuales
    if semantic_changed:
        perfil.perfil_estado_ia = "obsoleto"
        perfil.embedding_perfil = None
        perfil.perfil_embedding_fuente_revision = None
        perfil.perfil_fuente_revision = None
        perfil.perfil_confirmado_at = None
    
    db.commit()
    db.refresh(perfil)
    
    return _private_profile(usuario, perfil)
