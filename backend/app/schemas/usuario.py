from pydanic import BaseModel, EmailStr

class UsuarioRegistro(BaseModel):
    nombre: str
    correo: EmailStr
    carrera: str
    password: str

class UsuarioLogin(BaseModel):
    correo: EmailStr
    password: str

class UsuarioRespuesta(BaseModel):
    id_usuario: int
    nombre: str
    correo: EmailStr

    class Config:
        from_attributes = True