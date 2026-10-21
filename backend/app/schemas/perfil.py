from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class PerfilUpdate(BaseModel):
    bio: Optional[str] = None
    habilidades: Optional[List[str]] = []
    intereses: Optional[List[str]] = []
    rol_preferido: Optional[str] = None  # ej. "Backend Developer", "Diseñador UX", "Capitán"
    disponibilidad_horaria: Optional[str] = None  # ej. "Tardes y fines de semana"
    redes_sociales: Optional[Dict[str, str]] = {}  # ej. {"github": "https://...", "linkedin": "https://..."}

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