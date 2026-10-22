"""Evidence-based requirement coverage without scoring or semantic inference."""

import re
from collections.abc import Iterable

from .normalization import DEFAULT_EQUIVALENCES, EquivalenceCatalog, apply_equivalence, normalize_term
from .schemas import CandidateInput, EventInput, Evidence, RequirementAssessment


def _same_term(left: str, right: str, catalog: EquivalenceCatalog) -> bool:
    return apply_equivalence(left, catalog) == apply_equivalence(right, catalog)


def _matching(items: Iterable[Evidence] | None, term: str, catalog: EquivalenceCatalog,
              *, kind: str) -> list[Evidence]:
    return [item for item in (items or ())
            if item.kind == kind and _same_term(item.value, term, catalog)]


def _matching_candidate_skills(items: Iterable[Evidence] | None, term: str,
                               catalog: EquivalenceCatalog) -> list[Evidence]:
    matched = []
    for item in items or ():
        if item.kind != "skill":
            continue
        if _same_term(item.value, term, catalog):
            matched.append(item)
            continue
        if item.polarity == "denies":
            # Only a narrow, explicit negation is stripped. No synonym inference.
            negated = re.fullmatch(r"(?:no\s+(?:se|tengo|domino)|sin)\s+(.+)",
                                   normalize_term(item.value))
            if negated and _same_term(negated.group(1), term, catalog):
                matched.append(item)
    return matched


_CONSTRAINT_FILLER = {
    "a", "al", "con", "de", "del", "disponibilidad", "el", "en", "la", "las",
    "los", "para", "por", "requiere", "requerida", "se", "un", "una", "y",
    "no", "puedo", "asistir", "estar",
}


def _constraint_mentions(evidence: str, requirement: str, *, require_all: bool = True) -> bool:
    """Compare explicit condition tokens without claiming an unmentioned clause.

    Positive evidence must cover every salient part of a condition. A confirmed
    denial of any part can contradict a conjunctive condition.
    """
    evidence_terms = set(normalize_term(evidence).split()) - _CONSTRAINT_FILLER
    required_terms = set(normalize_term(requirement).split()) - _CONSTRAINT_FILLER
    if not required_terms:
        return normalize_term(evidence) == normalize_term(requirement)
    return required_terms <= evidence_terms if require_all else bool(evidence_terms & required_terms)


def _dedupe_terms(items: Iterable[str], catalog: EquivalenceCatalog) -> list[str]:
    seen = set()
    unique = []
    for item in items:
        key = apply_equivalence(item, catalog)
        if key not in seen:
            unique.append(item)
            seen.add(key)
    return unique


def _candidate_status(evidence: list[Evidence]) -> tuple[str, list[Evidence], str]:
    confirmed = [item for item in evidence if item.confirmed and item.source == "user_declared"]
    positive = [item for item in confirmed if item.polarity == "affirms"]
    negative = [item for item in confirmed if item.polarity == "denies"]
    if positive and negative:
        return "unknown", positive + negative, "evidencia_contradictoria"
    if positive:
        return "met", positive, "evidencia_positiva_confirmada"
    if negative:
        return "unmet_confirmed", negative, "negacion_confirmada"
    return "unknown", evidence, "evidencia_de_candidato_pendiente"


def _assessment(term: str, kind: str, status: str, evidence: list[Evidence], reason: str) -> RequirementAssessment:
    return RequirementAssessment(requirement=term, kind=kind, status=status,
                                 evidence=evidence, reason=reason)


