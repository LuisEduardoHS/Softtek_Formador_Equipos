"""Participation invariants shared by invitations, applications and event edits."""
from contextlib import contextmanager

from fastapi import HTTPException
from sqlalchemy import or_, and_, update
from sqlalchemy.exc import IntegrityError, OperationalError

from app.models.evento import Evento
from app.models.participante import ParticipanteEvento
from app.models.solicitud import SolicitudEquipo
from app.models.usuario import Usuario, PerfilUsuario


def role_key(value):
    return " ".join(str(value or "").split()).casefold()


@contextmanager
def team_transaction(db):
    # Authentication may already have started this session's transaction.
    try:
        yield
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(409, "El equipo cambió durante la operación. Recarga y reintenta.") from error
    except OperationalError as error:
        db.rollback()
        code = error.orig.args[0] if error.orig.args else None
        if code in {1205, 1213} or "locked" in str(error.orig).lower():
            raise HTTPException(409, "El equipo cambió durante la operación. Recarga y reintenta.") from error
        raise
    except Exception:
        db.rollback()
        raise


def lock_event(db, event_id):
    # MySQL uses a current/locking read, even if authentication read an older
    # REPEATABLE READ snapshot. SQLite has no FOR UPDATE: acquire its writer lock.
    if db.get_bind().dialect.name == "sqlite":
        db.execute(update(Evento).where(Evento.id_evento == event_id)
                   .values(estado=Evento.estado).execution_options(synchronize_session=False))
    event = db.query(Evento).filter_by(id_evento=event_id).populate_existing().with_for_update().first()
    if event is None:
        raise HTTPException(404, "Evento no encontrado.")
    return event


def roster(db, event):
    return db.query(ParticipanteEvento).filter_by(id_evento=event.id_evento).populate_existing().with_for_update().all()


def capacity(details):
    value = details.get("integrantes", 8)
    if type(value) is not int or not 2 <= value <= 8:
        raise HTTPException(422, "La capacidad del equipo debe estar entre 2 y 8 personas, incluyendo al creador.")
    return value


def validated_roles(details, members=()):
    roles = details.get("roles", [])
    if not isinstance(roles, list):
        raise HTTPException(422, "La lista de roles no es válida.")
    cleaned, names, ids = [], set(), set()
    for index, role in enumerate(roles):
        if not isinstance(role, dict) or not isinstance(role.get("nombre"), str):
            raise HTTPException(422, "Cada rol debe tener un nombre válido.")
        name = " ".join(role["nombre"].split())
        key, identifier = role_key(name), str(role.get("id", index))
        slots = role.get("vacantes", 1)
        if not name or len(name) > 50 or key in names or identifier in ids:
            raise HTTPException(422, "Usa nombres e identificadores de rol únicos; el nombre admite hasta 50 caracteres.")
        if type(slots) is not int or not 1 <= slots <= 8:
            raise HTTPException(422, "Las vacantes de cada rol deben estar entre 1 y 8.")
        names.add(key)
        ids.add(identifier)
        cleaned.append({k: v for k, v in {**role, "nombre": name, "id": identifier, "vacantes": slots}.items()
                        if k not in {"cubiertoPor", "ocupados", "integrantesIds"}})
    for member in members:
        matching = next((r for r in cleaned if role_key(r["nombre"]) == role_key(member.rol)), None)
        if not matching:
            raise HTTPException(409, "No puedes quitar o renombrar un rol que tiene un integrante asignado.")
        occupied = sum(role_key(m.rol) == role_key(member.rol) for m in members)
        if occupied > matching["vacantes"]:
            raise HTTPException(409, "No puedes reducir las vacantes por debajo de los integrantes asignados.")
    return cleaned


def event_roles(event):
    details = event.detalles_especificos or {}
    if "roles" not in details:
        details = {**details, "roles": (event.requisitos_ia or {}).get("roles", [])}
    return validated_roles(details)


def available_role(db, event, user_id, requested):
    if event.estado != "Abierto":
        raise HTTPException(409, "El evento ya no acepta integrantes.")
    if user_id == event.creador_id:
        raise HTTPException(409, "La persona creadora ya forma parte del equipo.")
    members = roster(db, event)
    member_ids = {m.id_usuario for m in members} | {event.creador_id}
    if user_id in member_ids:
        raise HTTPException(409, "Esta persona ya forma parte del equipo.")
    if len(member_ids) >= capacity(event.detalles_especificos or {}):
        raise HTTPException(409, "El equipo ya alcanzó su capacidad.")
    users = db.query(Usuario).filter(Usuario.id_usuario.in_([user_id, event.creador_id])).order_by(
        Usuario.id_usuario).populate_existing().with_for_update().all()
    user = next((u for u in users if u.id_usuario == user_id), None)
    creator = next((u for u in users if u.id_usuario == event.creador_id), None)
    profile = db.query(PerfilUsuario).filter_by(usuario_id=user_id).populate_existing().with_for_update().first()
    if not user or user.estado_cuenta != "Activa":
        raise HTTPException(409, "La cuenta del integrante ya no está activa.")
    if not creator or creator.estado_cuenta != "Activa":
        raise HTTPException(409, "La cuenta creadora ya no está activa.")
    if profile and (profile.datos_crudos or {}).get("pausado"):
        raise HTTPException(409, "El perfil del integrante está pausado.")
    roles = event_roles(event)
    if not roles and role_key(requested) in {"", "participante"}:
        return "Participante"  # Compatibility with existing events without role definitions.
    role = next((r for r in roles if str(r["id"]) == str(requested)
                 or role_key(r["nombre"]) == role_key(requested)), None)
    if not role:
        raise HTTPException(409, "El rol seleccionado ya no existe. Revisa el proyecto.")
    occupied = sum(role_key(m.rol) == role_key(role["nombre"]) for m in members)
    if occupied >= role["vacantes"]:
        raise HTTPException(409, "Ese rol ya está cubierto.")
    return role["nombre"]


def reject_pending_pair(db, event, user_id):
    pending = db.query(SolicitudEquipo).filter(
        SolicitudEquipo.id_evento == event.id_evento,
        SolicitudEquipo.estado.ilike("pendiente"),
        or_(and_(SolicitudEquipo.id_remitente == event.creador_id, SolicitudEquipo.id_destinatario == user_id),
            and_(SolicitudEquipo.id_remitente == user_id, SolicitudEquipo.id_destinatario == event.creador_id)),
    ).with_for_update().first()
    if pending:
        raise HTTPException(409, "Ya existe una invitación o solicitud pendiente entre esta persona y el evento.")
