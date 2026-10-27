from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
from app.schemas.profile_data import Text150


class _PasswordInput(BaseModel):
    @field_validator("password", check_fields=False)
    @classmethod
    def valid_password_text(cls, value):
        try:
            value.encode("utf-8")
        except UnicodeError as error:
            raise ValueError("La contraseña debe ser texto Unicode válido.") from error
        if "\x00" in value or not value.strip():
            raise ValueError("La contraseña no puede estar vacía ni contener NUL.")
        return value  # Never strip or normalize a password.

class UsuarioRegistro(_PasswordInput):
    nombre: Text150
    correo: EmailStr = Field(max_length=100)
    carrera: str = Field(min_length=1, max_length=100)
    estado_geografico: Optional[str] = Field(default=None, max_length=50)
    municipio: Optional[str] = Field(default=None, max_length=50)
    password: str = Field(min_length=8, max_length=128, repr=False)

class UsuarioLogin(_PasswordInput):
    correo: EmailStr = Field(max_length=100)
    # Existing short bcrypt passwords remain usable and migrate on valid login.
    password: str = Field(min_length=1, max_length=128, repr=False)
