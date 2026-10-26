"""Pure duplicate, action-state and snapshot-freshness checks.

The hashes are internal equality tokens, not public identifiers or a substitute
for authorized, transactional checks immediately before an invitation/request.
"""

import hashlib
import json
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.services.ai.matching.normalization import normalize_term
from app.services.ai.matching.policy import RankingPolicy
from app.services.ai.matching.schemas import CandidateInput, EventInput, Evidence

from .contracts import (CandidateRecommendation, OrganizerRecommendationContext,
                        ProjectRecommendation, UserRecommendationContext)


Recommendation = CandidateRecommendation | ProjectRecommendation
Context = OrganizerRecommendationContext | UserRecommendationContext
ActionState = Literal["member", "pending", "pending_invitation",
                      "pending_application", "pending_both", "available", "unknown"]
_COMPONENTS = ("profile", "event", "team", "access", "actions",
               "profile_embedding", "event_embedding", "policy")
_REVISION_COMPONENTS = {
    "profile": "profile", "event": "event", "team": "team", "access": "access",
    "actions": "actions", "profile_embedding": "profile_embedding",
    "event_embedding": "event_embedding",
    "profile_embedding_source": "profile_embedding",
    "event_embedding_source": "event_embedding",
}
_REVISION = re.compile(r"[A-Za-z0-9_.:-]{1,128}\Z")


class SourceVersions(BaseModel):
    """Opaque revisions from an authorized adapter; None means unavailable.

    An embedding source revision must identify the source content it represents.
    `embedding_source_version` in matching instead identifies pipeline compatibility.
    A known absence of an embedding still needs an explicit revision token.
    """

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    profile: str | None = None
    event: str | None = None
    team: str | None = None
    access: str | None = None
    actions: str | None = None
    profile_embedding: str | None = None
    event_embedding: str | None = None
    profile_embedding_source: str | None = None
    event_embedding_source: str | None = None

    @field_validator("profile", "event", "team", "access", "actions",
                     "profile_embedding", "event_embedding",
                     "profile_embedding_source", "event_embedding_source")
    @classmethod
    def opaque_revision(cls, value: str | None) -> str | None:
        if value is not None and not _REVISION.fullmatch(value):
            raise ValueError("La revisión debe ser un identificador opaco.")
        return value


