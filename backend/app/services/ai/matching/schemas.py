"""Internal, validated data contracts for matching subphase 4.1.

These models do not decide eligibility, calculate scores, or access persistence.
"""

import math
import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.services.ai.schemas import StructuredEventRequirements, StructuredProfile

from .normalization import deduplicate_evidence, normalize_term


class _Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, str_strip_whitespace=True)


def _nonblank(value: str) -> str:
    if not value or not value.strip():
        raise ValueError("El texto no puede estar vacío.")
    return value.strip()


def _public_text(value: str) -> str:
    value = _nonblank(value)
    if re.search(r"\b[\w.+-]+@[\w.-]+\.[a-z]{2,}\b", value, re.IGNORECASE):
        raise ValueError("La respuesta no puede contener correo personal.")
    if re.search(r"\b(?:\+?\d[\d\s().-]{7,}\d)\b", value):
        raise ValueError("La respuesta no puede contener teléfono personal.")
    return value


class Evidence(_Contract):
    source: Literal["user_declared", "organizer_confirmed", "ai_unreviewed", "team_record"]
    kind: Literal["skill", "interest", "learning_goal", "role", "role_preference", "availability", "constraint", "other"]
    value: str = Field(min_length=1, repr=False)
    polarity: Literal["affirms", "denies", "unknown"]
    confirmed: bool
    source_ref: str | None = Field(default=None, exclude=True, repr=False)

    @field_validator("value")
    @classmethod
    def nonblank_value(cls, value: str) -> str:
        return _nonblank(value)

    @field_validator("source_ref")
    @classmethod
    def opaque_reference(cls, value: str | None) -> str | None:
        if value is not None and not re.fullmatch(r"[A-Za-z0-9_.:-]{1,128}", value):
            raise ValueError("source_ref debe ser un identificador opaco.")
        return value

    @model_validator(mode="after")
    def unreviewed_cannot_be_confirmed(self):
        if self.source == "ai_unreviewed" and self.confirmed:
            raise ValueError("Una extracción IA sin revisar no puede estar confirmada.")
        if self.kind == "skill":
            statement = normalize_term(self.value)
            if re.match(r"^(?:quiero|deseo|busco)\s+(?:aprender|mejorar|desarrollar)\b", statement):
                raise ValueError("Un objetivo de aprendizaje no es una habilidad adquirida.")
            if self.polarity == "affirms" and re.match(
                r"^(?:no\s+(?:se|tengo|domino|puedo|cuento\s+con)|sin)\b", statement
            ):
                raise ValueError("Una negación no puede afirmar una habilidad.")
        return self


class Location(_Contract):
    estado_geografico: str | None = Field(default=None, repr=False)
    municipio: str | None = Field(default=None, repr=False)

    @field_validator("estado_geografico", "municipio")
    @classmethod
    def nonblank_if_present(cls, value: str | None) -> str | None:
        return _nonblank(value) if value is not None else None


class Participant(_Contract):
    user_id: int = Field(gt=0)
    role: str | None = None
    confirmed: bool

    @field_validator("role")
    @classmethod
    def role_if_present(cls, value: str | None) -> str | None:
        return _nonblank(value) if value is not None else None


class _EmbeddingContract(_Contract):
    embedding_model: str | None = None
    embedding_source_version: str | None = None

    @field_validator("embedding_model", "embedding_source_version")
    @classmethod
    def nonblank_metadata(cls, value: str | None) -> str | None:
        return _nonblank(value) if value is not None else None

    @staticmethod
    def validate_embedding(vector: list[float] | None, model: str | None, version: str | None):
        if vector is None:
            if model is not None or version is not None:
                raise ValueError("No se aceptan metadatos sin embedding.")
            return
        if not vector or model is None or version is None:
            raise ValueError("El embedding requiere vector, modelo y versión de origen.")
        if any(not math.isfinite(value) for value in vector):
            raise ValueError("El embedding debe contener números finitos.")
        if model in {"nomic-embed-text", "nomic-embed-text:latest"} and len(vector) != 768:
            raise ValueError("Nomic requiere 768 dimensiones.")


class CandidateInput(_EmbeddingContract):
    user_id: int = Field(gt=0)
    profile: StructuredProfile | None = Field(default=None, repr=False)
    declared_skills: list[Evidence] | None = Field(default=None, repr=False)
    role_preferences: list[Evidence] | None = Field(default=None, repr=False)
    availability: list[Evidence] | None = Field(default=None, repr=False)
    location: Location | None = Field(default=None, repr=False)
    visibility: Literal["visible", "hidden", "unknown"] = "unknown"
    account_state: Literal["active", "inactive", "unknown"] = "unknown"
    profile_embedding: list[float] | None = Field(default=None, repr=False)

    @field_validator("declared_skills", "role_preferences", "availability")
    @classmethod
    def remove_repeated_evidence(cls, value: list[Evidence] | None) -> list[Evidence] | None:
        return deduplicate_evidence(value) if value is not None else None

    @model_validator(mode="after")
    def evidence_categories(self):
        for values, expected in (
            (self.declared_skills, "skill"),
            (self.role_preferences, "role_preference"),
            (self.availability, "availability"),
        ):
            if values is not None and any(item.kind != expected for item in values):
                raise ValueError(f"El tipo de evidencia debe ser {expected}.")
        self.validate_embedding(self.profile_embedding, self.embedding_model, self.embedding_source_version)
        return self


