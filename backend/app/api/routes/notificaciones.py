from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.evento import Evento
from app.models.participante import ParticipanteEvento
from app.models.solicitud import SolicitudEquipo
from app.models.usuario import PerfilUsuario, Usuario

router = APIRouter(prefix="/notificaciones", tags=["Notificaciones"])


def _normalizar(texto):
    return texto.strip().casefold() if isinstance(texto, str) else ""


def _habilidades_visibles(perfil):
    if not perfil:
        return set()

    datos = perfil.datos_crudos or {}
    if not isinstance(datos, dict):
        return set()
    visibilidad = datos.get("visibilidad") or {}
    if not isinstance(visibilidad, dict):
        visibilidad = {}
    if not visibilidad.get("fortalezas", True) or datos.get("pausado", False):
        return set()

    habilidades = datos.get("fortalezas", datos.get("habilidades", []))
    if not isinstance(habilidades, list):
        return set()

    nombres = set()
    for habilidad in habilidades:
        if isinstance(habilidad, str):
            nombre = _normalizar(habilidad)
        elif isinstance(habilidad, dict):
            nombre = _normalizar(habilidad.get("nombre"))
        else:
            nombre = ""
        if nombre:
            nombres.add(nombre)
    return nombres


def _obtener_recomendaciones(db, usuario_id):
    eventos = (
        db.query(Evento)
        .filter(Evento.creador_id == usuario_id, Evento.estado == "Abierto")
        .order_by(Evento.fecha_creacion.desc())
        .all()
    )
    if not eventos:
        return []

    ids_evento = [evento.id_evento for evento in eventos]
    miembros = db.query(ParticipanteEvento).filter(
        ParticipanteEvento.id_evento.in_(ids_evento)
    ).all()
    miembros_por_evento = {}
    for miembro in miembros:
        miembros_por_evento.setdefault(miembro.id_evento, set()).add(miembro.id_usuario)

    invitaciones = db.query(SolicitudEquipo).filter(
        SolicitudEquipo.id_evento.in_(ids_evento),
        SolicitudEquipo.estado.ilike("pendiente"),
    ).all()
    invitados_por_evento = {}
    for invitacion in invitaciones:
        invitados_por_evento.setdefault(invitacion.id_evento, set()).add(invitacion.id_destinatario)

    estudiantes = (
        db.query(Usuario, PerfilUsuario)
        .outerjoin(PerfilUsuario, PerfilUsuario.usuario_id == Usuario.id_usuario)
        .filter(Usuario.estado_cuenta == "Activa", Usuario.id_usuario != usuario_id)
        .all()
    )

    recomendaciones = []
    for evento in eventos:
        detalles = evento.detalles_especificos or {}
        requisitos = evento.requisitos_ia or {}
        if not isinstance(detalles, dict):
            detalles = {}
        if not isinstance(requisitos, dict):
            requisitos = {}
        roles = detalles.get("roles") or requisitos.get("roles") or []
        if not roles and isinstance(requisitos.get("roles_buscados"), list):
            habilidades = requisitos.get("habilidades_obligatorias", [])
            roles = [
                {"nombre": nombre, "habilidades": habilidades}
                for nombre in requisitos["roles_buscados"]
                if isinstance(nombre, str)
            ]
        if not isinstance(roles, list):
            continue

        excluidos = miembros_por_evento.get(evento.id_evento, set())
        excluidos.update(invitados_por_evento.get(evento.id_evento, set()))
        for rol_index, rol in enumerate(roles):
            if not isinstance(rol, dict) or rol.get("cubiertoPor"):
                continue

            nombre_rol = rol.get("nombre")
            habilidades_rol = rol.get("habilidades", [])
            if not isinstance(habilidades_rol, list):
                habilidades_rol = []
            habilidades_globales = requisitos.get("habilidades_obligatorias", [])
            if isinstance(habilidades_globales, list):
                habilidades_rol = [*habilidades_rol, *habilidades_globales]
            requeridas = {
                habilidad
                for valor in habilidades_rol
                if (habilidad := _normalizar(valor))
            }
            nombre_normalizado = _normalizar(nombre_rol)
            if nombre_normalizado:
                requeridas.add(nombre_normalizado)
            if not requeridas:
                continue

            for estudiante, perfil in estudiantes:
                if estudiante.id_usuario in excluidos:
                    continue
                coincidentes = sorted(_habilidades_visibles(perfil) & requeridas)
                if not coincidentes:
                    continue

                recomendaciones.append({
                    "id": f"recomendacion-{evento.id_evento}-{estudiante.id_usuario}-{rol_index}",
                    "grupo": "ia",
                    "texto": (
                        f"{estudiante.nombre} coincide con el rol «{nombre_rol or coincidentes[0]}» "
                        f"en «{evento.titulo}» por {', '.join(coincidentes)}."
                    ),
                    "fecha": None,
                    "accion": {
                        "label": "Ver proyecto",
                        "to": f"/proyectos/{evento.id_evento}",
                    },
                })

    return recomendaciones


@router.get("/{id_usuario}")
def obtener_notificaciones(id_usuario: int, db: Session = Depends(get_db)):
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
        if recibida and estado == "pendiente":
            texto = f"{otra_persona.nombre} te invitó a «{evento.titulo}»."
            accion = {"label": "Responder", "to": "/invitaciones"}
        elif not recibida and estado in {"aceptada", "rechazada"}:
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

    notificaciones.extend(_obtener_recomendaciones(db, id_usuario))

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
