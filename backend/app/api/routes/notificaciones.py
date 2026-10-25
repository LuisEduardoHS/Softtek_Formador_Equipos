from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.evento import Evento
from app.models.participante import ParticipanteEvento
from app.models.solicitud import SolicitudEquipo
from app.models.usuario import Usuario
from app.core.security import get_current_user, require_self
from app.services.ai.recommendations.orm_adapter import candidate_recommendations
from app.api.routes.solicitudes import MARCADOR_SOLICITUD_UNIRSE

router = APIRouter(prefix="/notificaciones", tags=["Notificaciones"])


def _obtener_recomendaciones(db, actor: Usuario):
    """Expose only the public, deterministic engine projection to the owner."""
    eventos = db.query(Evento).filter(
        Evento.creador_id == actor.id_usuario, Evento.estado == "Abierto"
    ).order_by(Evento.fecha_creacion.desc()).all()
    items = []
    for evento in eventos:
        for rec in candidate_recommendations(db, evento, actor, top_n=3):
            fact = (rec.explanation.strengths or rec.explanation.unknowns or
                    ["Revisa la evidencia del candidato."])[0]
            items.append({
                "id": f"recomendacion-{evento.id_evento}-{rec.candidate_id}",
                "grupo": "ia",
                "texto": f"Candidato recomendado para «{evento.titulo}»: {fact}",
                "fecha": None,
                "accion": {"label": "Ver proyecto", "to": f"/proyectos/{evento.id_evento}"},
            })
    return items


@router.get("/{id_usuario}")
def obtener_notificaciones(id_usuario: int, db: Session = Depends(get_db),
                           actor: Usuario = Depends(get_current_user)):
    require_self(id_usuario, actor)
    usuario = db.query(Usuario).filter(Usuario.id_usuario == id_usuario).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")

    solicitudes = db.query(SolicitudEquipo).filter(
        (SolicitudEquipo.id_destinatario == id_usuario)
        | (
            (SolicitudEquipo.id_remitente == id_usuario)
            & SolicitudEquipo.estado.ilike("aceptada")
        )
        | (
            (SolicitudEquipo.id_remitente == id_usuario)
            & SolicitudEquipo.estado.ilike("rechazada")
        )
    ).order_by(SolicitudEquipo.fecha_envio.desc()).all()

    notificaciones = []
    for solicitud in solicitudes:
        evento = db.query(Evento).filter(Evento.id_evento == solicitud.id_evento).first()
        otra_persona_id = (
            solicitud.id_remitente
            if solicitud.id_destinatario == id_usuario
            else solicitud.id_destinatario
        )
        otra_persona = db.query(Usuario).filter(
            Usuario.id_usuario == otra_persona_id
        ).first()
        if not evento or not otra_persona:
            continue

        recibida = solicitud.id_destinatario == id_usuario
        estado = (solicitud.estado or "").casefold()
        es_solicitud_unirse = (solicitud.mensaje_explicacion or "").startswith(
            MARCADOR_SOLICITUD_UNIRSE
        )
        if recibida and estado == "pendiente":
            if es_solicitud_unirse:
                texto = f"{otra_persona.nombre} solicita unirse a «{evento.titulo}»."
            else:
                texto = f"{otra_persona.nombre} te invitó a «{evento.titulo}»."
            accion = {"label": "Responder", "to": "/invitaciones"}
        elif not recibida and estado in {"aceptada", "rechazada"}:
            if es_solicitud_unirse:
                respuesta = "aceptó" if estado == "aceptada" else "rechazó"
                texto = f"{otra_persona.nombre} {respuesta} tu solicitud para unirte a «{evento.titulo}»."
                accion = {
                    "label": "Ver equipo" if estado == "aceptada" else "Ver solicitudes",
                    "to": "/equipos" if estado == "aceptada" else "/invitaciones",
                }
            else:
                respuesta = "aceptó" if estado == "aceptada" else "rechazó"
                texto = f"{otra_persona.nombre} {respuesta} tu invitación a «{evento.titulo}»."
                accion = {"label": "Ver invitaciones", "to": "/invitaciones"}
        else:
            continue

        notificaciones.append({
            "id": f"invitacion-{solicitud.id_solicitud}",
            "grupo": "invitaciones",
            "texto": texto,
            "fecha": solicitud.fecha_envio.isoformat() if solicitud.fecha_envio else None,
            "accion": accion,
        })

    notificaciones.extend(_obtener_recomendaciones(db, actor))

    eventos_del_usuario = db.query(Evento.id_evento).outerjoin(
        ParticipanteEvento, ParticipanteEvento.id_evento == Evento.id_evento
    ).filter(
        (Evento.creador_id == id_usuario)
        | (ParticipanteEvento.id_usuario == id_usuario)
    ).distinct().subquery()

    actualizaciones = (
        db.query(ParticipanteEvento, Usuario.nombre, Evento.titulo)
        .join(Usuario, Usuario.id_usuario == ParticipanteEvento.id_usuario)
        .join(Evento, Evento.id_evento == ParticipanteEvento.id_evento)
        .filter(
            ParticipanteEvento.id_evento.in_(
                db.query(eventos_del_usuario.c.id_evento)
            ),
            ParticipanteEvento.id_usuario != id_usuario,
        )
        .order_by(ParticipanteEvento.fecha_ingreso.desc())
        .limit(50)
        .all()
    )
    for participacion, nombre, titulo in actualizaciones:
        notificaciones.append({
            "id": f"equipo-{participacion.id_participacion}",
            "grupo": "equipo",
            "texto": f"{nombre} se unió al equipo «{titulo}».",
            "fecha": participacion.fecha_ingreso.isoformat() if participacion.fecha_ingreso else None,
            "accion": {
                "label": "Ver proyecto",
                "to": f"/proyectos/{participacion.id_evento}",
            },
        })

    return notificaciones
