from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.solicitud import SolicitudEquipo
from app.models.participante import ParticipanteEvento
from app.models.evento import Evento
from app.models.usuario import PerfilUsuario, Usuario
from app.schemas.solicitud import SolicitudCreate, SolicitudUnirse, SolicitudUpdate
from app.core.security import get_current_user, require_self

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
def solicitar_unirse(
    id_evento: int,
    solicitud: SolicitudUnirse,
    solicitante_id: int,
    db: Session = Depends(get_db),
    actor: Usuario = Depends(get_current_user),
):
    require_self(solicitante_id, actor)
    evento = db.query(Evento).filter(Evento.id_evento == id_evento).first()
    if not evento or (evento.estado or "").casefold() != "abierto":
        raise HTTPException(status_code=404, detail="El evento no está disponible.")
    if evento.creador_id == solicitante_id:
        raise HTTPException(status_code=400, detail="No puedes solicitar unirte a tu propio evento.")

    solicitante = db.query(Usuario).filter(Usuario.id_usuario == solicitante_id).first()
    if not solicitante:
        raise HTTPException(status_code=404, detail="No encontramos tu cuenta.")

    participante = db.query(ParticipanteEvento).filter(
        ParticipanteEvento.id_evento == id_evento,
        ParticipanteEvento.id_usuario == solicitante_id,
    ).first()
    if participante:
        raise HTTPException(status_code=409, detail="Ya formas parte de este equipo.")

    detalles = evento.detalles_especificos or {}
    requisitos = evento.requisitos_ia or {}
    roles = detalles.get("roles") if isinstance(detalles, dict) else None
    if not isinstance(roles, list):
        roles = requisitos.get("roles", []) if isinstance(requisitos, dict) else []
    rol = next(
        (
            item for index, item in enumerate(roles)
            if isinstance(item, dict)
            and str(item.get("id", index)) == str(solicitud.rol_esperado)
        ),
        None,
    )
    if not rol:
        raise HTTPException(status_code=400, detail="El rol seleccionado no existe en este evento.")
    if rol.get("cubiertoPor"):
        raise HTTPException(status_code=409, detail="Ese rol ya está cubierto.")

    solicitud_existente = db.query(SolicitudEquipo).filter(
        SolicitudEquipo.id_evento == id_evento,
        SolicitudEquipo.id_remitente == solicitante_id,
        SolicitudEquipo.id_destinatario == evento.creador_id,
        SolicitudEquipo.estado.ilike("pendiente"),
    ).first()
    if solicitud_existente:
        raise HTTPException(status_code=409, detail="Ya tienes una solicitud pendiente para este evento.")

    mensaje = (
        f"{MARCADOR_SOLICITUD_UNIRSE}\n"
        f"Rol solicitado: {rol.get('nombre', 'Participante')}\n\n"
        f"{(solicitud.mensaje_explicacion or '').strip()}"
    )
    nueva_solicitud = SolicitudEquipo(
        id_evento=id_evento,
        id_remitente=solicitante_id,
        id_destinatario=evento.creador_id,
        mensaje_explicacion=mensaje,
        estado="Pendiente",
    )
    db.add(nueva_solicitud)
    db.commit()
    db.refresh(nueva_solicitud)
    return {"id": nueva_solicitud.id_solicitud, "estado": "pendiente"}

@router.post("/invitaciones/")
def crear_solicitud(sol: SolicitudCreate, de_id: int, db: Session = Depends(get_db),
                   actor: Usuario = Depends(get_current_user)):
    require_self(de_id, actor)
    evento = db.query(Evento).filter(Evento.id_evento == sol.id_evento).first()
    destinatario = db.query(Usuario).filter(Usuario.id_usuario == sol.id_destinatario).first()
    if not evento or evento.creador_id != de_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No encontramos un evento tuyo para enviar esta invitación.",
        )
    if evento.estado != "Abierto":
        raise HTTPException(status_code=409, detail="El evento no está abierto a invitaciones.")
    if not destinatario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No encontramos a la persona que quieres invitar.",
        )
    if destinatario.estado_cuenta != "Activa":
        raise HTTPException(status_code=409, detail="La cuenta destinataria no está activa.")
    perfil_destinatario = db.get(PerfilUsuario, destinatario.id_usuario)
    if perfil_destinatario and (perfil_destinatario.datos_crudos or {}).get("pausado", False):
        raise HTTPException(status_code=409, detail="El perfil destinatario no está disponible.")
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
def responder_solicitud(id_solicitud: int, sol_update: SolicitudUpdate, db: Session = Depends(get_db),
                        actor: Usuario = Depends(get_current_user)):
    db_sol = db.query(SolicitudEquipo).filter(SolicitudEquipo.id_solicitud == id_solicitud).first()
    if not db_sol:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")
    require_self(db_sol.id_destinatario, actor)

    estado_normalizado = sol_update.estado.strip().casefold()
    if estado_normalizado not in {"aceptada", "rechazada"}:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="La respuesta debe ser aceptada o rechazada.",
        )
    if (db_sol.estado or "").casefold() != "pendiente":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Esta invitación ya fue respondida.",
        )
    if estado_normalizado == "aceptada":
        evento = db.get(Evento, db_sol.id_evento)
        if not evento or evento.estado != "Abierto":
            raise HTTPException(status_code=409, detail="El evento ya no acepta integrantes.")

    estado_guardado = estado_normalizado.capitalize()
    db_sol.estado = estado_guardado
    
    es_solicitud_unirse = _es_solicitud_unirse(db_sol)
    if estado_normalizado == "aceptada":
        id_usuario_aceptado = db_sol.id_remitente if es_solicitud_unirse else db_sol.id_destinatario
        miembro_existente = db.query(ParticipanteEvento).filter(
            ParticipanteEvento.id_evento == db_sol.id_evento,
            ParticipanteEvento.id_usuario == id_usuario_aceptado,
        ).first()
        if miembro_existente:
            db.commit()
            return {"id": db_sol.id_solicitud, "estado": estado_normalizado}

        _, rol, _ = _detalles_solicitud(db_sol)
        nuevo_participante = ParticipanteEvento(
            id_evento=db_sol.id_evento,
            id_usuario=id_usuario_aceptado,
            rol=rol[:50] or "Participante",
        )
        db.add(nuevo_participante)

    db.commit()
    return {"id": db_sol.id_solicitud, "estado": estado_normalizado}

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
            miembro_asignado = next(
                (
                    miembro for miembro in miembros
                    if miembro["rol"].casefold() == str(nombre_rol).casefold()
                ),
                None,
            )
            roles.append({
                **rol,
                "id": str(rol.get("id", index)),
                "cubiertoPor": (
                    str(miembro_asignado["id"]) if miembro_asignado else rol.get("cubiertoPor")
                ),
            })

        proyecto = {
            "id_evento": evento.id_evento,
            "creador_id": evento.creador_id,
            "categoria_principal": evento.categoria_principal,
            "titulo": evento.titulo,
            "descripcion_libre": evento.descripcion_libre,
            "detalles_especificos": {**detalles, "roles": roles},
            "requisitos_ia": requisitos,
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
