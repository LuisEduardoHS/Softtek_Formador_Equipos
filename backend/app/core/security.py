"""Server-verified bearer identity; client-provided user IDs are never authority."""

import os
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.usuario import Usuario

_bearer = HTTPBearer(auto_error=False)
_ISSUER = "softtek-equipos"


def _secret() -> str:
    secret = os.getenv("AUTH_SECRET", "")
    if len(secret) < 32:
        raise RuntimeError("AUTH_SECRET debe tener al menos 32 caracteres.")
    return secret


def create_access_token(user_id: int) -> str:
    now = datetime.now(timezone.utc)
    return jwt.encode(
        {"sub": str(user_id), "iss": _ISSUER, "iat": now,
         "exp": now + timedelta(hours=8)},
        _secret(), algorithm="HS256",
    )


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> Usuario:
    unauthorized = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                 detail="Credencial inválida o ausente.",
                                 headers={"WWW-Authenticate": "Bearer"})
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise unauthorized
    try:
        claims = jwt.decode(credentials.credentials, _secret(), algorithms=["HS256"],
                            issuer=_ISSUER, options={"require": ["sub", "exp", "iat", "iss"]})
        subject = claims["sub"]
        if not isinstance(subject, str) or not subject.isdecimal() or int(subject) <= 0:
            raise unauthorized
    except (jwt.PyJWTError, ValueError) as error:
        raise unauthorized from error
    user = db.get(Usuario, int(subject))
    if user is None:
        raise unauthorized
    if user.estado_cuenta != "Activa":
        raise HTTPException(status_code=403, detail="Cuenta inactiva.")
    return user


def require_self(resource_user_id: int, actor: Usuario) -> None:
    if resource_user_id != actor.id_usuario:
        raise HTTPException(status_code=403, detail="No tienes acceso a este recurso.")
