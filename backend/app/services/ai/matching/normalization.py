"""Conservative, versioned equivalences; no semantic skill inference."""

import unicodedata
from typing import Mapping

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from app.services.ai.skill_catalog import CATALOG_VERSION, SKILL_ALIASES


def normalize_term(term: str) -> str:
    """Normalize spelling for comparison while preserving meaningful symbols."""
    if not isinstance(term, str):
        raise TypeError("El término debe ser texto.")
    value = " ".join(unicodedata.normalize("NFKC", term).split()).casefold()
    value = "".join(
        char for char in unicodedata.normalize("NFKD", value)
        if not unicodedata.combining(char)
    )
    if not value:
        raise ValueError("El término no puede estar vacío.")
    return value


class EquivalenceCatalog(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    version: str = Field(min_length=1)
    aliases: dict[str, str]

    @field_validator("version")
    @classmethod
    def nonblank_version(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Se requiere una versión no vacía.")
        return value.strip()

    @model_validator(mode="after")
    def validate_aliases(self):
        normalized = {}
        for alias, canonical in self.aliases.items():
            key = normalize_term(alias)
            target = normalize_term(canonical)
            if key in normalized and normalized[key] != target:
                raise ValueError("Hay equivalencias contradictorias.")
            if key == target:
                raise ValueError("Una equivalencia no puede apuntar a sí misma.")
            normalized[key] = target
        if set(normalized) & set(normalized.values()):
            raise ValueError("No se permiten cadenas de equivalencias.")
        return self


DEFAULT_EQUIVALENCES = EquivalenceCatalog(
    version=CATALOG_VERSION,
    aliases=SKILL_ALIASES,
)


def apply_equivalence(term: str, catalog: EquivalenceCatalog = DEFAULT_EQUIVALENCES) -> str:
    """Return a comparable term using only catalogued, explicit aliases."""
    if not isinstance(catalog, EquivalenceCatalog):
        raise TypeError("Se requiere un catálogo de equivalencias.")
    normalized = normalize_term(term)
    aliases = {normalize_term(key): normalize_term(value) for key, value in catalog.aliases.items()}
    return aliases.get(normalized, normalized)


def validate_evidence(value: object):
    """Validate one evidence item without promoting interests or learning goals."""
    from .schemas import Evidence

    if isinstance(value, Evidence):
        return value
    if not isinstance(value, Mapping):
        raise TypeError("La evidencia debe ser un objeto JSON.")
    return Evidence.model_validate(value)


def deduplicate_evidence(items: list, catalog: EquivalenceCatalog = DEFAULT_EQUIVALENCES) -> list:
    """Remove exact semantic duplicates from the same provenance, preserving order."""
    seen = set()
    result = []
    for item in items:
        key = (
            apply_equivalence(item.value, catalog), item.source, item.polarity,
            item.kind, item.confirmed, item.source_ref,
        )
        if key not in seen:
            result.append(item)
            seen.add(key)
    return result
