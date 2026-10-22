from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.db.database import get_db
from app.models.evento import Evento
from app.models.usuario import Usuario
from app.schemas.evento import EventoCreate, EventoOut

router = APIRouter(prefix="/eventos", tags=["Eventos y Convocatorias"])


@router.post("/", response_model=EventoOut, status_code=status.HTTP_201_CREATED)
def crear_evento(evento: EventoCreate, db: Session = Depends(get_db)):
    creador = db.query(Usuario).filter(Usuario.id_usuario == evento.creador_id).first()
    if not creador:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El usuario creador especificado no existe."
        )

    nuevo_evento = Evento(
        creador_id=evento.creador_id,
        titulo=evento.titulo,
        categoria_principal=evento.categoria_principal,
        descripcion_libre=evento.descripcion_libre,
        detalles_especificos=evento.detalles_especificos or {},
        requisitos_ia=evento.requisitos_ia or {},
        embedding_requisitos={}
    )

    db.add(nuevo_evento)
    db.commit()
    db.refresh(nuevo_evento)
    return nuevo_evento


@router.get("/", response_model=List[EventoOut])
def listar_eventos(
    categoria_principal: Optional[str] = Query(None, description="Filtrar por categoría (ej. Academico, Deportivo, Social, Hackathon)"),
    estado: Optional[str] = Query(None, description="Filtrar por estado (ej. Abierto, Finalizado)"),
    db: Session = Depends(get_db)
):
    query = db.query(Evento)
    if categoria_principal:
        query = query.filter(Evento.categoria_principal == categoria_principal)
    if estado:
        query = query.filter(Evento.estado == estado)
    
    return query.all()


@router.get("/{id_evento}", response_model=EventoOut)
def obtener_evento(id_evento: int, db: Session = Depends(get_db)):
    evento = db.query(Evento).filter(Evento.id_evento == id_evento).first()
    if not evento:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evento no encontrado."
        )
    return evento