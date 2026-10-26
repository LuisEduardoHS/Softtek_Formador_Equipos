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
    requisitos_borrador_ia = Column(JSON, nullable=True)
    embedding_requisitos = Column(JSON, nullable=True)  # list[float] o NULL
    estado_ia = Column(String(32), nullable=True)
    requisitos_fuente_revision = Column(String(64), nullable=True)
    embedding_model = Column(String(100), nullable=True)
    embedding_pipeline = Column(String(60), nullable=True)
    embedding_fuente_revision = Column(String(64), nullable=True)
    requisitos_confirmados_at = Column(DateTime, nullable=True)
    procesado_at = Column(DateTime, nullable=True)
    estado = Column(String(30), default="Abierto")
    fecha_creacion = Column(DateTime, server_default=func.now())
