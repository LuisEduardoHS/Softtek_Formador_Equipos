from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from typing import Optional, List, Dict, Any
from app.schemas.profile_data import ProfileData, Text150, TextList

class PerfilUpdate(BaseModel):
    nombre: Text150 | None = None
    carrera: Optional[str] = Field(default=None, min_length=1, max_length=100)
    bio: Optional[str] = Field(default=None, max_length=1000)
    habilidades: Optional[List[Text150]] = Field(default=None, max_length=100)
    intereses: Optional[TextList] = None
    rol_preferido: Optional[str] = None  # ej. "Backend Developer", "Diseñador UX", "Capitán"
    disponibilidad_horaria: Optional[str] = None  # ej. "Tardes y fines de semana"
    redes_sociales: Optional[Dict[str, str]] = None  # ej. {"github": "https://...", "linkedin": "https://..."}
    datos_crudos: Optional[Dict[str, Any]] = None

    @field_validator("datos_crudos")
    @classmethod
    def typed_raw_fields(cls, value):
        return ProfileData.model_validate(value).model_dump(exclude_unset=True) if value is not None else None

    @field_validator("rol_preferido", "disponibilidad_horaria", "redes_sociales")
    @classmethod
    def typed_legacy_fields(cls, value, info):
        if value is None:
            return value
        return ProfileData.model_validate({info.field_name: value}).model_dump()[info.field_name]

    @model_validator(mode="after")
    def valid_effective_patch(self):
        patch = self.model_dump(exclude_unset=True)
        raw = patch.pop("datos_crudos", None) or {}
        patch.pop("nombre", None)
        patch.pop("carrera", None)
        ProfileData.model_validate({**raw, **patch})
        return self

class PerfilOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    usuario_id: int
    nombre: str
    correo: str
    carrera: str
    estado_geografico: Optional[str] = None
    municipio: Optional[str] = None
    rol_sistema: Optional[str] = None
    datos_crudos: Dict[str, Any]
    atributos_dinamicos: Dict[str, Any]
    perfil_estructurado_ia: Optional[Dict[str, Any]] = None
    perfil_estado_ia: Optional[str] = None

class PerfilPublicoOut(BaseModel):
    usuario_id: int
    nombre: str
    carrera: str
    estado_geografico: Optional[str] = None
    municipio: Optional[str] = None
    correo: Optional[str] = None
    datos_crudos: Dict[str, Any] = Field(default_factory=dict)
    atributos_dinamicos: Dict[str, Any] = Field(default_factory=dict)
