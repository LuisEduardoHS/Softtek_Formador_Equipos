from sqlalchemy import Column, Integer, String, ForeignKey, JSON
from app.db.database import Base

class Usuario(Base):
    __tablename__ = "usuarios"

    id_usuario = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(50), nullable=False)
    correo = Column(String(100), unique=True, nullable=False)
    carrera = Column(String(100), nullable=False)
    estado_cuenta = Column(String(20), default="activo")
    password = Column(String(255), nullable=False)

    class PerfilUsuario(Base):
        __tablename__ = "perfiles_usuarios"

       usuario_id = Column(Integer, ForeignKey("usuarios.id_usuario"), ondelete="CASCADE", primary_key=True)
       datos_crudos = Column(JSON, default={})
       atributos_dinamicos = Column(JSON, default={})