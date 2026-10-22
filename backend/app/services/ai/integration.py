"""Deterministic content revision and recoverable embedding state for 6A."""

import hashlib
import json
from datetime import datetime, timezone
from fastapi.concurrency import run_in_threadpool

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
    except (OllamaServiceError, ValueError):
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
    except (OllamaServiceError, ValueError):
        return
    evento.embedding_requisitos = vector
    evento.embedding_model = EMBEDDING_MODEL
    evento.embedding_pipeline = PIPELINE_VERSION
    evento.embedding_fuente_revision = evento.requisitos_fuente_revision
    evento.estado_ia = "listo"
    evento.procesado_at = utc_now()


async def process_profile_embedding(db, perfil, structured: StructuredProfile) -> None:
    """Compute off the request loop; discard a result for an older confirmation."""
    revision = perfil.perfil_fuente_revision
    try:
        vector = await run_in_threadpool(generate_reviewed_profile_vector, structured)
    except (OllamaServiceError, ValueError):
        vector = None
    db.refresh(perfil)
    if revision != perfil.perfil_fuente_revision:
        return
    def result(_):
        if vector is None:
            raise OllamaServiceError("Embedding no disponible.")
        return vector
    store_profile_embedding(perfil, structured, generator=result)


async def process_event_embedding(db, evento, requirements: StructuredEventRequirements) -> None:
    revision = evento.requisitos_fuente_revision
    try:
        vector = await run_in_threadpool(generate_reviewed_event_vector, requirements)
    except (OllamaServiceError, ValueError):
        vector = None
    db.refresh(evento)
    if revision != evento.requisitos_fuente_revision:
        return
    def result(_):
        if vector is None:
            raise OllamaServiceError("Embedding no disponible.")
        return vector
    store_event_embedding(evento, requirements, generator=result)
