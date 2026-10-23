from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime

class EventoCreate(BaseModel):
    creador_id: int
    titulo: str
    categoria_principal: Optional[str] = "Academico"
    descripcion_libre: Optional[str] = None
    detalles_especificos: Optional[Dict[str, Any]] = {}
    requisitos_ia: Optional[Dict[str, Any]] = {}

class EventoUpdate(BaseModel):
    categoria_principal: str
    descripcion_libre: Optional[str] = None
    detalles_especificos: Dict[str, Any]
    requisitos_ia: Dict[str, Any]
    integrantes: int = Field(ge=2, le=8)

class EventoOut(BaseModel):
    id_evento: int
    creador_id: int
    creador_nombre: Optional[str] = None
    categoria_principal: str
    titulo: str
    descripcion_libre: Optional[str] = None
    detalles_especificos: Optional[Dict[str, Any]] = {}
    requisitos_ia: Optional[Dict[str, Any]] = {}
    embedding_requisitos: Optional[Dict[str, Any]] = {}
    estado: str
    fecha_creacion: datetime

    class Config:
        from_attributes = True