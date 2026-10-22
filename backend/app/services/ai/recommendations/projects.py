"""Pure project recommendations for one authenticated user."""

from collections.abc import Mapping, Sequence

from app.services.ai.matching.policy import RankingPolicy
from app.services.ai.matching.ranking import rank_candidates
from app.services.ai.matching.schemas import CandidateInput, EventInput, MatchRequest, MatchResult

from .contracts import ProjectRecommendation, UserRecommendationContext
from .evidence import evidence_group


def _project_order(result: MatchResult, policy: RankingPolicy) -> tuple[int, int, int, int, int]:
    """Compare confirmed facts, never separately reweighted event scores."""
    assessments = result.requirements
    core_fit = any(item.status == "met" and item.kind in {"required_skill", "open_role"}
                   for item in assessments)
    preferred_fit = any(item.status == "met" and item.kind == "preferred_skill"
                        for item in assessments)
    return (
        0 if result.eligibility == "eligible" else 1,
        0 if evidence_group(result, policy) == "sufficient_evidence" else 1,
        0 if core_fit else 1,
        0 if preferred_fit else 1,
        result.event_id,
    )


def recommend_projects(
    user: CandidateInput,
    events: Sequence[EventInput],
    context: UserRecommendationContext,
    *,
    policy: RankingPolicy | None = None,
    team_members_by_event: Mapping[int, Mapping[int, CandidateInput]] | None = None,
    top_n: int | None = None,
) -> list[ProjectRecommendation]:
    """Evaluate each visible event with matching, then order conservative groups.

    Context must be prepared from server authentication, consent, event access,
    membership and live action states. A recommendation cannot authorize a
    future application; the adapter must recheck state before writing it.
    """
    if not isinstance(user, CandidateInput) or not isinstance(context, UserRecommendationContext):
        raise TypeError("Se requieren usuario y contexto validados.")
    if (context.authenticated_user_id != user.user_id or not context.discovery_consent
            or user.visibility != "visible"):
        raise PermissionError("No se autorizó la consulta de recomendaciones.")
    policy = policy if policy is not None else RankingPolicy()
    if not isinstance(policy, RankingPolicy):
        raise TypeError("Se requiere RankingPolicy.")
    if top_n is not None and (type(top_n) is not int or top_n <= 0):
        raise ValueError("top_n debe ser un entero positivo.")
    if not isinstance(events, Sequence) or any(not isinstance(event, EventInput) for event in events):
        raise TypeError("Se requieren eventos validados.")
    ids = [event.event_id for event in events]
    if len(ids) != len(set(ids)):
        raise ValueError("Los eventos deben tener identificadores únicos.")
    if team_members_by_event is not None and (not isinstance(team_members_by_event, Mapping)
            or any(type(key) is not int or key <= 0 or not isinstance(value, Mapping)
                   for key, value in team_members_by_event.items())):
        raise TypeError("team_members_by_event debe mapear eventos a integrantes.")

    excluded_actions = (context.pending_invitation_event_ids
                        | context.pending_application_event_ids)
    evaluated: list[MatchResult] = []
    for event in events:
        if (event.event_id not in context.discoverable_event_ids
                or event.state == "closed"
                or event.creator_id == user.user_id
                or event.event_id in context.confirmed_member_event_ids
                or event.event_id in excluded_actions
                or any(person.user_id == user.user_id and person.confirmed
                       for person in (event.participants or ()))):
            continue
        request = MatchRequest(event=event, candidates=[user], policy_version=policy.version,
                               top_n=1)
        team_members = (team_members_by_event.get(event.event_id)
                        if team_members_by_event is not None else None)
        evaluated.extend(rank_candidates(request, policy, team_members=team_members))

    evaluated.sort(key=lambda result: _project_order(result, policy))
    if top_n is not None:
        evaluated = evaluated[:top_n]
    return [
        ProjectRecommendation(
            event_id=result.event_id,
            eligibility=result.eligibility,
            evidence_group=evidence_group(result, policy),
            evidence_coverage=result.evidence_coverage,
            explanation=result.explanation,
            policy_version=result.policy_version,
        )
        for result in evaluated
    ]