class EventInput(_EmbeddingContract):
    event_id: int = Field(gt=0)
    creator_id: int = Field(gt=0)
    state: Literal["open", "closed", "unknown"] = "unknown"
    requirements: StructuredEventRequirements | None = Field(default=None, repr=False)
    confirmed_requirements: list[Evidence] | None = Field(default=None, repr=False)
    participants: list[Participant] | None = Field(default=None, repr=False)
    outstanding_roles: list[Evidence] | None = Field(default=None, repr=False)
    explicit_constraints: list[Evidence] | None = Field(default=None, repr=False)
    event_embedding: list[float] | None = Field(default=None, repr=False)

    @field_validator("confirmed_requirements", "outstanding_roles", "explicit_constraints")
    @classmethod
    def remove_repeated_evidence(cls, value: list[Evidence] | None) -> list[Evidence] | None:
        return deduplicate_evidence(value) if value is not None else None

    @model_validator(mode="after")
    def validate_internal_state(self):
        self.validate_embedding(self.event_embedding, self.embedding_model, self.embedding_source_version)
        for values, kinds in (
            (self.confirmed_requirements, {"skill", "constraint", "role"}),
            (self.outstanding_roles, {"role"}),
            (self.explicit_constraints, {"constraint"}),
        ):
            if values is not None and any(item.kind not in kinds for item in values):
                raise ValueError("El tipo de evidencia no corresponde al campo.")
        if self.participants is not None:
            ids = [person.user_id for person in self.participants]
            if len(ids) != len(set(ids)):
                raise ValueError("Un participante no puede repetirse.")
        if self.confirmed_requirements is not None and any(
            not item.confirmed for item in self.confirmed_requirements
        ):
            raise ValueError("confirmed_requirements exige evidencias confirmadas.")
        return self


class MatchRequest(_Contract):
    event: EventInput
    candidates: list[CandidateInput]
    policy_version: str = Field(min_length=1)
    top_n: int | None = Field(default=None, gt=0)

    @field_validator("policy_version")
    @classmethod
    def nonblank_policy(cls, value: str) -> str:
        return _nonblank(value)

    @model_validator(mode="after")
    def unique_candidates(self):
        ids = [candidate.user_id for candidate in self.candidates]
        if len(ids) != len(set(ids)):
            raise ValueError("Los candidatos deben tener identificadores únicos.")
        return self


class RequirementAssessment(_Contract):
    requirement: str
    kind: Literal["required_skill", "preferred_skill", "open_role", "explicit_constraint"]
    status: Literal["met", "unmet_confirmed", "unknown", "not_applicable"]
    evidence: list[Evidence] = Field(default_factory=list, exclude=True, repr=False)
    reason: str = Field(repr=False)

    @field_validator("requirement", "reason")
    @classmethod
    def safe_public_text(cls, value: str) -> str:
        return _public_text(value)

    @model_validator(mode="after")
    def confirmed_negative_requires_evidence(self):
        if self.status == "unmet_confirmed" and not any(
            item.confirmed and item.polarity == "denies" for item in self.evidence
        ):
            raise ValueError("unmet_confirmed requiere evidencia negativa confirmada.")
        return self


class EvidenceCoverage(_Contract):
    known: int = Field(default=0, ge=0)
    unknown: int = Field(default=0, ge=0)
    not_applicable: int = Field(default=0, ge=0)


class PublicExplanation(_Contract):
    strengths: list[str] = Field(default_factory=list, repr=False)
    gaps: list[str] = Field(default_factory=list, repr=False)
    unknowns: list[str] = Field(default_factory=list, repr=False)

    @field_validator("strengths", "gaps", "unknowns")
    @classmethod
    def reject_obvious_personal_data(cls, values: list[str]) -> list[str]:
        return [_public_text(value) for value in values]


class MatchResult(_Contract):
    event_id: int = Field(gt=0)
    candidate_id: int = Field(gt=0)
    eligibility: Literal["eligible", "needs_review", "ineligible"]
    eligibility_reasons: list[str] = Field(default_factory=list, repr=False)
    requirements: list[RequirementAssessment] = Field(default_factory=list, repr=False)
    ranking_score: float | None = Field(default=None, ge=0, le=1)
    score_components: dict[str, float | None] = Field(default_factory=dict, repr=False)
    evidence_coverage: EvidenceCoverage = Field(default_factory=EvidenceCoverage)
    explanation: PublicExplanation = Field(default_factory=PublicExplanation, repr=False)
    policy_version: str

    @field_validator("eligibility_reasons")
    @classmethod
    def safe_reasons(cls, values: list[str]) -> list[str]:
        return [_public_text(value) for value in values]

    @field_validator("policy_version")
    @classmethod
    def nonblank_policy(cls, value: str) -> str:
        return _nonblank(value)

    @field_validator("score_components")
    @classmethod
    def bounded_components(cls, values: dict[str, float | None]) -> dict[str, float | None]:
        if any(not key.strip() or (value is not None and (not math.isfinite(value) or not 0 <= value <= 1))
               for key, value in values.items()):
            raise ValueError("Los componentes deben tener nombre y valor entre 0 y 1.")
        return values
