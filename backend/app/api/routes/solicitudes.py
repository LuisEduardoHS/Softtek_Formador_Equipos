from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.solicitud import SolicitudEquipo
from app.models.participante import ParticipanteEvento
from app.models.evento import Evento
from app.models.usuario import PerfilUsuario, Usuario
from app.schemas.solicitud import SolicitudCreate, SolicitudUnirse, SolicitudUpdate
from app.core.security import get_current_user, require_self
from app.services.team_rules import (team_transaction, lock_event, available_role, reject_pending_pair)

router = APIRouter()
MARCADOR_SOLICITUD_UNIRSE = "[SOLICITUD_UNIRSE]"


def _es_solicitud_unirse(solicitud):
    return (solicitud.mensaje_explicacion or "").startswith(MARCADOR_SOLICITUD_UNIRSE)


def _detalles_solicitud(solicitud):
    mensaje = solicitud.mensaje_explicacion or ""
    tipo_solicitud = "unirse" if _es_solicitud_unirse(solicitud) else "invitacion"
    rol = "Participante"

    if tipo_solicitud == "unirse":
        contenido = mensaje[len(MARCADOR_SOLICITUD_UNIRSE):].lstrip("\n")
        if contenido.startswith("Rol solicitado: "):
            rol, _, contenido = contenido.partition("\n\n")
            rol = rol.removeprefix("Rol solicitado: ").strip()
            mensaje = contenido
        else:
            mensaje = contenido
    else:
        marcador_rol = "\n\nRol propuesto: "
        if marcador_rol in mensaje:
            mensaje, rol = mensaje.rsplit(marcador_rol, 1)

    return tipo_solicitud, rol, mensaje

@router.get("/invitaciones/{id_usuario}")
def obtener_invitaciones(id_usuario: int, db: Session = Depends(get_db),
                         actor: Usuario = Depends(get_current_user)):
    require_self(id_usuario, actor)
    solicitudes = db.query(SolicitudEquipo).filter(
        (SolicitudEquipo.id_destinatario == id_usuario)
        | (SolicitudEquipo.id_remitente == id_usuario)
    ).order_by(SolicitudEquipo.fecha_envio.desc()).all()
    
    resultado = []
    for sol in solicitudes:
        evento = db.query(Evento).filter(Evento.id_evento == sol.id_evento).first()
        otra_persona_id = (
            sol.id_remitente if sol.id_destinatario == id_usuario else sol.id_destinatario
        )
        otra_persona = db.query(Usuario).filter(
            Usuario.id_usuario == otra_persona_id
        ).first()
        if not evento or not otra_persona:
            continue

        recibida = sol.id_destinatario == id_usuario
        tipo_solicitud, rol, mensaje = _detalles_solicitud(sol)

        resultado.append({
            "id": sol.id_solicitud,
            "tipo": "recibida" if recibida else "enviada",
            "deId": sol.id_remitente,
            "paraId": sol.id_destinatario,
            "projectId": sol.id_evento,
            "mensaje": mensaje,
            "rol": rol,
            "tipoSolicitud": tipo_solicitud,
            "estado": (sol.estado or "Pendiente").casefold(),
            "fecha": sol.fecha_envio.isoformat() if sol.fecha_envio else None,
            "remitente": (
                {"id": sol.id_remitente, "nombre": otra_persona.nombre}
                if recibida
                else None
            ),
            "destinatario": (
                {"id": sol.id_destinatario, "nombre": otra_persona.nombre}
                if not recibida
                else None
            ),
            "proyecto": {"id": evento.id_evento, "titulo": evento.titulo},
        })
    return resultado


@router.post("/eventos/{id_evento}/solicitudes")
def solicitar_unirse(id_evento: int, solicitud: SolicitudUnirse, solicitante_id: int,
                     db: Session = Depends(get_db), actor: Usuario = Depends(get_current_user)):
    require_self(solicitante_id, actor)
    with team_transaction(db):
        evento = lock_event(db, id_evento)
        rol = available_role(db, evento, actor.id_usuario, solicitud.rol_esperado)
        reject_pending_pair(db, evento, actor.id_usuario)
        nueva = SolicitudEquipo(
            id_evento=id_evento, id_remitente=actor.id_usuario, id_destinatario=evento.creador_id,
            mensaje_explicacion=(f"{MARCADOR_SOLICITUD_UNIRSE}\nRol solicitado: {rol}\n\n"
                                 f"{(solicitud.mensaje_explicacion or '').strip()}"), estado="Pendiente")
        db.add(nueva)
        db.flush()
        result = {"id": nueva.id_solicitud, "estado": "pendiente"}
    return result