class ActionRecord(BaseModel):
    """Prepared projection of SolicitudEquipo; no ORM or message text."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    event_id: int = Field(gt=0)
    sender_id: int = Field(gt=0)
    recipient_id: int = Field(gt=0)
    state: str

    @field_validator("state")
    @classmethod
    def normalized_state(cls, value: str) -> str:
        known = {
            "pendiente": "pending", "pending": "pending",
            "aceptada": "accepted", "aceptado": "accepted", "accepted": "accepted",
            "rechazada": "rejected", "rechazado": "rejected", "rejected": "rejected",
        }
        return known.get(normalize_term(value), "unknown")


@dataclass(frozen=True, slots=True)
class SnapshotFingerprint:
    audience: Literal["organizer", "user"]
    pair_digest: str
    profile: str | None
    event: str | None
    team: str | None
    access: str | None
    actions: str | None
    profile_embedding: str | None
    event_embedding: str | None
    policy: str
    revision_digests: tuple[tuple[str, str | None], ...] = ()
    intrinsically_stale: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class FreshnessAssessment:
    status: Literal["current", "stale", "unknown"]
    changed: tuple[str, ...] = ()
    unknown: tuple[str, ...] = ()


def _digest(value: object) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"),
                         ensure_ascii=False, allow_nan=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _versioned(revision: str | None, value: object) -> str | None:
    return _digest({"revision": revision, "content": value}) if revision is not None else None


def _evidence(items: list[Evidence] | None) -> list[dict] | None:
    if items is None:
        return None
    values = [{"kind": item.kind, "value": item.value, "source": item.source,
               "polarity": item.polarity, "confirmed": item.confirmed} for item in items]
    return sorted(values, key=lambda value: json.dumps(value, sort_keys=True, ensure_ascii=False))


def _pair(recommendation: Recommendation, user_id: int | None) -> tuple[int, int, str]:
    if isinstance(recommendation, CandidateRecommendation):
        return recommendation.event_id, recommendation.candidate_id, "organizer"
    if isinstance(recommendation, ProjectRecommendation):
        if type(user_id) is not int or user_id <= 0:
            raise ValueError("La recomendación de proyecto requiere ID de usuario validado.")
        return recommendation.event_id, user_id, "user"
    raise TypeError("Se requiere una recomendación validada.")


def same_action_pair(left: Recommendation, right: Recommendation, *,
                     left_user_id: int | None = None, right_user_id: int | None = None) -> bool:
    """Deduplicate actions by event/person, regardless of audience or policy."""
    return _pair(left, left_user_id)[:2] == _pair(right, right_user_id)[:2]


def classify_pair_records(event: EventInput, user_id: int,
                          actions: Sequence[ActionRecord] | None) -> ActionState:
    """Interpret prepared ORM-like records without treating accepted as membership.

    None means the action query was unavailable; [] means confirmed empty.
    An accepted request without a participant record is inconsistent, so unknown.
    """
    if not isinstance(event, EventInput) or type(user_id) is not int or user_id <= 0:
        raise TypeError("Se requieren evento e ID válidos.")
    if actions is not None and (not isinstance(actions, Sequence)
            or any(not isinstance(item, ActionRecord) for item in actions)):
        raise TypeError("Se requieren solicitudes preparadas válidas.")
    if event.participants is not None and any(
        person.user_id == user_id and person.confirmed for person in event.participants
    ):
        return "member"
    if actions is None:
        return "unknown"
    invitation = application = uncertain = False
    for action in actions:
        if action.event_id != event.event_id:
            continue
        if action.sender_id == event.creator_id and action.recipient_id == user_id:
            direction = "invitation"
        elif action.sender_id == user_id and action.recipient_id == event.creator_id:
            direction = "application"
        else:
            continue
        if action.state == "pending":
            invitation |= direction == "invitation"
            application |= direction == "application"
        elif action.state in {"accepted", "unknown"}:
            uncertain = True
    if invitation and application:
        return "pending_both"
    if invitation:
        return "pending_invitation"
    if application:
        return "pending_application"
    if uncertain or event.participants is None or any(
        person.user_id == user_id and not person.confirmed for person in event.participants
    ):
        return "unknown"
    return "available"


def context_action_state(recommendation: Recommendation, context: Context,
                         event: EventInput) -> ActionState:
    """Read checked member/action sets from the appropriate 5.1/5.2 context."""
    if not isinstance(event, EventInput) or recommendation.event_id != event.event_id:
        raise ValueError("El evento no coincide con la recomendación.")
    if isinstance(recommendation, CandidateRecommendation):
        if not isinstance(context, OrganizerRecommendationContext):
            raise TypeError("Se requiere contexto del organizador.")
        user_id = recommendation.candidate_id
        if user_id in context.confirmed_member_ids or any(
            person.user_id == user_id and person.confirmed
            for person in (event.participants or ())
        ):
            return "member"
        return "pending" if user_id in context.pending_candidate_ids else "available"
    if not isinstance(recommendation, ProjectRecommendation) or not isinstance(context, UserRecommendationContext):
        raise TypeError("Se requiere recomendación y contexto del usuario.")
    if recommendation.event_id in context.confirmed_member_event_ids or any(
        person.user_id == context.authenticated_user_id and person.confirmed
        for person in (event.participants or ())
    ):
        return "member"
    invitation = recommendation.event_id in context.pending_invitation_event_ids
    application = recommendation.event_id in context.pending_application_event_ids
    if invitation and application:
        return "pending_both"
    if invitation:
        return "pending_invitation"
    if application:
        return "pending_application"
    return "available"


def _profile_content(candidate: CandidateInput) -> dict | None:
    if candidate.declared_skills is None or candidate.profile is None:
        return None
    return {
        "user_id": candidate.user_id, "visibility": candidate.visibility,
        "account_state": candidate.account_state,
        "declared_skills": _evidence(candidate.declared_skills),
        "role_preferences": _evidence(candidate.role_preferences),
        "availability": _evidence(candidate.availability),
        "interests": candidate.profile.intereses,
    }


def _event_content(event: EventInput) -> dict | None:
    if event.requirements is None or event.confirmed_requirements is None:
        return None
    return {
        "event_id": event.event_id, "creator_id": event.creator_id,
        "state": event.state, "requirements": event.requirements.model_dump(mode="json"),
        "confirmed_requirements": _evidence(event.confirmed_requirements),
        "outstanding_roles": _evidence(event.outstanding_roles),
        "explicit_constraints": _evidence(event.explicit_constraints),
    }


def _team_content(event: EventInput,
                  team_members: Mapping[int, CandidateInput] | None) -> dict | None:
    if event.participants is None or any(not person.confirmed or person.role is None
                                         for person in event.participants):
        return None
    members = []
    for person in sorted(event.participants, key=lambda participant: participant.user_id):
        member = team_members.get(person.user_id) if team_members is not None else None
        if member is None or member.user_id != person.user_id or member.declared_skills is None:
            return None
        members.append({"user_id": person.user_id, "role": person.role,
                        "visibility": member.visibility,
                        "declared_skills": _evidence(member.declared_skills)})
    return {"members": members}


def _pair_records(actions: Sequence[ActionRecord] | None, event_id: int,
                  creator_id: int, user_id: int) -> list[dict] | None:
    if actions is None:
        return None
    relevant = [
        {"sender_id": action.sender_id, "recipient_id": action.recipient_id,
         "state": action.state}
        for action in actions if action.event_id == event_id and (
            (action.sender_id == creator_id and action.recipient_id == user_id)
            or (action.sender_id == user_id and action.recipient_id == creator_id)
        )
    ]
    return sorted(relevant, key=lambda value: json.dumps(value, sort_keys=True))


def build_snapshot_fingerprint(
    recommendation: Recommendation,
    candidate: CandidateInput,
    event: EventInput,
    context: Context,
    versions: SourceVersions,
    policy: RankingPolicy,
    *,
    team_members: Mapping[int, CandidateInput] | None = None,
    action_records: Sequence[ActionRecord] | None = None,
) -> SnapshotFingerprint:
    """Hash only matching-relevant facts plus explicit source revisions.

    A missing source revision or incomplete relevant input leaves its component
    unknown. A source revision mismatch marks the corresponding embedding stale.
    No raw profile/event content, source_ref or vector is returned.
    """
    if not isinstance(candidate, CandidateInput) or not isinstance(event, EventInput):
        raise TypeError("Se requieren contratos de perfil y evento.")
    if not isinstance(versions, SourceVersions) or not isinstance(policy, RankingPolicy):
        raise TypeError("Se requieren revisiones y política validadas.")
    event_id, user_id, audience = _pair(
        recommendation, candidate.user_id if isinstance(recommendation, ProjectRecommendation) else None
    )
    if event_id != event.event_id or user_id != candidate.user_id:
        raise ValueError("El par no coincide con la recomendación.")
    if audience == "organizer":
        if (not isinstance(context, OrganizerRecommendationContext)
                or context.authenticated_organizer_id != event.creator_id
                or context.authorized_event_id != event_id):
            raise PermissionError("Contexto no autorizado.")
        access = {"discoverable": user_id in context.discoverable_candidate_ids}
        actions = {"member": user_id in context.confirmed_member_ids,
                   "pending": user_id in context.pending_candidate_ids}
    else:
        if not isinstance(context, UserRecommendationContext) or context.authenticated_user_id != user_id:
            raise PermissionError("Contexto no autorizado.")
        access = {"discoverable": event_id in context.discoverable_event_ids,
                  "consent": context.discovery_consent}
        actions = {"member": event_id in context.confirmed_member_event_ids,
                   "pending_invitation": event_id in context.pending_invitation_event_ids,
                   "pending_application": event_id in context.pending_application_event_ids}
    if team_members is not None and (not isinstance(team_members, Mapping) or any(
        type(key) is not int or key <= 0 or not isinstance(value, CandidateInput)
        for key, value in team_members.items()
    )):
        raise TypeError("team_members debe mapear IDs a CandidateInput.")
    if action_records is not None and (not isinstance(action_records, Sequence) or any(
        not isinstance(item, ActionRecord) for item in action_records
    )):
        raise TypeError("action_records debe contener solicitudes preparadas.")

    profile = _profile_content(candidate)
    event_data = _event_content(event)
    team = _team_content(event, team_members)
    stale = []
    if (versions.profile is not None and versions.profile_embedding_source is not None
            and versions.profile != versions.profile_embedding_source):
        stale.append("profile_embedding")
    if (versions.event is not None and versions.event_embedding_source is not None
            and versions.event != versions.event_embedding_source):
        stale.append("event_embedding")
    if recommendation.policy_version != policy.version:
        stale.append("policy")

    profile_embedding = None
    if all(value is not None for value in (versions.profile, versions.profile_embedding,
                                            versions.profile_embedding_source)):
        profile_embedding = _versioned(versions.profile_embedding, {
            "source_revision": versions.profile_embedding_source,
            "model": candidate.embedding_model, "pipeline": candidate.embedding_source_version,
            "vector": candidate.profile_embedding,
        })
    event_embedding = None
    if all(value is not None for value in (versions.event, versions.event_embedding,
                                            versions.event_embedding_source)):
        event_embedding = _versioned(versions.event_embedding, {
            "source_revision": versions.event_embedding_source,
            "model": event.embedding_model, "pipeline": event.embedding_source_version,
            "vector": event.event_embedding,
        })
    eligibility = policy.eligibility
    policy_digest = _digest({
        "version": policy.version, "weights": policy.weights,
        "min_available_signals": policy.min_available_signals,
        "min_known_requirements": policy.min_known_requirements,
        "strict_constraints": sorted(eligibility.strict_constraint_terms),
        "exclude_missing_required": eligibility.exclude_confirmed_missing_required_skills,
        "equivalence_version": eligibility.catalog.version,
        "equivalences": eligibility.catalog.aliases,
    })
    return SnapshotFingerprint(
        audience=audience,
        pair_digest=_digest({"audience": audience, "event_id": event_id, "user_id": user_id}),
        profile=_versioned(versions.profile, profile) if profile is not None else None,
        event=_versioned(versions.event, event_data) if event_data is not None else None,
        team=_versioned(versions.team, team) if team is not None else None,
        access=_versioned(versions.access, access),
        actions=_versioned(versions.actions, {
            "context": actions,
            "records": _pair_records(action_records, event_id, event.creator_id, user_id),
        }),
        profile_embedding=profile_embedding, event_embedding=event_embedding,
        policy=policy_digest,
        revision_digests=tuple((name, _digest({"revision": getattr(versions, name)})
                                if getattr(versions, name) is not None else None)
                               for name in _REVISION_COMPONENTS),
        intrinsically_stale=tuple(stale),
    )


def assess_freshness(previous: SnapshotFingerprint,
                     current: SnapshotFingerprint) -> FreshnessAssessment:
    """Known changes win over unknown components; no time-based assumption."""
    if not isinstance(previous, SnapshotFingerprint) or not isinstance(current, SnapshotFingerprint):
        raise TypeError("Se requieren dos huellas validadas.")
    if previous.audience != current.audience or previous.pair_digest != current.pair_digest:
        raise ValueError("Las huellas pertenecen a recomendaciones distintas.")
    changed = [name for name in _COMPONENTS if (getattr(previous, name) is not None
               and getattr(current, name) is not None
               and getattr(previous, name) != getattr(current, name))]
    old_revisions = dict(previous.revision_digests)
    new_revisions = dict(current.revision_digests)
    for revision, component in _REVISION_COMPONENTS.items():
        if (old_revisions.get(revision) is not None and new_revisions.get(revision) is not None
                and old_revisions[revision] != new_revisions[revision]
                and component not in changed):
            changed.append(component)
    changed.extend(name for name in (*previous.intrinsically_stale, *current.intrinsically_stale)
                   if name not in changed)
    unknown = [name for name in _COMPONENTS if (getattr(previous, name) is None
               or getattr(current, name) is None)]
    return FreshnessAssessment("stale" if changed else "unknown" if unknown else "current",
                               tuple(changed), tuple(unknown))


def is_repeated_recommendation(previous: SnapshotFingerprint,
                               current: SnapshotFingerprint) -> bool | None:
    """True only for the same audience, pair, policy and complete snapshot."""
    if not isinstance(previous, SnapshotFingerprint) or not isinstance(current, SnapshotFingerprint):
        raise TypeError("Se requieren dos huellas validadas.")
    if previous.audience != current.audience or previous.pair_digest != current.pair_digest:
        return False
    status = assess_freshness(previous, current).status
    return True if status == "current" else False if status == "stale" else None
