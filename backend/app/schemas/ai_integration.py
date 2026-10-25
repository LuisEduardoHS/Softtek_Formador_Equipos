"""Reviewed 6A input; parser suggestions and confirmed facts are separate."""

from pydantic import BaseModel, ConfigDict, Field, model_validator, field_validator

from app.services.ai.schemas import StructuredEventRequirements, StructuredProfile
from app.services.ai.skill_terms import canonical_skill, folded
import re


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class ProfileInterpretRequest(_Strict):
    fortalezas: str = Field(min_length=1, max_length=20000)
    reforzar: str = Field(default="", max_length=5000)
    intereses: str = Field(default="", max_length=5000)


class ReviewedSkill(_Strict):
    nombre: str = Field(min_length=1, max_length=150)
    nivel: str | None = Field(default=None, max_length=50)

    @field_validator("nombre")
    @classmethod
    def affirmative_skill(cls, value):
        if re.search(r"\b(?:no|sin|quiero|aprender)\b", folded(value)):
            raise ValueError("Las fortalezas deben ser habilidades afirmadas; separa negaciones y objetivos de aprendizaje.")
        return canonical_skill(value)


class ProfileReviewed(_Strict):
    nombre: str = Field(min_length=1, max_length=150)
    carrera: str | None = Field(default=None, max_length=100)
    fortalezas: list[ReviewedSkill]
    reforzar: list[str] = Field(default_factory=list)
    intereses: list[str] = Field(default_factory=list)
    experiencia: list[str] = Field(default_factory=list)
    resumen_publico: str = Field(default="", max_length=1000)
    disponibilidad: list[str] = Field(default_factory=list)
    visibilidad: dict[str, bool]
    pausado: bool = False
    consentimiento_recomendaciones: bool = False

    @model_validator(mode="after")
    def bounded_lists(self):
        for values in (self.fortalezas, self.reforzar, self.intereses,
                       self.experiencia, self.disponibilidad):
            if len(values) > 100 or any(len(str(value)) > 200 for value in values):
                raise ValueError("Demasiados elementos o elemento demasiado largo.")
        allowed = {"fortalezas", "intereses", "disponibilidad", "reforzar", "correo"}
        if set(self.visibilidad) - allowed:
            raise ValueError("Campo de visibilidad desconocido.")
        if set(self.visibilidad) != allowed:
            raise ValueError("Confirma la visibilidad de todos los campos del perfil.")
        return self

    def structured(self) -> StructuredProfile:
        return StructuredProfile(
            habilidades=[item.nombre for item in self.fortalezas],
            areas_mejora=self.reforzar, intereses=self.intereses,
            experiencia=self.experiencia, resumen_publico=self.resumen_publico,
        )


class EventInterpretRequest(_Strict):
    descripcion_libre: str = Field(min_length=1, max_length=20000)
    categoria_principal: str = Field(min_length=1, max_length=50)
    detalles_especificos: dict = Field(default_factory=dict)


class EventReviewed(_Strict):
    requirements: StructuredEventRequirements
    confirmado_por_creador: bool
    fuente_revision: str | None = Field(default=None, min_length=64, max_length=64)

    @model_validator(mode="after")
    def explicit_review(self):
        if not self.confirmado_por_creador:
            raise ValueError("Se requiere confirmación explícita del creador.")
        return self
