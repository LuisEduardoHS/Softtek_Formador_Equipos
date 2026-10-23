"""Pure, reproducible ranking over validated matching contracts."""

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from .complementarity import assess_team_gaps, complementarity_score
from .eligibility import assess_eligibility
from .explanations import explain_match
from .normalization import EquivalenceCatalog, apply_equivalence
from .policy import RankingPolicy
from .schemas import CandidateInput, EvidenceCoverage, EventInput, MatchRequest, MatchResult, RequirementAssessment
from .similarity import InvalidEmbeddingError, cosine_similarity


@dataclass(frozen=True, slots=True)
class ScoreBreakdown:
    score: float | None
    components: dict[str, float | None]
    available_signals: int


def _bounded(value: float | None, name: str, *, lower: float = 0) -> float | None:
    if value is None:
        return None
    if (isinstance(value, bool) or not isinstance(value, (int, float))
            or not math.isfinite(value) or not lower <= value <= 1):
        raise ValueError(f"{name} debe ser finito y estar entre {lower} y 1.")
    return float(value)


def _confirmed_requirement(item: RequirementAssessment) -> bool:
    organizer = [evidence for evidence in item.evidence
                 if evidence.source == "organizer_confirmed" and evidence.kind == "skill"
                 and evidence.confirmed]
    return bool(organizer) and {evidence.polarity for evidence in organizer} == {"affirms"}


def _skill_coverage(assessments: Sequence[RequirementAssessment], kind: str) -> float | None:
    confirmed = [item for item in assessments if item.kind == kind
                 and _confirmed_requirement(item)]
    for item in confirmed:
        if item.status == "met" and not any(
            evidence.source == "user_declared" and evidence.confirmed
            and evidence.polarity == "affirms" and evidence.kind == "skill"
            for evidence in item.evidence
        ):
            raise ValueError("Un requisito acreditado necesita evidencia de habilidad confirmada.")
        if item.status == "unmet_confirmed" and not any(
            evidence.source == "user_declared" and evidence.confirmed
            and evidence.polarity == "denies" and evidence.kind == "skill"
            for evidence in item.evidence
        ):
            raise ValueError("Una negación requiere evidencia declarada confirmada.")
    if not confirmed or all(item.status == "unknown" for item in confirmed):
        return None
    return sum(item.status == "met" for item in confirmed) / len(confirmed)


def score_candidate(
    assessments: Sequence[RequirementAssessment],
    policy: RankingPolicy,
    *,
    complementarity: float | None = None,
    semantic_similarity: float | None = None,
    interests: float | None = None,
) -> ScoreBreakdown:
    """Reweight available signals; None is unknown and zero is observed lack of credit.

    Partial skill coverage uses the number of confirmed requirements as its
    denominator. Unknown items remain visible in evidence coverage and never
    generate positive credit. A wholly unknown component stays absent.
    """
    if not isinstance(policy, RankingPolicy):
        raise TypeError("Se requiere RankingPolicy.")
    if not isinstance(assessments, Sequence) or any(
        not isinstance(item, RequirementAssessment) for item in assessments
    ):
        raise TypeError("Se requieren evaluaciones de requisitos válidas.")
    catalog = policy.eligibility.catalog
    keys = [(item.kind, apply_equivalence(item.requirement, catalog)) for item in assessments]
    if len(keys) != len(set(keys)):
        raise ValueError("No se permiten requisitos duplicados en la puntuación.")
    complementarity = _bounded(complementarity, "Complementariedad")
    interests = _bounded(interests, "Intereses")
    semantic_similarity = _bounded(semantic_similarity, "Coseno", lower=-1)
    components = {
        "required_skills": _skill_coverage(assessments, "required_skill"),
        "complementarity": complementarity,
        "preferred_skills": _skill_coverage(assessments, "preferred_skill"),
        # Fixed linear mapping of a genuine cosine; this is not a probability.
        "semantic_similarity": ((semantic_similarity + 1) / 2
                                if semantic_similarity is not None else None),
        "interests": interests,
    }
    available = {name: value for name, value in components.items() if value is not None
                 and policy.weights[name] > 0}
    total_weight = sum(policy.weights[name] for name in available)
    score = (sum(policy.weights[name] * value for name, value in available.items()) / total_weight
             if total_weight else None)
    return ScoreBreakdown(score, components, len(available))


def _confirmed_role_terms(event: EventInput, catalog: EquivalenceCatalog) -> set[str]:
    if event.requirements is None:
        return set()
    facts = event.outstanding_roles if event.outstanding_roles is not None else event.confirmed_requirements
    result = set()
    for term in event.requirements.roles_buscados:
        key = apply_equivalence(term, catalog)
        matched = [item for item in (facts or ()) if item.kind == "role" and item.confirmed
                   and item.source == "organizer_confirmed"
                   and apply_equivalence(item.value, catalog) == key]
        if matched and {item.polarity for item in matched} == {"affirms"}:
            result.add(key)
    return result


