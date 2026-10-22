from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.solicitud import SolicitudEquipo
from app.models.participante import ParticipanteEvento
from app.models.evento import Evento
from app.models.usuario import Usuario
from app.schemas.solicitud import SolicitudCreate, SolicitudUpdate

router = APIRouter()

@router.get("/invitaciones/{id_usuario}")
def obtener_invitaciones(id_usuario: int, db: Session = Depends(get_db)):
    # Buscar solicitudes pendientes dirigidas al usuario
    solicitudes = db.query(SolicitudEquipo).filter(
        SolicitudEquipo.id_destinatario == id_usuario,
        SolicitudEquipo.estado == 'Pendiente'
    ).all()
    
    resultado = []
    for sol in solicitudes:
        remitente = db.query(Usuario).filter(Usuario.id_usuario == sol.id_remitente).first()
        
        resultado.append({
            "id": sol.id_solicitud,
            "tipo": "recibida",
            "deId": sol.id_remitente,
            "paraId": sol.id_destinatario,
            "projectId": sol.id_evento,
            "mensaje": sol.mensaje_explicacion,
            "estado": "pendiente",
            "remitente": {"nombre": remitente.nombre if remitente else "Usuario"}
        })
    return resultado

@router.post("/invitaciones/")
def crear_solicitud(sol: SolicitudCreate, de_id: int, db: Session = Depends(get_db)):
    evento = db.query(Evento).filter(Evento.id_evento == sol.id_evento).first()
    destinatario = db.query(Usuario).filter(Usuario.id_usuario == sol.id_destinatario).first()
    if not evento or evento.creador_id != de_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No encontramos un evento tuyo para enviar esta invitación.",
        )
    if not destinatario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No encontramos a la persona que quieres invitar.",
        )
    if sol.id_destinatario == de_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No puedes invitarte a tu propio evento.",
        )

    solicitud_existente = db.query(SolicitudEquipo).filter(
        SolicitudEquipo.id_evento == sol.id_evento,
        SolicitudEquipo.id_remitente == de_id,
        SolicitudEquipo.id_destinatario == sol.id_destinatario,
        SolicitudEquipo.estado == "Pendiente",
    ).first()
    if solicitud_existente:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya enviaste una invitación pendiente a esta persona para el evento.",
        )

    nueva_solicitud = SolicitudEquipo(
        id_evento=sol.id_evento,
        id_remitente=de_id,
        id_destinatario=sol.id_destinatario,
        mensaje_explicacion=sol.mensaje_explicacion,
        estado="Pendiente"
    )
    db.add(nueva_solicitud)
    db.commit()
    db.refresh(nueva_solicitud)
    return {"id": nueva_solicitud.id_solicitud, "estado": "pendiente"}

@router.patch("/invitaciones/{id_solicitud}")
def responder_solicitud(id_solicitud: int, sol_update: SolicitudUpdate, db: Session = Depends(get_db)):
    db_sol = db.query(SolicitudEquipo).filter(SolicitudEquipo.id_solicitud == id_solicitud).first()
    if not db_sol:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")
    
    estado_normalizado = sol_update.estado.capitalize() # Asegura que sea "Aceptada" o "Rechazada"
    db_sol.estado = estado_normalizado
    
    # LÓGICA CLAVE: Si acepta, lo metemos a la tabla de participantes
    if estado_normalizado == "Aceptada":
        nuevo_participante = ParticipanteEvento(
            id_evento=db_sol.id_evento,
            id_usuario=db_sol.id_destinatario
        )
        db.add(nuevo_participante)

    db.commit()
    return {"id": db_sol.id_solicitud, "estado": db_sol.estado.lower()}

@router.get("/equipos/{id_usuario}")
def obtener_equipos(id_usuario: int, db: Session = Depends(get_db)):
    # Los equipos ahora se leen directo de la tabla de participantes reales
    participaciones = db.query(ParticipanteEvento).filter(
        ParticipanteEvento.id_usuario == id_usuario
    ).all()

    resultado = []
    for part in participaciones:
        resultado.append({
            "id": part.id_participacion,
            "projectId": part.id_evento,
            "rol": part.rol
        })
    return resultado