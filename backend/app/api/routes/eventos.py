"""Authenticated event drafts and confirmed AI requirements."""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.orm import Session
from app.core.security import get_current_user
from app.db.database import get_db
from app.models.participante import ParticipanteEvento
from app.models.evento import Evento
from app.models.usuario import Usuario
from app.schemas.ai_integration import EventInterpretRequest, EventReviewed
from app.schemas.evento import EventoCreate, EventoOut, EventoUpdate
from app.services.ai.event_parser import EventParser
from app.services.ai.integration import content_revision, process_event_embedding, utc_now
from app.services.ai.ollama_client import OllamaClient, OllamaServiceError
from app.services.ai.schemas import StructuredEventRequirements

router = APIRouter(prefix="/eventos", tags=["Eventos y Convocatorias"])


def _visible(evento: Evento, actor: Usuario, db: Session) -> EventoOut:
    creator = db.get(Usuario, evento.creador_id)
    details = dict(evento.detalles_especificos or {})
    roles = details.get("roles")
    if isinstance(roles, list):
        participants = db.query(ParticipanteEvento).filter(
            ParticipanteEvento.id_evento == evento.id_evento).all()
        assignments = {p.rol.strip().casefold(): str(p.id_usuario) for p in participants if p.rol}
        details["roles"] = [
            {**role, "cubiertoPor": assignments.get(str(role.get("nombre", "")).strip().casefold())}
            if isinstance(role, dict) else role for role in roles
        ]
    return EventoOut(
        id_evento=evento.id_evento, creador_id=evento.creador_id,
        creador_nombre=creator.nombre if creator else None,
        categoria_principal=evento.categoria_principal, titulo=evento.titulo,
        descripcion_libre=evento.descripcion_libre,
        detalles_especificos=details,
        requisitos_ia=(evento.requisitos_ia or {}) if evento.requisitos_confirmados_at else {},
        requisitos_confirmados=bool(evento.requisitos_confirmados_at),
        estado_ia=evento.estado_ia if evento.creador_id == actor.id_usuario else None,
        estado=evento.estado, fecha_creacion=evento.fecha_creacion,
    )


def _owned(db: Session, id_evento: int, actor: Usuario) -> Evento:
    evento = db.get(Evento, id_evento)
    if evento is None:
        raise HTTPException(404, "Evento no encontrado.")
    if evento.creador_id != actor.id_usuario:
        raise HTTPException(403, "No tienes permiso para modificar este evento.")
    return evento


def _confirm(evento: Evento, req: StructuredEventRequirements) -> StructuredEventRequirements:
    if req.categoria and req.categoria.casefold() != evento.categoria_principal.casefold():
        raise HTTPException(422, "La categoría revisada no coincide con el evento.")
    confirmed = req.model_copy(update={"categoria": evento.categoria_principal})
    data = confirmed.model_dump(mode="json")
    evento.requisitos_ia = data
    evento.requisitos_fuente_revision = content_revision(data)
    evento.requisitos_confirmados_at = utc_now()
    evento.estado_ia = "pendiente_embedding"
    evento.estado = "Abierto"
    evento.embedding_requisitos = None
    evento.embedding_fuente_revision = None
    return confirmed


@router.post("/interpretar")
async def interpretar_evento(payload: EventInterpretRequest,
                            actor: Usuario = Depends(get_current_user)):
    try:
        parsed = await run_in_threadpool(
            EventParser(ai=OllamaClient(timeout=60)).parse_event,
            payload.descripcion_libre, payload.categoria_principal,
            payload.detalles_especificos,
        )
    except OllamaServiceError as error:
        raise HTTPException(503, "La interpretación no está disponible. Puedes revisar manualmente o reintentar.") from error
    return {"requisitos": parsed.model_dump(mode="json"), "origen": "ia_sin_confirmar"}


@router.post("/", response_model=EventoOut, status_code=status.HTTP_201_CREATED)
async def crear_evento(payload: EventoCreate, db: Session = Depends(get_db),
                      actor: Usuario = Depends(get_current_user)):
    if payload.creador_id is not None and payload.creador_id != actor.id_usuario:
        raise HTTPException(403, "El creador debe ser el usuario autenticado.")
    evento = Evento(
        creador_id=actor.id_usuario, titulo=payload.titulo,
        categoria_principal=payload.categoria_principal or "Academico",
        descripcion_libre=payload.descripcion_libre,
        detalles_especificos=payload.detalles_especificos or {},
        requisitos_ia={}, embedding_requisitos=None,
        estado="Borrador", estado_ia="pendiente_revision",
    )
    confirmed = None
    if payload.requisitos_confirmados is not None:
        confirmed = _confirm(evento, payload.requisitos_confirmados)
    db.add(evento)
    db.commit()
    db.refresh(evento)
    if confirmed is not None:
        await process_event_embedding(db, evento, confirmed)
        db.commit()
        db.refresh(evento)
    return _visible(evento, actor, db)


