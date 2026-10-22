from pydantic import BaseModel
from typing import Optional

class SolicitudCreate(BaseModel):
    id_destinatario: int
    id_evento: int
    mensaje_explicacion: Optional[str] = None
    rol_esperado: Optional[str] = 'Participante' # Lo usaremos si aceptan

class SolicitudUpdate(BaseModel):
    estado: str  # "Aceptada" o "Rechazada"

class SolicitudUnirse(BaseModel):
    rol_esperado: str
    mensaje_explicacion: Optional[str] = None