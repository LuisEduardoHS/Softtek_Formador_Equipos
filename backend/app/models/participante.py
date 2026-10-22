from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.sql import func
from app.db.database import Base

class ParticipanteEvento(Base):
    __tablename__ = "participantes_evento"
    __table_args__ = (UniqueConstraint("id_evento", "id_usuario", name="uq_participante_evento_usuario"),)

    id_participacion = Column(Integer, primary_key=True, autoincrement=True)
    id_evento = Column(Integer, ForeignKey("eventos.id_evento"), nullable=False)
    id_usuario = Column(Integer, ForeignKey("usuarios.id_usuario"), nullable=False)
    rol = Column(String(50), default='Participante')
    fecha_ingreso = Column(DateTime, server_default=func.now())
