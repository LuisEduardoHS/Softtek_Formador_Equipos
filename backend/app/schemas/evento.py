from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from typing import Optional, Dict, Any
from datetime import datetime
from app.services.ai.schemas import StructuredEventRequirements
from app.schemas.event_details import EventDetails


def valid_details(value):
    if any(k.startswith("_creation_") for k in value):
        raise ValueError("Metadatos de creación reservados.")
    return EventDetails.model_validate(value).model_dump(exclude_unset=True)

class EventoCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    creador_id: int | None = None  # legacy hint; must equal authenticated actor
    titulo: str = Field(min_length=1, max_length=150)
    categoria_principal: Optional[str] = Field(default="Academico", min_length=1, max_length=50)
    descripcion_libre: Optional[str] = Field(default=None, max_length=20000)
    detalles_especificos: Dict[str, Any] = Field(default_factory=dict)
    requisitos_confirmados: StructuredEventRequirements | None = None
    confirmado_por_creador: bool = False

    _details = field_validator("detalles_especificos")(valid_details)

    @model_validator(mode="after")
    def explicit_review(self):
        if self.requisitos_confirmados is not None and not self.confirmado_por_creador:
            raise ValueError("Se requiere confirmación explícita del creador.")
        return self

class EventoUpdate(BaseModel):
    categoria_principal: str
    descripcion_libre: Optional[str] = None
    detalles_especificos: Dict[str, Any]
    requisitos_ia: Dict[str, Any]
    integrantes: int = Field(ge=2, le=8)
    fuente_revision: str | None = Field(default=None, min_length=64, max_length=64)

    _details = field_validator("detalles_especificos")(valid_details)

class EventoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id_evento: int
    creador_id: int
    creador_nombre: Optional[str] = None
    categoria_principal: str
    titulo: str
    descripcion_libre: Optional[str] = None
    detalles_especificos: Dict[str, Any] = Field(default_factory=dict)
    requisitos_ia: Dict[str, Any] = Field(default_factory=dict)
    estado_ia: str | None = None
    requisitos_confirmados: bool = False
    fuente_revision: str | None = None
    soy_integrante: bool = False
    cupos_disponibles: int = 0
    acepta_participacion: bool = False
    roles_disponibles: list[dict] = Field(default_factory=list)
    motivo_no_disponible: str | None = None
    puede_solicitar: bool = False
    estado: str
    fecha_creacion: datetime
