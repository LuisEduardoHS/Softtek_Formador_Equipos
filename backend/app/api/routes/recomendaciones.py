"""Authenticated public DTOs from the single Fase 5 recommendation engine."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.security import get_current_user, require_self
from app.db.database import get_db
from app.models.evento import Evento
from app.models.usuario import Usuario
from app.services.ai.recommendations.contracts import CandidateRecommendation, ProjectRecommendation
from app.services.ai.recommendations.orm_adapter import candidate_recommendations, project_recommendations

router = APIRouter(prefix="/recomendaciones", tags=["Recomendaciones"])


@router.get("/eventos/{id_evento}/candidatos", response_model=list[CandidateRecommendation])
def candidatos_por_evento(id_evento: int, top_n: int = Query(10, ge=1, le=20),
                          db: Session = Depends(get_db),
                          actor: Usuario = Depends(get_current_user)):
    event = db.get(Evento, id_evento)
    if event is None:
        raise HTTPException(404, "Evento no encontrado.")
    if event.creador_id != actor.id_usuario:
        raise HTTPException(403, "Solo el organizador puede consultar candidatos.")
    return candidate_recommendations(db, event, actor, top_n=top_n)


@router.get("/usuarios/{id_usuario}/proyectos", response_model=list[ProjectRecommendation])
def proyectos_para_usuario(id_usuario: int, top_n: int = Query(10, ge=1, le=20),
                           db: Session = Depends(get_db),
                           actor: Usuario = Depends(get_current_user)):
    require_self(id_usuario, actor)
    try:
        return project_recommendations(db, actor, top_n=top_n)
    except PermissionError as error:
        raise HTTPException(403, str(error)) from error