@router.post("/{id_evento}/confirmar", response_model=EventoOut)
async def confirmar_evento(id_evento: int, payload: EventReviewed,
                          db: Session = Depends(get_db),
                          actor: Usuario = Depends(get_current_user)):
    evento = _owned(db, id_evento, actor)
    confirmed = _confirm(evento, payload.requirements)
    db.commit()
    await process_event_embedding(db, evento, confirmed)
    db.commit()
    db.refresh(evento)
    return _visible(evento, actor, db)


@router.post("/{id_evento}/embedding/reintentar", response_model=EventoOut)
async def reintentar_embedding_evento(id_evento: int, db: Session = Depends(get_db),
                                     actor: Usuario = Depends(get_current_user)):
    evento = _owned(db, id_evento, actor)
    if not evento.requisitos_confirmados_at or not evento.requisitos_ia:
        raise HTTPException(409, "Primero confirma los requisitos.")
    confirmed = StructuredEventRequirements.model_validate(evento.requisitos_ia)
    await process_event_embedding(db, evento, confirmed)
    db.commit()
    return _visible(evento, actor, db)


@router.get("/", response_model=list[EventoOut])
def listar_eventos(categoria_principal: str | None = Query(None),
                  estado: str | None = Query(None), db: Session = Depends(get_db),
                  actor: Usuario = Depends(get_current_user)):
    query = db.query(Evento)
    if categoria_principal:
        query = query.filter(Evento.categoria_principal == categoria_principal)
    if estado:
        query = query.filter(Evento.estado == estado)
    return [_visible(e, actor, db) for e in query.order_by(Evento.id_evento.desc()).all()
            if e.estado != "Borrador" or e.creador_id == actor.id_usuario]


@router.get("/{id_evento}", response_model=EventoOut)
def obtener_evento(id_evento: int, db: Session = Depends(get_db),
                   actor: Usuario = Depends(get_current_user)):
    evento = db.get(Evento, id_evento)
    if not evento or (evento.estado == "Borrador" and evento.creador_id != actor.id_usuario):
        raise HTTPException(404, "Evento no encontrado.")
    return _visible(evento, actor, db)


@router.put("/{id_evento}", response_model=EventoOut)
def actualizar_evento(
    id_evento: int,
    cambios: EventoUpdate,
    usuario_id: int,
    db: Session = Depends(get_db),
    actor: Usuario = Depends(get_current_user),
):
    if usuario_id != actor.id_usuario:
        raise HTTPException(403, "El usuario debe coincidir con la sesión.")
    evento = db.query(Evento).filter(Evento.id_evento == id_evento).first()
    if not evento:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evento no encontrado.",
        )
    if evento.creador_id != usuario_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo quien creó el evento puede editarlo.",
        )
    if cambios.categoria_principal not in {"Academico", "Personal", "Deportivo", "Videojuegos", "General"}:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="El tipo de proyecto no es válido.",
        )

    participantes = db.query(ParticipanteEvento).filter(
        ParticipanteEvento.id_evento == id_evento
    ).all()
    if len(participantes) + 1 > cambios.integrantes:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El número de integrantes no puede ser menor que las personas que ya forman parte del equipo.",
        )

    detalles = dict(cambios.detalles_especificos)
    roles = detalles.get("roles")
    if not isinstance(roles, list):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="La lista de roles no es válida.",
        )
    if any(
        not isinstance(rol, dict)
        or not isinstance(rol.get("nombre"), str)
        or not rol["nombre"].strip()
        for rol in roles
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Cada rol debe tener un nombre válido.",
        )
    roles_por_nombre = {
        rol["nombre"].strip().casefold()
        for rol in roles
    }
    roles_asignados = {participante.rol.strip().casefold() for participante in participantes if participante.rol}
    roles_eliminados = roles_asignados - roles_por_nombre
    if roles_eliminados:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No puedes quitar un rol que ya tiene un integrante asignado.",
        )

    detalles["tipo"] = cambios.categoria_principal.casefold()
    detalles["integrantes"] = cambios.integrantes
    detalles["fechaLimite"] = detalles.get("fechaLimite") or None

    evento.categoria_principal = cambios.categoria_principal
    evento.descripcion_libre = cambios.descripcion_libre
    evento.detalles_especificos = detalles
    # Edits must not retain confirmed evidence or vectors from an older revision.
    evento.requisitos_borrador_ia = evento.requisitos_ia
    evento.requisitos_ia = {}
    evento.requisitos_confirmados_at = None
    evento.requisitos_fuente_revision = None
    evento.embedding_requisitos = None
    evento.embedding_fuente_revision = None
    evento.embedding_model = None
    evento.embedding_pipeline = None
    evento.procesado_at = None
    evento.estado_ia = "pendiente_revision"
    db.commit()
    db.refresh(evento)

    creador = db.query(Usuario).filter(Usuario.id_usuario == evento.creador_id).first()
    if not creador:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No encontramos a la persona creadora del evento.",
        )
    return _visible(evento, actor, db)
