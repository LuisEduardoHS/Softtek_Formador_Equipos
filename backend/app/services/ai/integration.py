"""Deterministic content revision and recoverable embedding state for 6A."""

import hashlib
import json
from datetime import datetime, timezone
from fastapi.concurrency import run_in_threadpool
from sqlalchemy import update

from app.services.ai.config import EMBEDDING_MODEL
from app.services.ai.embeddings import generate_event_embedding, generate_profile_embedding
from app.services.ai.ollama_client import OllamaClient, OllamaServiceError
from app.services.ai.schemas import StructuredEventRequirements, StructuredProfile

PIPELINE_VERSION = "2026-10-22.v1"


def content_revision(data: dict) -> str:
    raw = json.dumps(data, sort_keys=True, ensure_ascii=False,
                     separators=(",", ":"), allow_nan=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def event_source_revision(evento) -> str:
    details = evento.detalles_especificos or {}
    if isinstance(details, dict):
        details = {k: v for k, v in details.items() if not k.startswith("_creation_")}
    return content_revision({"titulo": evento.titulo, "categoria": evento.categoria_principal,
                             "descripcion": evento.descripcion_libre,
                             "detalles": details})


def generate_reviewed_profile_vector(profile: StructuredProfile) -> list[float]:
    return generate_profile_embedding(profile, ai=OllamaClient(timeout=25))


def generate_reviewed_event_vector(requirements: StructuredEventRequirements) -> list[float]:
    return generate_event_embedding(requirements, ai=OllamaClient(timeout=25))


def store_profile_embedding(perfil, structured: StructuredProfile,
                            generator=None) -> None:
    """Never return an old vector as current after confirmed content changes."""
    perfil.perfil_estado_ia = "pendiente_embedding"
    perfil.embedding_perfil = None
    perfil.perfil_embedding_fuente_revision = None
    try:
        vector = (generator or generate_reviewed_profile_vector)(structured)
    except (OllamaServiceError, ConnectionError, TimeoutError, ValueError):
        return
    perfil.embedding_perfil = vector
    perfil.perfil_embedding_model = EMBEDDING_MODEL
    perfil.perfil_embedding_pipeline = PIPELINE_VERSION
    perfil.perfil_embedding_fuente_revision = perfil.perfil_fuente_revision
    perfil.perfil_estado_ia = "listo"
    perfil.perfil_procesado_at = utc_now()


def store_event_embedding(evento, requirements: StructuredEventRequirements,
                          generator=None) -> None:
    evento.estado_ia = "pendiente_embedding"
    evento.embedding_requisitos = None
    evento.embedding_fuente_revision = None
    try:
        vector = (generator or generate_reviewed_event_vector)(requirements)
    except (OllamaServiceError, ConnectionError, TimeoutError, ValueError):
        return
    evento.embedding_requisitos = vector
    evento.embedding_model = EMBEDDING_MODEL
    evento.embedding_pipeline = PIPELINE_VERSION
    evento.embedding_fuente_revision = evento.requisitos_fuente_revision
    evento.estado_ia = "listo"
    evento.procesado_at = utc_now()


async def process_profile_embedding(db, perfil, structured: StructuredProfile, *, expected_revision=None) -> None:
    """Compute off the request loop; discard a result for an older confirmation."""
    revision = expected_revision if expected_revision is not None else perfil.perfil_fuente_revision
    try:
        vector = await run_in_threadpool(generate_reviewed_profile_vector, structured)
    except (OllamaServiceError, ConnectionError, TimeoutError, ValueError):
        vector = None
    from app.models.usuario import PerfilUsuario
    values = dict(embedding_perfil=vector, perfil_embedding_fuente_revision=revision if vector else None,
                  perfil_estado_ia="listo" if vector else "pendiente_embedding",
                  perfil_embedding_model=EMBEDDING_MODEL if vector else None,
                  perfil_embedding_pipeline=PIPELINE_VERSION if vector else None,
                  perfil_procesado_at=utc_now() if vector else None)
    db.execute(update(PerfilUsuario).where(
        PerfilUsuario.usuario_id == perfil.usuario_id,
        PerfilUsuario.perfil_fuente_revision == revision,
        PerfilUsuario.perfil_confirmado_at.is_not(None),
        PerfilUsuario.perfil_estado_ia.in_(["listo", "pendiente_embedding"] if vector else ["pendiente_embedding"]),
    ).values(**values).execution_options(synchronize_session=False))
    db.refresh(perfil, with_for_update=True)
    return

async def process_event_embedding(db, evento, requirements: StructuredEventRequirements, *, expected_revision=None) -> None:
    revision = expected_revision if expected_revision is not None else evento.requisitos_fuente_revision
    try:
        vector = await run_in_threadpool(generate_reviewed_event_vector, requirements)
    except (OllamaServiceError, ConnectionError, TimeoutError, ValueError):
        vector = None
    from app.models.evento import Evento
    db.execute(update(Evento).where(
        Evento.id_evento == evento.id_evento,
        Evento.requisitos_fuente_revision == revision,
        Evento.requisitos_confirmados_at.is_not(None),
        Evento.estado_ia.in_(["listo", "pendiente_embedding"] if vector else ["pendiente_embedding"]),
    ).values(embedding_requisitos=vector, embedding_fuente_revision=revision if vector else None,
             estado_ia="listo" if vector else "pendiente_embedding",
             embedding_model=EMBEDDING_MODEL if vector else None,
             embedding_pipeline=PIPELINE_VERSION if vector else None,
             procesado_at=utc_now() if vector else None).execution_options(synchronize_session=False))
    db.refresh(evento, with_for_update=True)
    return