@router.post("/invitaciones/")
def crear_solicitud(sol: SolicitudCreate, de_id: int, db: Session = Depends(get_db),
                    actor: Usuario = Depends(get_current_user)):
    require_self(de_id, actor)
    with team_transaction(db):
        evento = lock_event(db, sol.id_evento)
        if evento.creador_id != actor.id_usuario:
            raise HTTPException(403, "Solo quien creó el evento puede invitar.")
        # Read the legacy footer for old clients, but construct the stored type/role
        # ourselves so user text cannot change who is enrolled on acceptance.
        message = (sol.mensaje_explicacion or "").strip()
        if message.startswith(MARCADOR_SOLICITUD_UNIRSE):
            raise HTTPException(422, "El mensaje contiene un marcador reservado.")
        role_hint = sol.rol_esperado
        if "\n\nRol propuesto: " in message:
            message, legacy_role = message.rsplit("\n\nRol propuesto: ", 1)
            if role_hint in (None, "Participante"):
                role_hint = legacy_role
        role = available_role(db, evento, sol.id_destinatario, role_hint)
        reject_pending_pair(db, evento, sol.id_destinatario)
        nueva = SolicitudEquipo(
            id_evento=evento.id_evento, id_remitente=actor.id_usuario,
            id_destinatario=sol.id_destinatario,
            mensaje_explicacion=f"{message}\n\nRol propuesto: {role}", estado="Pendiente")
        db.add(nueva)
        db.flush()
        result = {"id": nueva.id_solicitud, "estado": "pendiente"}
    return result


@router.patch("/invitaciones/{id_solicitud}")
def responder_solicitud(id_solicitud: int, sol_update: SolicitudUpdate, db: Session = Depends(get_db),
                        actor: Usuario = Depends(get_current_user)):
    estado = sol_update.estado.strip().casefold()
    if estado not in {"aceptada", "rechazada"}:
        raise HTTPException(422, "La respuesta debe ser aceptada o rechazada.")
    with team_transaction(db):
        # Lock order is always event -> request -> roster/users. The first lookup
        # locates the event only; never use its cached state to authorize acceptance.
        hint = db.get(SolicitudEquipo, id_solicitud)
        if not hint:
            raise HTTPException(404, "Solicitud no encontrada.")
        evento = lock_event(db, hint.id_evento)
        sol = db.query(SolicitudEquipo).filter_by(id_solicitud=id_solicitud).populate_existing().with_for_update().one()
        require_self(sol.id_destinatario, actor)
        if (sol.estado or "").casefold() != "pendiente":
            raise HTTPException(409, "Esta solicitud ya fue respondida.")
        es_adhesion = _es_solicitud_unirse(sol)
        if (es_adhesion and sol.id_destinatario != evento.creador_id) or (
                not es_adhesion and sol.id_remitente != evento.creador_id):
            raise HTTPException(409, "La solicitud ya no corresponde al creador actual del evento.")
        if estado == "aceptada":
            user_id = sol.id_remitente if es_adhesion else sol.id_destinatario
            _, requested_role, _ = _detalles_solicitud(sol)
            role = available_role(db, evento, user_id, requested_role)
            db.add(ParticipanteEvento(id_evento=evento.id_evento, id_usuario=user_id, rol=role))
        sol.estado = estado.capitalize()
        db.flush()
    return {"id": id_solicitud, "estado": estado}


