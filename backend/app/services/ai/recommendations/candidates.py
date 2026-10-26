"""Organizer-only candidate recommendations with no I/O or model inference."""

from collections.abc import Mapping, Sequence

from app.services.ai.matching.policy import RankingPolicy
from app.services.ai.matching.ranking import rank_candidates
from app.services.ai.matching.schemas import CandidateInput, EventInput, MatchRequest

from .contracts import CandidateRecommendation, OrganizerRecommendationContext
from .evidence import evidence_group


def recommend_candidates(
    event: EventInput,
    candidates: Sequence[CandidateInput],
    context: OrganizerRecommendationContext,
    *,
    policy: RankingPolicy | None = None,
    team_members: Mapping[int, CandidateInput] | None = None,
    top_n: int | None = None,
) -> list[CandidateRecommendation]:
    """Rank a prepared snapshot for its verified organizer and return safe DTOs.

    The caller must derive context from server authentication, event ownership,
    consent/visibility and real pending requests. This function never fetches
    that state and its output does not authorize an invitation.
    """
    if not isinstance(event, EventInput) or not isinstance(context, OrganizerRecommendationContext):
        raise TypeError("Se requieren evento y contexto validados.")
    if (context.authenticated_organizer_id != event.creator_id
            or context.authorized_event_id != event.event_id):
        raise PermissionError("No se autorizó la consulta de recomendaciones.")
    policy = policy if policy is not None else RankingPolicy()
    if not isinstance(policy, RankingPolicy):
        raise TypeError("Se requiere RankingPolicy.")

    # Validate the full snapshot before filtering, including duplicate IDs and top_n.
    request = MatchRequest(
        event=event, candidates=list(candidates), policy_version=policy.version, top_n=top_n,
    )
    if event.state == "closed":
        return []

    confirmed_members = set(context.confirmed_member_ids) | {
        participant.user_id for participant in (event.participants or ())
        if participant.confirmed
    }
    allowed = [
        candidate for candidate in request.candidates
        if candidate.user_id in context.discoverable_candidate_ids
        and candidate.user_id not in context.pending_candidate_ids
        and candidate.user_id not in confirmed_members
        and candidate.user_id != event.creator_id
        and candidate.visibility == "visible"
    ]
    ranked = rank_candidates(
        MatchRequest(event=event, candidates=allowed,
                     policy_version=policy.version, top_n=top_n),
        policy, team_members=team_members,
    )
    return [
        CandidateRecommendation(
            event_id=result.event_id,
            candidate_id=result.candidate_id,
            eligibility=result.eligibility,
            evidence_group=evidence_group(result, policy),
            evidence_coverage=result.evidence_coverage,
            explanation=result.explanation,
            policy_version=result.policy_version,
        )
        for result in ranked
    ]
