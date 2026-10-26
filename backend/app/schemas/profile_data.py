"""Validate known JSON fields on writes; safely project legacy data on reads."""
from typing import Annotated, Any

from pydantic import (AfterValidator, BaseModel, ConfigDict, Field, StrictBool,
                      StrictInt, StringConstraints, ValidationError, field_validator)


def no_controls(value: str) -> str:
    if any(ord(char) < 32 for char in value):
        raise ValueError("El texto no admite caracteres de control.")
    return value


Text150 = Annotated[str, StringConstraints(strict=True, strip_whitespace=True,
                     min_length=1, max_length=150), AfterValidator(no_controls)]
Text200 = Annotated[str, StringConstraints(strict=True, strip_whitespace=True,
                     min_length=1, max_length=200), AfterValidator(no_controls)]
Text50 = Annotated[str, StringConstraints(strict=True, strip_whitespace=True,
                    min_length=1, max_length=50), AfterValidator(no_controls)]
TextList = Annotated[list[Text200], Field(max_length=100)]
VISIBILITY_DEFAULTS = {"fortalezas": True, "intereses": True, "disponibilidad": True,
                       "reforzar": False, "correo": False}


def visibility_fields(value):
    if set(value) - VISIBILITY_DEFAULTS.keys():
        raise ValueError("Campo de visibilidad desconocido.")
    return value


class ProfileSkill(BaseModel):
    model_config = ConfigDict(extra="forbid")
    nombre: Text150
    nivel: Text50 | None = None


class ProfileData(BaseModel):
    # Existing UI/legacy metadata is retained, but every consumed field is typed.
    model_config = ConfigDict(extra="allow")
    fortalezas: list[Text150 | ProfileSkill] = Field(default_factory=list, max_length=100)
    habilidades: list[Text150] = Field(default_factory=list, max_length=100)
    reforzar: TextList = Field(default_factory=list)
    intereses: TextList = Field(default_factory=list)
    experiencia: TextList = Field(default_factory=list)
    disponibilidad: TextList = Field(default_factory=list)
    visibilidad: dict[str, StrictBool] = Field(default_factory=dict)
    pausado: StrictBool = False
    consentimiento_recomendaciones: StrictBool = False
    semestre: Annotated[StrictInt, Field(ge=1, le=20)] = 1
    bio: str = Field(default="", max_length=1000)
    rol_preferido: Text150 | None = None
    disponibilidad_horaria: str | None = Field(default=None, max_length=1000)
    redes_sociales: dict[Text50, Annotated[str, StringConstraints(max_length=1000)]] = Field(default_factory=dict)

    _visibility = field_validator("visibilidad")(visibility_fields)


def safe_profile_data(value: Any) -> dict:
    """Read-only sanitization. Corrupt privacy settings never grant disclosure."""
    original = value if isinstance(value, dict) else {}
    cleaned = dict(original)
    for key in ProfileData.model_fields:
        if key not in original or key == "visibilidad":
            continue
        try:
            cleaned[key] = ProfileData.model_validate({key: original[key]}).model_dump(exclude_unset=True)[key]
        except ValidationError:
            cleaned.pop(key, None)
    visibility = original.get("visibilidad", {})
    invalid = (not isinstance(visibility, dict) or
               any(k not in VISIBILITY_DEFAULTS or type(v) is not bool for k, v in visibility.items()))
    cleaned["visibilidad"] = ({k: False for k in VISIBILITY_DEFAULTS} if invalid else dict(VISIBILITY_DEFAULTS))
    if isinstance(visibility, dict):
        cleaned["visibilidad"].update({k: v for k, v in visibility.items()
                                      if k in VISIBILITY_DEFAULTS and type(v) is bool})
    if "pausado" in original and type(original["pausado"]) is not bool:
        cleaned["pausado"] = True
    return cleaned
