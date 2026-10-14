from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.usuario import UsuarioRegistro, UsuarioLogin
from app.models.usuario import Usuario, PerfilUsuario

router = APIRouter(prefix="/auth", tags=["Autenticación"])

@router.post("/registro")
def registrar_usuario(user: UsuarioRegistro, db: Session = Depends(get_db)):
    pass
@router.post("/login")
def login_usuario(user: UsuarioLogin, db: Session = Depends(get_db)):
    pass