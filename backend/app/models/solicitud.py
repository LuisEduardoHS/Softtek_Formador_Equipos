from sqlalchemy import Column, Integer, String, ForeignKey, Text, DateTime
from sqlalchemy.sql import func
from app.db.database import Base

class SolicitudEquipo(Base):
    __tablename__ = "solicitudes_equipo"

    id_solicitud = Column(Integer, primary_key=True, autoincrement=True)
    id_evento = Column(Integer, ForeignKey("eventos.id_evento"), nullable=False)
    id_remitente = Column(Integer, ForeignKey("usuarios.id_usuario"), nullable=False)
    id_destinatario = Column(Integer, ForeignKey("usuarios.id_usuario"), nullable=False)
    estado = Column(String(50), default='Pendiente')
    mensaje_explicacion = Column(Text, nullable=True)
    fecha_envio = Column(DateTime, server_default=func.now())