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
from app.services.ai.integration import content_revision, process_event_embedding, utc_now, event_source_revision
from app.services.ai.ollama_client import OllamaClient, OllamaServiceError
from app.services.ai.schemas import StructuredEventRequirements
from app.services.team_rules import lock_event, roster, validated_roles, capacity, role_key

router = APIRouter(prefix="/eventos", tags=["Eventos y Convocatorias"])


def _visible(evento: Evento, actor: Usuario, db: Session) -> EventoOut:
    creator = db.get(Usuario, evento.creador_id)
    details = dict(evento.detalles_especificos or {})
    participants = db.query(ParticipanteEvento).filter(
        ParticipanteEvento.id_evento == evento.id_evento).all()
    member_ids = {p.id_usuario for p in participants} | {evento.creador_id}
    roles = details.get("roles")
    if isinstance(roles, list):
        details["roles"] = []
        for role in roles:
            if not isinstance(role, dict):
                continue
            ids = [str(p.id_usuario) for p in participants
                   if role_key(p.rol) == role_key(role.get("nombre"))]
            slots = role.get("vacantes", 1)
            details["roles"].append({**role, "ocupados": len(ids), "integrantesIds": ids,
                                     "cubiertoPor": ids[0] if ids and len(ids) >= slots else None})
    return EventoOut(
        id_evento=evento.id_evento, creador_id=evento.creador_id,
        creador_nombre=creator.nombre if creator else None,
        categoria_principal=evento.categoria_principal, titulo=evento.titulo,
        descripcion_libre=evento.descripcion_libre,
        detalles_especificos=details,
        requisitos_ia=(evento.requisitos_ia or {}) if evento.requisitos_confirmados_at else {},
        requisitos_confirmados=bool(evento.requisitos_confirmados_at),
        estado_ia=evento.estado_ia if evento.creador_id == actor.id_usuario else None,
        fuente_revision=event_source_revision(evento) if evento.creador_id == actor.id_usuario else None,
        soy_integrante=actor.id_usuario in member_ids,
        cupos_disponibles=max(0, capacity(details) - len(member_ids)),
        estado=evento.estado, fecha_creacion=evento.fecha_creacion,
    )


def _owned(db: Session, id_evento: int, actor: Usuario) -> Evento:
    evento = lock_event(db, id_evento)
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
    evento.requisitos_fuente_revision = content_revision({"source": event_source_revision(evento), "requirements": data})
    evento.requisitos_confirmados_at = utc_now()
    evento.estado_ia = "pendiente_embedding"
    evento.estado = "Abierto"
    evento.requisitos_borrador_ia = None
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
    details = dict(evento.detalles_especificos)
    if "integrantes" in details:
        capacity(details)
    if "roles" in details:
        details["roles"] = validated_roles(details)
    evento.detalles_especificos = details
    confirmed = None
    if payload.requisitos_confirmados is not None:
        confirmed = _confirm(evento, payload.requisitos_confirmados)
    revision = evento.requisitos_fuente_revision
    db.add(evento)
    db.commit()
    db.refresh(evento)
    if confirmed is not None:
        await process_event_embedding(db, evento, confirmed, expected_revision=revision)
        db.commit()
        db.refresh(evento)
    return _visible(evento, actor, db)


@router.post("/{id_evento}/confirmar", response_model=EventoOut)
async def confirmar_evento(id_evento: int, payload: EventReviewed,
                          db: Session = Depends(get_db),
                          actor: Usuario = Depends(get_current_user)):
    evento = _owned(db, id_evento, actor)
    if payload.fuente_revision and payload.fuente_revision != event_source_revision(evento):
        raise HTTPException(409, "El proyecto cambió mientras lo revisabas. Recarga los requisitos.")
    confirmed = _confirm(evento, payload.requirements)
    revision = evento.requisitos_fuente_revision
    db.commit()
    await process_event_embedding(db, evento, confirmed, expected_revision=revision)
    db.commit()
    db.refresh(evento)
    return _visible(evento, actor, db)


@router.post("/{id_evento}/embedding/reintentar", response_model=EventoOut)
async def reintentar_embedding_evento(id_evento: int, db: Session = Depends(get_db),
                                     actor: Usuario = Depends(get_current_user)):
    evento = _owned(db, id_evento, actor)
    if not evento.requisitos_confirmados_at or not evento.requisitos_ia or not evento.requisitos_fuente_revision:
        raise HTTPException(409, "Primero confirma los requisitos.")
    confirmed = StructuredEventRequirements.model_validate(evento.requisitos_ia)
    revision = evento.requisitos_fuente_revision
    db.commit()
    await process_event_embedding(db, evento, confirmed, expected_revision=revision)
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
    evento = lock_event(db, id_evento)
    if cambios.fuente_revision and cambios.fuente_revision != event_source_revision(evento):
        raise HTTPException(409, "El proyecto cambió. Recarga antes de guardar.")
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

    participantes = roster(db, evento)
    if len({p.id_usuario for p in participantes} | {evento.creador_id}) > cambios.integrantes:
        raise HTTPException(409, "La capacidad no puede ser menor que los integrantes actuales.")
    detalles = dict(cambios.detalles_especificos)
    detalles["roles"] = validated_roles(detalles, participantes)
    detalles["tipo"] = cambios.categoria_principal.casefold()
    detalles["integrantes"] = cambios.integrantes
    detalles["fechaLimite"] = detalles.get("fechaLimite") or None

    evento.categoria_principal = cambios.categoria_principal
    evento.descripcion_libre = cambios.descripcion_libre
    evento.detalles_especificos = detalles
    # Edits must not retain confirmed evidence or vectors from an older revision.
    if evento.requisitos_confirmados_at:
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