def _interest_signal(event: EventInput, candidate: CandidateInput,
                     catalog: EquivalenceCatalog) -> float | None:
    if event.requirements is None:
        return None
    targets: set[str] = set()
    matches: set[str] = set()
    if candidate.profile is not None and candidate.profile.intereses:
        themes = {apply_equivalence(term, catalog)
                  for term in event.requirements.intereses_relacionados}
        interests = {apply_equivalence(term, catalog) for term in candidate.profile.intereses}
        targets.update(themes)
        matches.update(themes & interests)
    if candidate.role_preferences is not None:
        preferences = [item for item in candidate.role_preferences
                       if item.kind == "role_preference" and item.source == "user_declared"
                       and item.confirmed]
        if preferences:
            roles = _confirmed_role_terms(event, catalog)
            positive = {apply_equivalence(item.value, catalog) for item in preferences
                        if item.polarity == "affirms"}
            negative = {apply_equivalence(item.value, catalog) for item in preferences
                        if item.polarity == "denies"}
            targets.update(roles)
            matches.update(roles & (positive - negative))
    return len(matches) / len(targets) if targets else None


def _evidence_coverage(assessments: Sequence[RequirementAssessment]) -> EvidenceCoverage:
    return EvidenceCoverage(
        known=sum(item.status in {"met", "unmet_confirmed"} for item in assessments),
        unknown=sum(item.status == "unknown" for item in assessments),
        not_applicable=sum(item.status == "not_applicable" for item in assessments),
    )


def _sort_key(result: MatchResult, policy: RankingPolicy) -> tuple:
    available = sum(result.score_components[name] is not None and weight > 0
                    for name, weight in policy.weights.items())
    required_met = sum(item.kind == "required_skill" and item.status == "met"
                       for item in result.requirements)
    complementarity = result.score_components.get("complementarity")
    return (
        0 if result.eligibility == "eligible" else 1,
        0 if (available >= policy.min_available_signals
              and result.evidence_coverage.known >= policy.min_known_requirements) else 1,
        0 if result.ranking_score is not None else 1,
        -(result.ranking_score if result.ranking_score is not None else 0),
        -required_met,
        -(complementarity if complementarity is not None else -1),
        result.candidate_id,
    )


def rank_candidates(
    request: MatchRequest,
    policy: RankingPolicy,
    *,
    team_members: Mapping[int, CandidateInput] | None = None,
) -> list[MatchResult]:
    """Exclude ineligible/private profiles, then order visible candidates stably."""
    if not isinstance(request, MatchRequest) or not isinstance(policy, RankingPolicy):
        raise TypeError("Se requieren MatchRequest y RankingPolicy.")
    if request.policy_version != policy.version:
        raise ValueError("La versión de la solicitud no coincide con la política.")
    if team_members is not None and (not isinstance(team_members, Mapping) or any(
        not isinstance(key, int) or isinstance(key, bool)
        or not isinstance(value, CandidateInput) for key, value in team_members.items()
    )):
        raise TypeError("team_members debe mapear identificadores a CandidateInput.")

    event = request.event
    catalog = policy.eligibility.catalog
    gaps = assess_team_gaps(event, team_members, catalog)
    # Partial rosters may support an individual role fact, but not a full team
    # complementarity component. Keep the ranking signal absent in that case.
    complete_team = gaps is not None and all(value is not None for value in (
        gaps.open_roles, gaps.missing_required_skills, gaps.missing_preferred_skills
    ))
    ranked: list[MatchResult] = []
    for candidate in request.candidates:
        decision = assess_eligibility(event, candidate, policy.eligibility)
        if decision.status == "ineligible" or decision.candidate_id is None:
            continue
        complement = (complementarity_score(event, candidate, gaps, catalog)
                      if complete_team else None)
        try:
            cosine = cosine_similarity(
                candidate.profile_embedding, event.event_embedding,
                left_model=candidate.embedding_model, right_model=event.embedding_model,
                left_version=candidate.embedding_source_version,
                right_version=event.embedding_source_version,
            )
        except InvalidEmbeddingError:
            cosine = None
        breakdown = score_candidate(
            decision.requirements, policy,
            complementarity=complement.coverage if complement is not None else None,
            semantic_similarity=cosine,
            interests=_interest_signal(event, candidate, catalog),
        )
        result = MatchResult(
            event_id=event.event_id, candidate_id=decision.candidate_id,
            eligibility=decision.status, eligibility_reasons=list(decision.reason_codes),
            requirements=list(decision.requirements), ranking_score=breakdown.score,
            score_components=breakdown.components,
            evidence_coverage=_evidence_coverage(decision.requirements),
            policy_version=policy.version,
        )
        result.explanation = explain_match(result)
        ranked.append(result)
    ranked.sort(key=lambda result: _sort_key(result, policy))
    return ranked[:request.top_n] if request.top_n is not None else ranked
