"""Contracts for the JSON fields displayed by the existing project UI."""
from typing import Annotated

from pydantic import (BaseModel, ConfigDict, Field, StrictBool, StrictInt,
                      StringConstraints, ValidationError, field_validator)

from app.schemas.profile_data import Text150, Text50

RoleId = Annotated[str, StringConstraints(strict=True, strip_whitespace=True,
                   min_length=1, max_length=100, pattern=r"^[\w.-]+$")]


class EventRole(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: RoleId
    nombre: Text50
    habilidades: list[Text150] = Field(default_factory=list, max_length=100)
    indispensable: StrictBool = False
    vacantes: Annotated[StrictInt, Field(ge=1, le=8)] = 1

    @field_validator("id", mode="before")
    @classmethod
    def legacy_numeric_id(cls, value):
        return str(value) if type(value) is int else value


class EventDetails(BaseModel):
    model_config = ConfigDict(extra="allow")
    integrantes: Annotated[StrictInt, Field(ge=2, le=8)] = 8
    roles: list[dict] = Field(default_factory=list, max_length=100)
    materia: str = Field(default="", max_length=150)
    tipo: str = Field(default="", max_length=50)
    titulo: str = Field(default="", max_length=150)
    fechaLimite: Annotated[str, StringConstraints(pattern=r"^\d{4}-\d{2}-\d{2}$")] | None = None


def safe_roles(value):
    """Discard incompatible legacy values without changing the stored record."""
    if not isinstance(value, list):
        return []
    result = []
    for index, role in enumerate(value[:100]):
        if not isinstance(role, dict):
            continue
        try:
            # Validate the name with the same contract as new writes.
            valid = EventRole.model_validate({"id": str(index), "nombre": role.get("nombre")})
        except ValidationError:
            continue
        cleaned = valid.model_dump()
        for key in ("id", "vacantes", "indispensable"):
            if key in role:
                try:
                    cleaned[key] = EventRole.model_validate({**cleaned, key: role[key]}).model_dump()[key]
                except ValidationError:
                    pass
        if isinstance(role.get("habilidades"), list):
            for skill in role["habilidades"][:100]:
                try:
                    cleaned["habilidades"].extend(EventRole.model_validate({
                        **cleaned, "habilidades": [skill]}).habilidades)
                except ValidationError:
                    pass
        result.append(cleaned)
    return result


def safe_event_details(value):
    original = value if isinstance(value, dict) else {}
    cleaned = {k: v for k, v in original.items() if not k.startswith("_creation_")}
    for key in EventDetails.model_fields:
        if key == "roles" or key not in original:
            continue
        try:
            cleaned[key] = EventDetails.model_validate({key: original[key]}).model_dump()[key]
        except ValidationError:
            cleaned[key] = EventDetails().model_dump()[key]
    if "roles" in original:
        cleaned["roles"] = safe_roles(original["roles"])
    return cleaned


def safe_event_requirements(value):
    from app.services.ai.schemas import StructuredEventRequirements
    if not isinstance(value, dict):
        return {}
    cleaned = {}
    for key in StructuredEventRequirements.model_fields:
        if key not in value:
            continue
        try:
            cleaned[key] = StructuredEventRequirements.model_validate({key: value[key]}).model_dump()[key]
        except ValidationError:
            pass
    if "roles" in value:  # Compatibility with older events.
        cleaned["roles"] = safe_roles(value["roles"])
    return cleaned
