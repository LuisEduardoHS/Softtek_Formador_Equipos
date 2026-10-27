"""Conservative eligibility decisions with privacy-safe outputs."""

from dataclasses import dataclass, field
from typing import Literal

from .normalization import DEFAULT_EQUIVALENCES, EquivalenceCatalog, apply_equivalence
from .requirements import assess_requirements
from .schemas import CandidateInput, EventInput, RequirementAssessment


@dataclass(frozen=True, slots=True)
class EligibilityPolicy:
    """Explicit product choices; no constraint is strict by default."""

    catalog: EquivalenceCatalog = DEFAULT_EQUIVALENCES
    strict_constraint_terms: frozenset[str] = field(default_factory=frozenset)
    exclude_confirmed_missing_required_skills: bool = False

    def __post_init__(self):
        if not isinstance(self.catalog, EquivalenceCatalog):
            raise TypeError("Se requiere un catálogo versionado.")
        if not isinstance(self.strict_constraint_terms, frozenset) or any(
            not isinstance(term, str) or not term.strip() for term in self.strict_constraint_terms
        ):
            raise ValueError("Las restricciones estrictas deben ser términos explícitos.")
        if not isinstance(self.exclude_confirmed_missing_required_skills, bool):
            raise TypeError("La política de habilidades debe ser booleana.")


@dataclass(frozen=True, slots=True)
class EligibilityDecision:
    event_id: int
    candidate_id: int | None  # None when visibility is not confirmed public
    status: Literal["eligible", "needs_review", "ineligible"]
    reason_codes: tuple[str, ...]
    requirements: tuple[RequirementAssessment, ...] = field(default=(), repr=False)


def assess_eligibility(
    event: EventInput,
    candidate: CandidateInput,
    policy: EligibilityPolicy = EligibilityPolicy(),
) -> EligibilityDecision:
    """Apply confirmed exclusions; unknown data never becomes a false failure.

    Hidden or visibility-unknown profiles return no ID or requirement details.
    The caller must not expose an input CandidateInput directly to clients.
    """
    if not isinstance(event, EventInput) or not isinstance(candidate, CandidateInput):
        raise TypeError("Se requieren EventInput y CandidateInput.")
    if not isinstance(policy, EligibilityPolicy):
        raise TypeError("Se requiere EligibilityPolicy.")
    if candidate.visibility == "hidden":
        return EligibilityDecision(event.event_id, None, "ineligible", ("profile_hidden",))
    if candidate.visibility == "unknown":
        return EligibilityDecision(event.event_id, None, "needs_review", ("visibility_unknown",))

    hard: list[str] = []
    review: list[str] = []
    if candidate.account_state == "inactive":
        hard.append("account_inactive")
    elif candidate.account_state == "unknown":
        review.append("account_state_unknown")
    if event.state == "closed":
        hard.append("event_closed")
    elif event.state == "unknown":
        review.append("event_state_unknown")
    if candidate.user_id == event.creator_id:
        hard.append("event_creator")
    if event.participants is None:
        review.append("participants_unknown")
    else:
        same_user = [person for person in event.participants if person.user_id == candidate.user_id]
        if any(person.confirmed for person in same_user):
            hard.append("already_participant")
        elif same_user:
            review.append("participation_unconfirmed")
    if event.requirements is None:
        review.append("requirements_unknown")

    assessments = assess_requirements(event, candidate, policy.catalog)
    strict_terms = {apply_equivalence(term, policy.catalog) for term in policy.strict_constraint_terms}
    for assessment in assessments:
        if assessment.kind == "preferred_skill" or assessment.status == "not_applicable":
            continue
        if assessment.status == "unknown":
            review.append("requirement_unknown")
        elif assessment.status == "unmet_confirmed":
            if assessment.kind == "required_skill" and policy.exclude_confirmed_missing_required_skills:
                hard.append("required_skill_contradicted")
            elif assessment.kind == "explicit_constraint" and apply_equivalence(
                assessment.requirement, policy.catalog
            ) in strict_terms:
                hard.append("strict_constraint_contradicted")
            elif assessment.kind == "required_skill":
                review.append("required_skill_contradicted_review")

    status = "ineligible" if hard else "needs_review" if review else "eligible"
    reasons = tuple(dict.fromkeys(hard + review))
    return EligibilityDecision(event.event_id, candidate.user_id, status, reasons, tuple(assessments))
