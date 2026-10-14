from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.usuario import ActualizarPerfil
from app.models.usuario import PerfilUsuario

router = APIRouter(prefix="/perfil", tags=["Perfiles e IA"])

@router.post("/procesar-texto")
def procesar_texto_perfil(datos: ActualizarPerfil, db: Session = Depends(get_db)):
    pass