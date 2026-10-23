import pytest

from app.services.ai.matching.eligibility import EligibilityPolicy, assess_eligibility
from app.services.ai.matching.requirements import assess_requirements
from app.services.ai.matching.schemas import CandidateInput, EventInput, Evidence


def fact(value, kind, *, source="user_declared", polarity="affirms", confirmed=True):
    return Evidence(source=source, kind=kind, value=value,
                    polarity=polarity, confirmed=confirmed)


def event(*, category="Académico", required=(), preferred=(), roles=(), constraints=(),
          confirm_skills=(), open_roles=None, confirm_constraints=None, participants=(),
          state="open"):
    return EventInput(
        event_id=10, creator_id=1, state=state,
        requirements={
            "categoria": category,
            "habilidades_obligatorias": list(required),
            "habilidades_deseables": list(preferred),
            "roles_buscados": list(roles),
            "restricciones_explicitas": list(constraints),
        },
        confirmed_requirements=[fact(value, "skill", source="organizer_confirmed")
                                for value in confirm_skills],
        outstanding_roles=None if open_roles is None else [
            fact(value, "role", source="organizer_confirmed") for value in open_roles
        ],
        explicit_constraints=None if confirm_constraints is None else [
            fact(value, "constraint", source="organizer_confirmed")
            for value in confirm_constraints
        ],
        participants=list(participants) if participants is not None else None,
    )


def candidate(*, user_id=2, skills=None, availability=None, roles=None,
              visibility="visible", account_state="active", profile=None):
    return CandidateInput(
        user_id=user_id, declared_skills=skills, availability=availability,
        role_preferences=roles, visibility=visibility,
        account_state=account_state, profile=profile,
    )


def statuses(items):
    return {(item.kind, item.requirement): item.status for item in items}


def test_academic_python_required_and_docker_preferred():
    project = event(required=["Python"], preferred=["Docker"],
                    confirm_skills=["Python", "Docker"])
    person = candidate(skills=[fact("Python", "skill")])
    covered = assess_requirements(project, person)
    assert statuses(covered) == {
        ("required_skill", "Python"): "met",
        ("preferred_skill", "Docker"): "unknown",
    }
    assert assess_eligibility(project, person).status == "eligible"
    assert covered[0].evidence[0].source == "organizer_confirmed"
    assert covered[0].evidence[1].source == "user_declared"


def test_missing_python_is_unknown_even_with_confirmed_empty_skills():
    project = event(required=["Python"], confirm_skills=["Python"])
    for skills in (None, []):
        covered = assess_requirements(project, candidate(skills=skills))
        assert covered[0].status == "unknown"
        assert assess_eligibility(project, candidate(skills=skills)).status == "needs_review"


def test_explicit_negative_skill_is_confirmed_unmet_and_policy_controls_exclusion():
    project = event(required=["Python"], confirm_skills=["Python"])
    person = candidate(skills=[fact("Python", "skill", polarity="denies")])
    covered = assess_requirements(project, person)
    assert covered[0].status == "unmet_confirmed"
    assert covered[0].evidence[-1].polarity == "denies"
    assert assess_eligibility(project, person).status == "needs_review"
    policy = EligibilityPolicy(exclude_confirmed_missing_required_skills=True)
    decision = assess_eligibility(project, person, policy)
    assert decision.status == "ineligible"
    assert "required_skill_contradicted" in decision.reason_codes


def test_literal_negative_sentence_matches_only_its_named_skill():
    project = event(required=["Python", "Docker"], confirm_skills=["Python", "Docker"])
    person = candidate(skills=[fact("No sé Python", "skill", polarity="denies")])
    assessed = statuses(assess_requirements(project, person))
    assert assessed[("required_skill", "Python")] == "unmet_confirmed"
    assert assessed[("required_skill", "Docker")] == "unknown"


def test_conflicting_evidence_does_not_create_a_confirmed_exclusion():
    project = event(required=["Python"], confirm_skills=["Python"])
    person = candidate(skills=[fact("Python", "skill"),
                               fact("Python", "skill", polarity="denies")])
    assert assess_requirements(project, person)[0].status == "unknown"
    project.confirmed_requirements.append(
        fact("Python", "skill", source="organizer_confirmed", polarity="denies")
    )
    assert assess_requirements(project, person)[0].status == "unknown"
    assert assess_eligibility(
        project, person, EligibilityPolicy(exclude_confirmed_missing_required_skills=True)
    ).status == "needs_review"


def test_unreviewed_ai_does_not_prove_or_disprove_skill():
    project = event(required=["Python"], confirm_skills=["Python"])
    person = candidate(skills=[fact("Python", "skill", source="ai_unreviewed", confirmed=False)])
    assert assess_requirements(project, person)[0].status == "unknown"
    unconfirmed_project = event(required=["Python"])
    assert assess_requirements(unconfirmed_project, candidate(skills=[fact("Python", "skill")]))[0].status == "unknown"


