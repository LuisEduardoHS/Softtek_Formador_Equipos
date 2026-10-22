from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class PerfilUpdate(BaseModel):
    nombre: Optional[str] = None
    carrera: Optional[str] = None
    bio: Optional[str] = None
    habilidades: Optional[List[str]] = None
    intereses: Optional[List[str]] = None
    rol_preferido: Optional[str] = None  # ej. "Backend Developer", "Diseñador UX", "Capitán"
    disponibilidad_horaria: Optional[str] = None  # ej. "Tardes y fines de semana"
    redes_sociales: Optional[Dict[str, str]] = None  # ej. {"github": "https://...", "linkedin": "https://..."}
    datos_crudos: Optional[Dict[str, Any]] = None

class PerfilOut(BaseModel):
    usuario_id: int
    nombre: str
    correo: str
    carrera: str
    estado_geografico: Optional[str] = None
    municipio: Optional[str] = None
    rol_sistema: Optional[str] = None
    datos_crudos: Dict[str, Any]
    atributos_dinamicos: Dict[str, Any]

    class Config:
        from_attributes = True


class PerfilPublicoOut(BaseModel):
    usuario_id: int
    nombre: str
    carrera: str
    estado_geografico: Optional[str] = None
    municipio: Optional[str] = None
    correo: Optional[str] = None
    datos_crudos: Dict[str, Any] = Field(default_factory=dict)
    atributos_dinamicos: Dict[str, Any] = Field(default_factory=dict)