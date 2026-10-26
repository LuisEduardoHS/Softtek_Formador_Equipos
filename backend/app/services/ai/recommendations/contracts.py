"""Trusted snapshot context and minimal public projection for organizers."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.services.ai.matching.schemas import EvidenceCoverage, PublicExplanation


def _valid_ids(values: frozenset[int]) -> bool:
    return all(type(value) is int and value > 0 for value in values)


class OrganizerRecommendationContext(BaseModel):
    """Facts checked by a future authenticated adapter, never client input.

    An empty set means the adapter checked and found none. Neither the owner
    grant nor discovery consent can be inferred from CandidateInput alone.
    """

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    authenticated_organizer_id: int = Field(gt=0)
    authorized_event_id: int = Field(gt=0)
    discoverable_candidate_ids: frozenset[int]
    confirmed_member_ids: frozenset[int]
    pending_candidate_ids: frozenset[int]

    def model_post_init(self, __context: object) -> None:
        if not _valid_ids(self.discoverable_candidate_ids):
            raise ValueError("Los IDs de candidatos visibles deben ser positivos.")
        if not _valid_ids(self.confirmed_member_ids):
            raise ValueError("Los IDs de integrantes deben ser positivos.")
        if not _valid_ids(self.pending_candidate_ids):
            raise ValueError("Los IDs de invitaciones pendientes deben ser positivos.")


class CandidateRecommendation(BaseModel):
    """Organizer-facing result; intentionally omits score and private inputs."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    event_id: int = Field(gt=0)
    candidate_id: int = Field(gt=0)
    eligibility: Literal["eligible", "needs_review"]
    evidence_group: Literal["sufficient_evidence", "insufficient_evidence"]
    evidence_coverage: EvidenceCoverage
    explanation: PublicExplanation
    policy_version: str = Field(min_length=1)


class UserRecommendationContext(BaseModel):
    """Server-verified access, consent and action snapshot for one user.

    Every set is required: an empty set means checked and empty, never unknown.
    The adapter must derive it from authentication and real event/action records.
    """

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    authenticated_user_id: int = Field(gt=0)
    discovery_consent: bool
    discoverable_event_ids: frozenset[int]
    confirmed_member_event_ids: frozenset[int]
    pending_invitation_event_ids: frozenset[int]
    pending_application_event_ids: frozenset[int]

    def model_post_init(self, __context: object) -> None:
        for values in (self.discoverable_event_ids, self.confirmed_member_event_ids,
                       self.pending_invitation_event_ids, self.pending_application_event_ids):
            if not _valid_ids(values):
                raise ValueError("Los IDs de eventos deben ser positivos.")


class ProjectRecommendation(BaseModel):
    """User-facing project result without profile, vectors or internal score."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    event_id: int = Field(gt=0)
    eligibility: Literal["eligible", "needs_review"]
    evidence_group: Literal["sufficient_evidence", "insufficient_evidence"]
    evidence_coverage: EvidenceCoverage
    explanation: PublicExplanation
    policy_version: str = Field(min_length=1)