def test_learning_goal_and_interest_do_not_count_as_python_skill():
    project = event(required=["Python"], confirm_skills=["Python"])
    person = candidate(
        profile={"habilidades": [], "intereses": ["Python"],
                 "areas_mejora": ["Python"], "resumen_publico": ""},
        skills=None,
    )
    assert assess_requirements(project, person)[0].status == "unknown"


def test_only_versioned_ue5_equivalence_counts():
    game_jam = event(category="Competencia", required=["Unreal Engine 5"],
                     confirm_skills=["Unreal Engine 5"])
    assert assess_requirements(game_jam, candidate(skills=[fact("UE5", "skill")]))[0].status == "met"
    assert assess_requirements(game_jam, candidate(skills=[fact("Unreal Engine", "skill")]))[0].status == "unknown"


def test_deportivo_portero_role_requires_competence_not_just_preference():
    match = event(category="Deportivo", roles=["portero"], open_roles=["portero"])
    preference = candidate(roles=[fact("portero", "role_preference")])
    assert assess_requirements(match, preference)[0].status == "unknown"
    actual = candidate(skills=[fact("portero", "skill")])
    assert assess_requirements(match, actual)[0].status == "met"
    filled = event(category="Deportivo", roles=["portero"], open_roles=[])
    assert assess_requirements(filled, actual)[0].status == "not_applicable"


def test_sunday_constraint_needs_confirmed_contradiction_and_explicit_strict_policy():
    match = event(category="Deportivo", constraints=["disponibilidad los domingos"],
                  confirm_constraints=["disponibilidad los domingos"])
    unavailable = candidate(availability=[fact("domingos", "availability", polarity="denies")])
    covered = assess_requirements(match, unavailable)
    assert covered[0].status == "unmet_confirmed"
    assert assess_eligibility(match, unavailable).status == "eligible"
    strict = EligibilityPolicy(strict_constraint_terms=frozenset({"disponibilidad los domingos"}))
    assert assess_eligibility(match, unavailable, strict).status == "ineligible"
    available = candidate(availability=[fact("domingos", "availability")])
    assert assess_requirements(match, available)[0].status == "met"
    unknown = candidate(availability=None)
    assert assess_requirements(match, unknown)[0].status == "unknown"
    assert assess_eligibility(match, unknown, strict).status == "needs_review"


def test_unconfirmed_constraint_never_excludes_even_when_policy_names_it():
    match = event(constraints=["domingos"], confirm_constraints=None)
    person = candidate(availability=[fact("domingos", "availability", polarity="denies")])
    strict = EligibilityPolicy(strict_constraint_terms=frozenset({"domingos"}))
    assert assess_requirements(match, person)[0].status == "unknown"
    assert assess_eligibility(match, person, strict).status == "needs_review"


@pytest.mark.parametrize("change,reason", [
    ({"account_state": "inactive"}, "account_inactive"),
    ({"user_id": 1}, "event_creator"),
])
def test_confirmed_account_or_creator_exclusions(change, reason):
    person = candidate(**change)
    decision = assess_eligibility(event(), person)
    assert decision.status == "ineligible"
    assert reason in decision.reason_codes


def test_closed_event_and_confirmed_participant_are_excluded():
    person = candidate()
    assert "event_closed" in assess_eligibility(event(state="closed"), person).reason_codes
    participant_event = event(participants=[{"user_id": 2, "role": "portero", "confirmed": True}])
    decision = assess_eligibility(participant_event, person)
    assert decision.status == "ineligible"
    assert "already_participant" in decision.reason_codes


def test_unconfirmed_participant_and_missing_roster_require_review():
    person = candidate()
    uncertain = event(participants=[{"user_id": 2, "confirmed": False}])
    assert assess_eligibility(uncertain, person).status == "needs_review"
    missing = event(participants=None)
    assert assess_eligibility(missing, person).status == "needs_review"


def test_hidden_and_unknown_visibility_do_not_expose_profile_or_id():
    private = candidate(visibility="hidden", profile={
        "habilidades": ["Python"], "resumen_publico": "Dato privado",
    })
    hidden = assess_eligibility(event(required=["Python"], confirm_skills=["Python"]), private)
    assert hidden.status == "ineligible"
    assert hidden.candidate_id is None
    assert hidden.requirements == ()
    assert "Dato privado" not in repr(hidden)
    unknown = assess_eligibility(event(), candidate(visibility="unknown"))
    assert unknown.status == "needs_review"
    assert unknown.candidate_id is None
    assert unknown.requirements == ()


def test_unknown_account_event_and_requirements_are_not_false_exclusions():
    match = EventInput(event_id=10, creator_id=1, state="unknown", participants=[])
    person = candidate(account_state="unknown")
    decision = assess_eligibility(match, person)
    assert decision.status == "needs_review"
    assert "account_state_unknown" in decision.reason_codes
    assert "event_state_unknown" in decision.reason_codes
    assert "requirements_unknown" in decision.reason_codes


def test_preferences_never_exclude_candidates():
    project = event(preferred=["Docker"], confirm_skills=["Docker"])
    person = candidate(skills=[fact("Docker", "skill", polarity="denies")])
    assert assess_requirements(project, person)[0].status == "unmet_confirmed"
    assert assess_eligibility(project, person).status == "eligible"
