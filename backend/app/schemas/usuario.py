from pydantic import BaseModel, EmailStr
from typing import Optional

class UsuarioRegistro(BaseModel):
    nombre: str
    correo: EmailStr
    carrera: str
    estado_geografico: Optional[str] = None
    municipio: Optional[str] = None
    password: str

class UsuarioLogin(BaseModel):
    correo: EmailStr
    password: str