@router.get("/equipos/{id_usuario}")
def obtener_equipos(id_usuario: int, db: Session = Depends(get_db),
                    actor: Usuario = Depends(get_current_user)):
    require_self(id_usuario, actor)
    usuario_actual = db.query(Usuario).filter(Usuario.id_usuario == id_usuario).first()
    if not usuario_actual:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")

    eventos_usuario = db.query(Evento).outerjoin(
        ParticipanteEvento, ParticipanteEvento.id_evento == Evento.id_evento
    ).filter(
        (Evento.creador_id == id_usuario)
        | (ParticipanteEvento.id_usuario == id_usuario)
    ).distinct().order_by(Evento.fecha_creacion.desc()).all()

    resultado = []
    for evento in eventos_usuario:
        participaciones = db.query(ParticipanteEvento).filter(
            ParticipanteEvento.id_evento == evento.id_evento
        ).all()
        miembros_ids = {participacion.id_usuario for participacion in participaciones}
        miembros_ids.add(evento.creador_id)
        usuarios = db.query(Usuario, PerfilUsuario).outerjoin(
            PerfilUsuario, PerfilUsuario.usuario_id == Usuario.id_usuario
        ).filter(Usuario.id_usuario.in_(miembros_ids)).all()
        participaciones_por_usuario = {
            participacion.id_usuario: participacion for participacion in participaciones
        }

        miembros = []
        for usuario, perfil in usuarios:
            datos = (perfil.datos_crudos or {}) if perfil else {}
            if not isinstance(datos, dict):
                datos = {}
            visibilidad = datos.get("visibilidad") or {}
            if not isinstance(visibilidad, dict):
                visibilidad = {}
            fortalezas = datos.get("fortalezas", datos.get("habilidades", []))
            if not visibilidad.get("fortalezas", True) or datos.get("pausado", False):
                fortalezas = []
            if not isinstance(fortalezas, list):
                fortalezas = []
            fortalezas = [
                {"nombre": fortaleza} if isinstance(fortaleza, str) else fortaleza
                for fortaleza in fortalezas
                if isinstance(fortaleza, str) or (
                    isinstance(fortaleza, dict) and isinstance(fortaleza.get("nombre"), str)
                )
            ]
            participacion = participaciones_por_usuario.get(usuario.id_usuario)
            miembros.append({
                "id": usuario.id_usuario,
                "nombre": usuario.nombre,
                "carrera": usuario.carrera,
                "correo": usuario.correo if visibilidad.get("correo", False) else None,
                "semestre": datos.get("semestre"),
                "fortalezas": fortalezas,
                "rol": participacion.rol if participacion else "Creador",
            })

        detalles = evento.detalles_especificos or {}
        requisitos = evento.requisitos_ia or {}
        detalles = detalles if isinstance(detalles, dict) else {}
        requisitos = requisitos if isinstance(requisitos, dict) else {}
        roles_evento = detalles.get("roles")
        if not isinstance(roles_evento, list):
            roles_evento = requisitos.get("roles", [])
        roles_evento = roles_evento if isinstance(roles_evento, list) else []
        roles = []
        for index, rol in enumerate(roles_evento):
            if not isinstance(rol, dict):
                continue
            nombre_rol = rol.get("nombre", "Rol sin nombre")
            assigned = [miembro for miembro in miembros
                        if miembro["rol"].strip().casefold() == str(nombre_rol).strip().casefold()]
            slots = rol.get("vacantes", 1)
            roles.append({
                **rol, "id": str(rol.get("id", index)), "ocupados": len(assigned),
                "integrantesIds": [str(member["id"]) for member in assigned],
                "cubiertoPor": str(assigned[0]["id"]) if assigned and len(assigned) >= slots else None,
            })

        proyecto = {
            "id_evento": evento.id_evento,
            "creador_id": evento.creador_id,
            "categoria_principal": evento.categoria_principal,
            "titulo": evento.titulo,
            "descripcion_libre": evento.descripcion_libre,
            "detalles_especificos": {**detalles, "roles": roles},
            "requisitos_ia": requisitos if evento.requisitos_confirmados_at else {},
            "requisitos_confirmados": bool(evento.requisitos_confirmados_at),
            "estado_ia": evento.estado_ia if evento.creador_id == actor.id_usuario else None,
            "estado": evento.estado,
            "fecha_creacion": evento.fecha_creacion.isoformat() if evento.fecha_creacion else None,
        }
        resultado.append({
            "id": str(evento.id_evento),
            "projectId": str(evento.id_evento),
            "nombre": evento.titulo,
            "rol": next(
                (
                    participacion.rol for participacion in participaciones
                    if participacion.id_usuario == id_usuario
                ),
                "Creador" if evento.creador_id == id_usuario else "Participante",
            ),
            "miembros": miembros,
            "proyecto": proyecto,
        })
    return resultado
