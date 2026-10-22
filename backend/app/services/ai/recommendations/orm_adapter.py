"""Read-only, authorized ORM snapshot for the existing pure recommendation engine."""

import math
import re
from collections import defaultdict

from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.models.evento import Evento
from app.models.participante import ParticipanteEvento
from app.models.solicitud import SolicitudEquipo
from app.models.usuario import PerfilUsuario, Usuario
from app.services.ai.matching.normalization import apply_equivalence
from app.services.ai.matching.schemas import CandidateInput, EventInput, Evidence, Location, Participant
from app.services.ai.schemas import StructuredEventRequirements, StructuredProfile

from .candidates import recommend_candidates
from .contracts import OrganizerRecommendationContext, UserRecommendationContext
from .projects import recommend_projects


def _json_object(value) -> dict:
    return value if isinstance(value, dict) else {}


def _safe_fact(value) -> str | None:
    if not isinstance(value, str):
        return None
    text = " ".join(value.split())
    if not text or len(text) > 150 or re.search(r"\b[\w.+-]+@[\w.-]+\.[a-z]{2,}\b", text, re.I):
        return None
    if re.search(r"\b(?:\+?\d[\d\s().-]{7,}\d)\b", text):
        return None
    return text


def _safe_vector(value, model, pipeline, source, revision):
    if (not source or not revision or source != revision or not isinstance(value, list) or not value
            or not isinstance(model, str) or not model
            or not isinstance(pipeline, str) or not pipeline):
        return None, None, None
    if any(type(item) not in (int, float) or not math.isfinite(item) for item in value):
        return None, None, None
    if model in {"nomic-embed-text", "nomic-embed-text:latest"} and len(value) != 768:
        return None, None, None
    return [float(item) for item in value], model, pipeline


def _evidence(source: str, kind: str, values: list[str]) -> list[Evidence]:
    return [Evidence(source=source, kind=kind, value=term, polarity="affirms", confirmed=True)
            for item in values if (term := _safe_fact(item))]


def candidate_from_orm(user: Usuario, profile: PerfilUsuario | None,
                       *, self_access: bool = False) -> CandidateInput:
    """Confirmed declarations only; unknown stays None and hidden stays hidden."""
    raw = _json_object(profile.datos_crudos) if profile else {}
    visibility = _json_object(raw.get("visibilidad"))
    consent = raw.get("consentimiento_recomendaciones") is True
    active = user.estado_cuenta == "Activa"
    visible = active and consent and raw.get("pausado") is False
    if not visible and not self_access:
        return CandidateInput(user_id=user.id_usuario, visibility="hidden",
                              account_state="active" if active else "inactive")
    confirmed = bool(profile and profile.perfil_confirmado_at
                     and profile.perfil_estado_ia in {"listo", "pendiente_embedding"})
    structured = None
    if confirmed:
        try:
            structured = StructuredProfile.model_validate(profile.perfil_estructurado_ia)
        except (ValidationError, TypeError, ValueError):
            confirmed = False
    if confirmed:
        skills = _evidence("user_declared", "skill", structured.habilidades) if (
            self_access or visibility.get("fortalezas") is True) else None
        raw_availability = raw.get("disponibilidad")
        availability = _evidence("user_declared", "availability", raw_availability) if (
            (self_access or visibility.get("disponibilidad") is True)
            and isinstance(raw_availability, list)) else None
        public_profile = structured.model_copy(update={
            "habilidades": [item.value for item in skills] if skills is not None else [],
            "intereses": [v for x in structured.intereses if (v := _safe_fact(x))]
            if (self_access or visibility.get("intereses") is True) else [],
            "areas_mejora": [],
            "experiencia": [],
            "resumen_publico": "",
        })
    else:
        skills = availability = public_profile = None
    vector, model, pipeline = (None, None, None)
    if confirmed and profile.perfil_estado_ia == "listo":
        vector, model, pipeline = _safe_vector(
            profile.embedding_perfil, profile.perfil_embedding_model,
            profile.perfil_embedding_pipeline, profile.perfil_embedding_fuente_revision,
            profile.perfil_fuente_revision,
        )
    location = None
    if user.estado_geografico or user.municipio:
        location = Location(estado_geografico=user.estado_geografico or None,
                            municipio=user.municipio or None)
    return CandidateInput(
        user_id=user.id_usuario, profile=public_profile, declared_skills=skills,
        role_preferences=None, availability=availability, location=location,
        visibility="visible" if visible else "hidden",
        account_state="active" if active else "inactive",
        profile_embedding=vector, embedding_model=model,
        embedding_source_version=pipeline,
    )