def assess_requirements(
    event: EventInput,
    candidate: CandidateInput,
    catalog: EquivalenceCatalog = DEFAULT_EQUIVALENCES,
) -> list[RequirementAssessment]:
    """Assess stated requirements; absence and unreviewed AI remain unknown.

    Only organizer-confirmed requirements and user-confirmed evidence can yield
    `met` or `unmet_confirmed`. A preference for a role is not proof of skill.
    """
    if not isinstance(event, EventInput) or not isinstance(candidate, CandidateInput):
        raise TypeError("Se requieren EventInput y CandidateInput.")
    if not isinstance(catalog, EquivalenceCatalog):
        raise TypeError("Se requiere un catálogo versionado.")
    if event.requirements is None:
        return []

    requirements = event.requirements
    result: list[RequirementAssessment] = []
    for kind, terms in (
        ("required_skill", requirements.habilidades_obligatorias),
        ("preferred_skill", requirements.habilidades_deseables),
    ):
        for term in _dedupe_terms(terms, catalog):
            organizer = [item for item in _matching(event.confirmed_requirements, term, catalog, kind="skill")
                         if item.confirmed and item.source == "organizer_confirmed"]
            if not organizer or {item.polarity for item in organizer} != {"affirms"}:
                result.append(_assessment(term, kind, "unknown", organizer, "requisito_sin_confirmar"))
                continue
            skill_evidence = _matching_candidate_skills(candidate.declared_skills, term, catalog)
            status, supporting, reason = _candidate_status(skill_evidence)
            result.append(_assessment(term, kind, status, organizer + supporting, reason))

    for term in _dedupe_terms(requirements.roles_buscados, catalog):
        if event.outstanding_roles is not None:
            role_facts = [item for item in _matching(event.outstanding_roles, term, catalog, kind="role")
                          if item.confirmed and item.source == "organizer_confirmed"]
            open_roles = role_facts if {item.polarity for item in role_facts} == {"affirms"} else []
            if not open_roles and not event.outstanding_roles:
                result.append(_assessment(term, "open_role", "not_applicable", [], "sin_vacante_confirmada"))
                continue
            if not open_roles:
                roster_confirmed = all(item.confirmed and item.source == "organizer_confirmed"
                                       and item.polarity == "affirms" for item in event.outstanding_roles)
                status = "not_applicable" if roster_confirmed else "unknown"
                reason = "sin_vacante_confirmada" if roster_confirmed else "vacante_sin_confirmar"
                result.append(_assessment(term, "open_role", status, [], reason))
                continue
        else:
            role_facts = [item for item in _matching(event.confirmed_requirements, term, catalog, kind="role")
                          if item.confirmed and item.source == "organizer_confirmed"]
            open_roles = role_facts if {item.polarity for item in role_facts} == {"affirms"} else []
            if not open_roles:
                result.append(_assessment(term, "open_role", "unknown", [], "vacante_sin_confirmar"))
                continue
        # Role preferences alone express interest, not competence.
        skill_evidence = _matching_candidate_skills(candidate.declared_skills, term, catalog)
        status, supporting, reason = _candidate_status(skill_evidence)
        if status == "unmet_confirmed":
            # A denied skill is not proof that the person cannot hold a role.
            status, reason = "unknown", "rol_no_acreditado"
        result.append(_assessment(term, "open_role", status, open_roles + supporting, reason))

    for term in _dedupe_terms(requirements.restricciones_explicitas, catalog):
        if event.explicit_constraints is not None and not event.explicit_constraints:
            result.append(_assessment(term, "explicit_constraint", "not_applicable", [],
                                      "sin_restriccion_confirmada"))
            continue
        organizer = [item for item in (event.explicit_constraints or ())
                     if item.kind == "constraint" and item.confirmed
                     and item.source == "organizer_confirmed"
                     and _constraint_mentions(item.value, term)]
        if not organizer or {item.polarity for item in organizer} != {"affirms"}:
            result.append(_assessment(term, "explicit_constraint", "unknown", [],
                                      "restriccion_sin_confirmar"))
            continue
        availability = [item for item in (candidate.availability or ())
                        if item.kind == "availability" and _constraint_mentions(
                            item.value, term, require_all=item.polarity != "denies"
                        )]
        status, supporting, reason = _candidate_status(availability)
        result.append(_assessment(term, "explicit_constraint", status, organizer + supporting, reason))
    return result
