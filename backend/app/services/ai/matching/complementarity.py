"""Local team-gap signal, based only on confirmed facts and visible profiles."""

from collections.abc import Mapping
from dataclasses import dataclass

from .normalization import DEFAULT_EQUIVALENCES, EquivalenceCatalog, apply_equivalence
from .requirements import assess_requirements
from .schemas import CandidateInput, EventInput, Evidence


@dataclass(frozen=True)
class TeamGaps:
    # None means that the relevant team facts are unavailable, not an empty gap.
    open_roles: tuple[str, ...] | None
    missing_required_skills: tuple[str, ...] | None
    missing_preferred_skills: tuple[str, ...] | None


@dataclass(frozen=True)
class ComplementaritySignal:
    filled_roles: tuple[str, ...]
    filled_required_skills: tuple[str, ...]
    filled_preferred_skills: tuple[str, ...]
    # A local fraction of confirmed gaps covered, not a global match score.
    coverage: float | None


def _key(term: str, catalog: EquivalenceCatalog) -> str:
    return apply_equivalence(term, catalog)


def _confirmed_positive(items: list[Evidence] | None, term: str, kind: str,
                        source: str, catalog: EquivalenceCatalog) -> bool:
    facts = [item for item in (items or ()) if item.kind == kind and item.source == source
             and item.confirmed and _key(item.value, catalog) == _key(term, catalog)]
    return bool(facts) and {item.polarity for item in facts} == {"affirms"}


def _unique(terms: list[str], catalog: EquivalenceCatalog) -> tuple[str, ...]:
    seen: set[str] = set()
    result: list[str] = []
    for term in terms:
        key = _key(term, catalog)
        if key not in seen:
            seen.add(key)
            result.append(term)
    return tuple(result)


def assess_team_gaps(
    event: EventInput,
    team_members: Mapping[int, CandidateInput] | None = None,
    catalog: EquivalenceCatalog = DEFAULT_EQUIVALENCES,
) -> TeamGaps | None:
    """Find uncovered, organizer-confirmed requirements in a known roster.

    `team_members` supplies visible profiles for confirmed participants only.
    Participant roles do not imply any skill. Unknown roster returns None;
    missing member skill data makes only skill gaps unknown.
    """
    if not isinstance(event, EventInput) or not isinstance(catalog, EquivalenceCatalog):
        raise TypeError("Se requieren EventInput y un catálogo versionado.")
    if event.participants is None or any(not person.confirmed for person in event.participants):
        return None

    requirements = event.requirements
    if requirements is None:
        return TeamGaps(None, None, None)

    participant_roles = {_key(person.role, catalog) for person in event.participants
                         if person.role is not None}
    role_terms = _unique(requirements.roles_buscados, catalog)
    if event.outstanding_roles is not None:
        # An explicit, confirmed vacancy list is authoritative. An unreviewed
        # entry makes the role picture incomplete rather than creating a gap.
        roles_known = all(item.confirmed and item.source == "organizer_confirmed"
                          and item.polarity == "affirms" for item in event.outstanding_roles)
        open_roles = tuple(term for term in role_terms
                           if _confirmed_positive(event.outstanding_roles, term, "role",
                                                  "organizer_confirmed", catalog)
                           and _key(term, catalog) not in participant_roles) if roles_known else None
    elif any(person.role is None for person in event.participants):
        open_roles = None
    else:
        open_roles = tuple(term for term in role_terms
                           if _confirmed_positive(event.confirmed_requirements, term, "role",
                                                  "organizer_confirmed", catalog)
                           and _key(term, catalog) not in participant_roles)
        if role_terms and not any(_confirmed_positive(event.confirmed_requirements, term,
                               "role", "organizer_confirmed", catalog) for term in role_terms):
            open_roles = None

    required = _unique(requirements.habilidades_obligatorias, catalog)
    preferred = _unique(requirements.habilidades_deseables, catalog)
    confirmed_required = tuple(term for term in required
                               if _confirmed_positive(event.confirmed_requirements, term,
                                                      "skill", "organizer_confirmed", catalog))
    confirmed_preferred = tuple(term for term in preferred
                                if _confirmed_positive(event.confirmed_requirements, term,
                                                       "skill", "organizer_confirmed", catalog))
    # If some requirements have not been reviewed, they are simply not
    # asserted as team gaps. The confirmed subset remains usable.
    members: list[CandidateInput] = []
    skill_data_known = True
    for person in event.participants:
        member = team_members.get(person.user_id) if team_members is not None else None
        if (member is None or member.user_id != person.user_id
                or member.visibility != "visible" or member.declared_skills is None):
            skill_data_known = False
            break
        members.append(member)

    if skill_data_known:
        def uncovered(terms: tuple[str, ...], kind: str) -> tuple[str, ...]:
            return tuple(term for term in terms if not any(
                item.kind == kind and item.requirement == term and item.status == "met"
                for member in members for item in assess_requirements(event, member, catalog)
            ))

        missing_required = uncovered(confirmed_required, "required_skill")
        missing_preferred = uncovered(confirmed_preferred, "preferred_skill")
    else:
        missing_required = None
        missing_preferred = None
    return TeamGaps(open_roles, missing_required, missing_preferred)


def complementarity_score(
    event: EventInput,
    candidate: CandidateInput,
    gaps: TeamGaps | None,
    catalog: EquivalenceCatalog = DEFAULT_EQUIVALENCES,
) -> ComplementaritySignal | None:
    """Credit only confirmed candidate capacities that fill known vacancies."""
    if not isinstance(event, EventInput) or not isinstance(candidate, CandidateInput):
        raise TypeError("Se requieren EventInput y CandidateInput.")
    if not isinstance(catalog, EquivalenceCatalog):
        raise TypeError("Se requiere un catálogo versionado.")
    if gaps is None or candidate.visibility != "visible" or candidate.declared_skills is None:
        return None
    assessed = assess_requirements(event, candidate, catalog)
    met = {(item.kind, _key(item.requirement, catalog)) for item in assessed
           if item.status == "met"}

    def filled(terms: tuple[str, ...] | None, kind: str) -> tuple[str, ...]:
        return tuple(term for term in (terms or ()) if (kind, _key(term, catalog)) in met)

    roles = filled(gaps.open_roles, "open_role")
    required = filled(gaps.missing_required_skills, "required_skill")
    preferred = filled(gaps.missing_preferred_skills, "preferred_skill")
    known_gap_count = sum(len(terms) for terms in (
        gaps.open_roles, gaps.missing_required_skills, gaps.missing_preferred_skills
    ) if terms is not None)
    coverage = (len(roles) + len(required) + len(preferred)) / known_gap_count if known_gap_count else None
    return ComplementaritySignal(roles, required, preferred, coverage)
