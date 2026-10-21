from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from app.db.database import Base

class Evento(Base):
    __tablename__ = "eventos"

    id_evento = Column(Integer, primary_key=True, index=True, autoincrement=True)
    creador_id = Column(Integer, ForeignKey("usuarios.id_usuario", ondelete="CASCADE"), nullable=False)
    categoria_principal = Column(String(50), nullable=False, default="Academico")
    titulo = Column(String(150), nullable=False)
    descripcion_libre = Column(Text, nullable=True)
    detalles_especificos = Column(JSON, default={})
    requisitos_ia = Column(JSON, default={})
    embedding_requisitos = Column(JSON, default={})
    estado = Column(String(30), default="Abierto")
    fecha_creacion = Column(DateTime, server_default=func.now())