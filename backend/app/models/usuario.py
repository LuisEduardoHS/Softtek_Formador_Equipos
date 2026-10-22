from sqlalchemy import Column, Integer, String, ForeignKey, JSON, DateTime
from sqlalchemy.sql import func
from app.db.database import Base

class Usuario(Base):
    __tablename__ = "usuarios"
    
    id_usuario = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nombre = Column(String(150), nullable=False)
    correo = Column(String(100), unique=True, nullable=False)
    carrera = Column(String(100), nullable=False)
    estado_geografico = Column(String(50), nullable=True)
    municipio = Column(String(50), nullable=True)
    estado_cuenta = Column(String(20), default="Activa")
    rol_sistema = Column(String(30), default="Estudiante")
    password_hash = Column(String(255), nullable=False)
    fecha_registro = Column(DateTime, server_default=func.now())

class PerfilUsuario(Base):
    __tablename__ = "perfiles_usuarios"
    
    usuario_id = Column(Integer, ForeignKey("usuarios.id_usuario", ondelete="CASCADE"), primary_key=True)
    datos_crudos = Column(JSON, default={})
    atributos_dinamicos = Column(JSON, default={})