def event_from_orm(event: Evento, members: list[ParticipanteEvento]) -> EventInput:
    """Never promote legacy requisitos_ia without a creator confirmation stamp."""
    requirements = None
    if event.requisitos_confirmados_at:
        try:
            parsed = StructuredEventRequirements.model_validate(event.requisitos_ia)
            requirements = parsed.model_copy(update={
                "habilidades_obligatorias": [v for x in parsed.habilidades_obligatorias if (v := _safe_fact(x))],
                "habilidades_deseables": [v for x in parsed.habilidades_deseables if (v := _safe_fact(x))],
                "roles_buscados": [v for x in parsed.roles_buscados if (v := _safe_fact(x))],
                "intereses_relacionados": [v for x in parsed.intereses_relacionados if (v := _safe_fact(x))],
                "restricciones_explicitas": [v for x in parsed.restricciones_explicitas if (v := _safe_fact(x))],
            })
        except (ValidationError, TypeError, ValueError):
            pass
    facts = None
    constraints = None
    outstanding = None
    if requirements is not None:
        facts = (_evidence("organizer_confirmed", "skill", requirements.habilidades_obligatorias)
                 + _evidence("organizer_confirmed", "skill", requirements.habilidades_deseables)
                 + _evidence("organizer_confirmed", "role", requirements.roles_buscados))
        constraints = _evidence("organizer_confirmed", "constraint", requirements.restricciones_explicitas)
        occupied = {apply_equivalence(member.rol) for member in members if _safe_fact(member.rol)}
        if all(member.rol for member in members):
            outstanding = _evidence("organizer_confirmed", "role", [
                role for role in requirements.roles_buscados
                if apply_equivalence(role) not in occupied
            ])
    participants = [Participant(user_id=event.creador_id, role=None, confirmed=True)]
    participants.extend(Participant(user_id=m.id_usuario, role=_safe_fact(m.rol), confirmed=True)
                        for m in members if m.id_usuario != event.creador_id)
    vector, model, pipeline = (None, None, None)
    if requirements is not None and event.estado_ia == "listo":
        vector, model, pipeline = _safe_vector(
            event.embedding_requisitos, event.embedding_model, event.embedding_pipeline,
            event.embedding_fuente_revision, event.requisitos_fuente_revision,
        )
    return EventInput(
        event_id=event.id_evento, creator_id=event.creador_id,
        state="open" if event.estado == "Abierto" else "closed",
        requirements=requirements, confirmed_requirements=facts,
        participants=participants, outstanding_roles=outstanding,
        explicit_constraints=constraints, event_embedding=vector,
        embedding_model=model, embedding_source_version=pipeline,
    )


def _all_profiles(db: Session):
    return {user.id_usuario: (user, profile) for user, profile in db.query(
        Usuario, PerfilUsuario).outerjoin(
            PerfilUsuario, PerfilUsuario.usuario_id == Usuario.id_usuario).all()}


def _rosters(db: Session, event_ids: list[int]):
    result = defaultdict(list)
    if event_ids:
        for row in db.query(ParticipanteEvento).filter(
                ParticipanteEvento.id_evento.in_(event_ids)).all():
            result[row.id_evento].append(row)
    return result


def _pending(db: Session, event_ids: list[int]):
    if not event_ids:
        return []
    return db.query(SolicitudEquipo).filter(
        SolicitudEquipo.id_evento.in_(event_ids),
        SolicitudEquipo.estado.ilike("pendiente"),
    ).all()


def candidate_recommendations(db: Session, event: Evento, actor: Usuario,
                              *, top_n: int = 10):
    if event.creador_id != actor.id_usuario:
        raise PermissionError("Solo el organizador puede consultar candidatos.")
    profiles = _all_profiles(db)
    members = _rosters(db, [event.id_evento])[event.id_evento]
    member_ids = {row.id_usuario for row in members}
    pending_ids = {row.id_destinatario if row.id_remitente == actor.id_usuario
                   else row.id_remitente for row in _pending(db, [event.id_evento])}
    candidates = [candidate_from_orm(user, profile) for user, profile in profiles.values()
                  if user.id_usuario not in member_ids | pending_ids | {actor.id_usuario}]
    discoverable = frozenset(candidate.user_id for candidate in candidates
                             if candidate.visibility == "visible")
    team = {uid: candidate_from_orm(*profiles[uid]) for uid in member_ids | {actor.id_usuario}
            if uid in profiles}
    context = OrganizerRecommendationContext(
        authenticated_organizer_id=actor.id_usuario, authorized_event_id=event.id_evento,
        discoverable_candidate_ids=discoverable,
        confirmed_member_ids=frozenset(member_ids), pending_candidate_ids=frozenset(pending_ids),
    )
    return recommend_candidates(event_from_orm(event, members), candidates, context,
                                team_members=team, top_n=top_n)


def project_recommendations(db: Session, actor: Usuario, *, top_n: int = 10):
    profiles = _all_profiles(db)
    user = candidate_from_orm(actor, profiles.get(actor.id_usuario, (actor, None))[1],
                              self_access=True)
    if user.visibility != "visible":
        raise PermissionError("Activa el consentimiento de recomendaciones en tu perfil.")
    records = db.query(Evento).filter(Evento.estado == "Abierto").all()
    ids = [row.id_evento for row in records]
    rosters = _rosters(db, ids)
    pending = _pending(db, ids)
    member_ids = frozenset(row.id_evento for row in records
                           if any(member.id_usuario == actor.id_usuario
                                  for member in rosters[row.id_evento]))
    context = UserRecommendationContext(
        authenticated_user_id=actor.id_usuario, discovery_consent=True,
        discoverable_event_ids=frozenset(ids), confirmed_member_event_ids=member_ids,
        pending_invitation_event_ids=frozenset(row.id_evento for row in pending
                                               if row.id_destinatario == actor.id_usuario),
        pending_application_event_ids=frozenset(row.id_evento for row in pending
                                                if row.id_remitente == actor.id_usuario),
    )
    events = [event_from_orm(row, rosters[row.id_evento]) for row in records]
    team = {row.id_evento: {uid: candidate_from_orm(*profiles[uid])
                           for uid in {row.creador_id} | {m.id_usuario for m in rosters[row.id_evento]}
                           if uid in profiles} for row in records}
    return recommend_projects(user, events, context, team_members_by_event=team, top_n=top_n)
