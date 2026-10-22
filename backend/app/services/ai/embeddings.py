
"""Stable semantic text and validated embeddings for AI analysis."""

import math

from app.services.ai.config import EMBEDDING_MODEL
from app.services.ai.ollama_client import OllamaClient, OllamaServiceError
from app.services.ai.schemas import StructuredEventRequirements, StructuredProfile


def _items(values: list[str]) -> str:
    seen = set()
    result = []
    for value in values:
        item = " ".join(value.split())[:200]
        if item and item.casefold() not in seen:
            result.append(item)
            seen.add(item.casefold())
    return ", ".join(result)


def _section(label: str, values: list[str]) -> str:
    joined = _items(values)
    return f"{label}: {joined}" if joined else ""


def build_profile_embedding_text(profile: StructuredProfile) -> str:
    """Represent declared abilities, interests and experience, never learning gaps."""
    if not isinstance(profile, StructuredProfile):
        raise TypeError("Se requiere StructuredProfile.")
    return "\n".join(filter(None, (
        _section("Habilidades", profile.habilidades),
        _section("Intereses", profile.intereses),
        _section("Experiencia", profile.experiencia),
    )))[:4000]


def build_event_embedding_text(requirements: StructuredEventRequirements) -> str:
    """Represent what the team seeks, with required and optional items labeled."""
    if not isinstance(requirements, StructuredEventRequirements):
        raise TypeError("Se requiere StructuredEventRequirements.")
    parts = [
        _section("Habilidades obligatorias buscadas", requirements.habilidades_obligatorias),
        _section("Habilidades deseables", requirements.habilidades_deseables),
        _section("Roles buscados", requirements.roles_buscados),
        _section("Intereses relacionados", requirements.intereses_relacionados),
        _section("Restricciones explícitas", requirements.restricciones_explicitas),
    ]
    if requirements.categoria:
        parts.insert(0, f"Categoría: {' '.join(requirements.categoria.split())[:200]}")
    if requirements.resumen:
        parts.append(f"Resumen: {' '.join(requirements.resumen.split())[:500]}")
    return "\n".join(filter(None, parts))[:4000]


def _generate(text: str, ai: OllamaClient | None) -> list[float]:
    if not text:
        raise ValueError("No hay información semántica suficiente.")
    client = ai if ai is not None else OllamaClient()
    vector = client.generate_embedding(text)
    if not isinstance(vector, (list, tuple)) or not vector or any(
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(value)
        for value in vector
    ):
        raise OllamaServiceError("Embedding inválido.")
    if EMBEDDING_MODEL == "nomic-embed-text" and len(vector) != 768:
        raise OllamaServiceError("Dimensión de embedding incompatible con Nomic.")
    return [float(value) for value in vector]


def generate_profile_embedding(
    profile: StructuredProfile,
    ai: OllamaClient | None = None,
) -> list[float]:
    return _generate(build_profile_embedding_text(profile), ai)


def generate_event_embedding(
    requirements: StructuredEventRequirements,
    ai: OllamaClient | None = None,
) -> list[float]:
    return _generate(build_event_embedding_text(requirements), ai)
