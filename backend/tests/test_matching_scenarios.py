"""End-to-end evaluation fixtures for the pure matching motor (no DB/Ollama)."""

import pytest
from pydantic import ValidationError

from app.services.ai.matching.eligibility import EligibilityPolicy
from app.services.ai.matching.policy import RankingPolicy
from app.services.ai.matching.ranking import rank_candidates
from app.services.ai.matching.schemas import CandidateInput, EventInput, Evidence, MatchRequest, Participant


def evidence(value, kind="skill", *, source="user_declared", polarity="affirms",
             confirmed=True):
    return Evidence(value=value, kind=kind, source=source, polarity=polarity,
                    confirmed=confirmed)


def person(user_id, *, skills=None, availability=None, preferences=None,
           interests=(), improvement=(), visibility="visible", account="active",
           vector=None, model="fixture", version="text-v1"):
    profile = None
    if interests or improvement:
        profile = {"habilidades": [], "intereses": list(interests),
                   "areas_mejora": list(improvement), "resumen_publico": ""}
    return CandidateInput(
        user_id=user_id, declared_skills=skills, availability=availability,
        role_preferences=preferences, profile=profile, visibility=visibility,
        account_state=account, profile_embedding=vector,
        embedding_model=model if vector is not None else None,
        embedding_source_version=version if vector is not None else None,
    )


def project(*, category, required=(), preferred=(), roles=(), themes=(),
            constraints=(), confirmed_skills=(), confirmed_roles=(),
            confirmed_constraints=(), roster=(), vector=None,
            model="fixture", version="text-v1", state="open"):
    return EventInput(
        event_id=50, creator_id=1, state=state,
        requirements={"categoria": category,
                      "habilidades_obligatorias": list(required),
                      "habilidades_deseables": list(preferred),
                      "roles_buscados": list(roles),
                      "intereses_relacionados": list(themes),
                      "restricciones_explicitas": list(constraints)},
        confirmed_requirements=[evidence(term, source="organizer_confirmed")
                                for term in confirmed_skills],
        outstanding_roles=None if confirmed_roles is None else [
            evidence(term, "role", source="organizer_confirmed")
            for term in confirmed_roles
        ],
        explicit_constraints=None if confirmed_constraints is None else [
            evidence(term, "constraint", source="organizer_confirmed")
            for term in confirmed_constraints
        ],
        participants=None if roster is None else list(roster),
        event_embedding=vector,
        embedding_model=model if vector is not None else None,
        embedding_source_version=version if vector is not None else None,
    )


def evaluate(event, candidates, *, team=None, policy=None, top_n=None):
    policy = policy or RankingPolicy()
    request = MatchRequest(event=event, candidates=candidates,
                           policy_version=policy.version, top_n=top_n)
    return rank_candidates(request, policy, team_members=team)


def by_id(results):
    return {result.candidate_id: result for result in results}


def statuses(result):
    return {(item.kind, item.requirement): item.status for item in result.requirements}


def public_text(result):
    explanation = result.explanation
    return " ".join(explanation.strengths + explanation.gaps + explanation.unknowns)


def test_academic_team_gap_orders_new_blender_capacity_above_redundant_python():
    event = project(category="Académico", required=["Python", "Blender"],
                    preferred=["Docker"], confirmed_skills=["Python", "Blender", "Docker"],
                    confirmed_roles=[],
                    roster=[Participant(user_id=10, role="desarrollador", confirmed=True)])
    team = {10: person(10, skills=[evidence("Python")])}
    blender = person(2, skills=[evidence("Blender"), evidence("Docker")],
                     improvement=["Python"])
    redundant = person(3, skills=[evidence("Python"), evidence("Docker")])
    results = evaluate(event, [redundant, blender], team=team)
    assert [result.candidate_id for result in results] == [2, 3]
    assert results[0].score_components["complementarity"] == 1
    assert results[1].score_components["complementarity"] == 0.5
    assert statuses(results[0])[("required_skill", "Python")] == "unknown"
    assert statuses(results[0])[("required_skill", "Blender")] == "met"
    assert statuses(results[0])[("preferred_skill", "Docker")] == "met"
    assert results[0].eligibility == "needs_review"
    assert "Python" in " ".join(results[0].explanation.unknowns)
    assert "Evidencia confirmada para habilidad obligatoria: Python" not in public_text(results[0])


def test_sports_real_vacancy_strict_sunday_overrides_cosine_and_privacy():
    event = project(category="Deportivo", roles=["portero"],
                    constraints=["disponibilidad los domingos"],
                    confirmed_roles=["portero"],
                    confirmed_constraints=["disponibilidad los domingos"],
                    roster=[Participant(user_id=10, role="delantero", confirmed=True)],
                    vector=[1.0, 0.0])
    team = {10: person(10, skills=[])}
    keeper = person(2, skills=[evidence("portero")],
                    availability=[evidence("domingos", "availability")],
                    vector=[0.0, 1.0])
    unavailable = person(3, skills=[evidence("portero")],
                         availability=[evidence("domingos", "availability", polarity="denies")],
                         vector=[1.0, 0.0])
    interested = person(4, skills=[],
                        preferences=[evidence("portero", "role_preference")],
                        availability=[evidence("domingos", "availability")])
    hidden = person(5, skills=[evidence("portero")], visibility="hidden")
    policy = RankingPolicy(eligibility=EligibilityPolicy(
        strict_constraint_terms=frozenset({"disponibilidad los domingos"})))
    results = evaluate(event, [unavailable, interested, hidden, keeper,
                               person(10, skills=[evidence("portero")])],
                       team=team, policy=policy)
    assert [result.candidate_id for result in results] == [2, 4]
    assert results[0].eligibility == "eligible"
    assert results[0].score_components["complementarity"] == 1
    assert statuses(results[0])[("open_role", "portero")] == "met"
    assert statuses(results[1])[("open_role", "portero")] == "unknown"
    assert results[1].eligibility == "needs_review"
    assert "portero" in " ".join(results[0].explanation.strengths)
    serialized = repr([result.model_dump() for result in results])
    assert "delantero" not in serialized
    assert "user_id" not in serialized


def test_sports_role_already_filled_has_no_vacancy_bonus_or_role_claim():
    event = project(category="Deportivo", roles=["portero"], confirmed_roles=[],
                    roster=[Participant(user_id=10, role="portero", confirmed=True)])
    candidate = person(2, skills=[evidence("portero")])
    result = evaluate(event, [candidate], team={10: person(10, skills=[])})[0]
    assert statuses(result)[("open_role", "portero")] == "not_applicable"
    assert result.score_components["complementarity"] is None
    assert not any("rol solicitado: portero" in item for item in result.explanation.strengths)


def test_game_jam_ue5_blender_git_without_foreign_skills_or_filled_musician_role():
    event = project(category="Videojuegos", required=["Blender", "Unreal Engine 5"],
                    preferred=["Git"], roles=["artista 3D", "programador Unreal Engine 5"],
                    confirmed_skills=["Blender", "Unreal Engine 5", "Git"],
                    confirmed_roles=["artista 3D", "programador Unreal Engine 5"],
                    roster=[Participant(user_id=10, role="músico", confirmed=True)],
                    vector=[1.0, 0.0])
    team = {10: person(10, skills=[])}
    programmer = person(2, skills=[evidence("UE5"), evidence("Git"),
                                   evidence("programador Unreal Engine 5")],
                        vector=[0.0, 1.0])
    artist = person(3, skills=[evidence("Blender"), evidence("artista 3D")])
    unreviewed = person(4, skills=[evidence("Blender", source="ai_unreviewed", confirmed=False)],
                        improvement=["Python", "CAD", "programación de navegación"],
                        vector=[1.0, 0.0])
    results = evaluate(event, [unreviewed, artist, programmer], team=team)
    assert [result.candidate_id for result in results] == [2, 3, 4]
    assert statuses(results[0])[("required_skill", "Unreal Engine 5")] == "met"
    assert statuses(results[0])[("preferred_skill", "Git")] == "met"
    assert statuses(results[2])[("required_skill", "Blender")] == "unknown"
    assert results[2].score_components["required_skills"] is None
    assert results[2].score_components["semantic_similarity"] == 1
    assert all("músico" not in public_text(result) for result in results)
    assert all(not any(term in public_text(result) for term in
                       ("Python", "CAD", "navegación")) for result in results)


def test_general_unknown_team_missing_or_incompatible_vectors_and_stable_top_n():
    event = project(category="Otra", required=["organización"],
                    confirmed_skills=["organización"], confirmed_roles=None,
                    roster=None, vector=[1.0, 0.0])
    accredited = person(3, skills=[evidence("organización")])
    old_model = person(2, skills=[evidence("organización")], vector=[1.0, 0.0],
                       model="other-model")
    unknown = person(4, skills=None, improvement=["organización"],
                     vector=[1.0, 0.0], version="older-text")
    hidden = person(5, skills=[evidence("organización")], visibility="hidden")
    candidates = [unknown, old_model, hidden, accredited]
    first = evaluate(event, candidates)
    second = evaluate(event, list(reversed(candidates)))
    assert [result.candidate_id for result in first] == [2, 3, 4]
    assert [result.model_dump() for result in first] == [result.model_dump() for result in second]
    assert [result.candidate_id for result in evaluate(event, candidates, top_n=2)] == [2, 3]
    assert all(result.score_components["complementarity"] is None for result in first)
    assert all(result.score_components["semantic_similarity"] is None for result in first)
    assert first[2].eligibility == "needs_review"
    assert first[2].ranking_score is None
    assert statuses(first[2])[("required_skill", "organización")] == "unknown"
    assert not any("Evidencia confirmada para habilidad" in phrase
                   for phrase in first[2].explanation.strengths)


def test_explicit_empty_vs_unknown_team_and_duplicate_candidate_rejection():
    empty = project(category="General", required=["Python"],
                    confirmed_skills=["Python"], confirmed_roles=[], roster=[])
    unknown = project(category="General", required=["Python"],
                      confirmed_skills=["Python"], confirmed_roles=[], roster=None)
    person_a = person(2, skills=[evidence("Python")])
    assert evaluate(empty, [person_a])[0].score_components["complementarity"] == 1
    assert evaluate(unknown, [person_a])[0].score_components["complementarity"] is None
    with pytest.raises(ValidationError):
        MatchRequest(event=empty, candidates=[person_a, person_a],
                     policy_version=RankingPolicy().version)


def test_partial_positive_schedule_evidence_does_not_confirm_full_location_constraint():
    condition = "disponibilidad los domingos en Monterrey"
    event = project(category="Deportivo", constraints=[condition],
                    confirmed_constraints=[condition], confirmed_roles=[], roster=[])
    sunday_only = person(2, skills=[], availability=[evidence("domingos", "availability")])
    policy = RankingPolicy(eligibility=EligibilityPolicy(
        strict_constraint_terms=frozenset({condition})))
    result = evaluate(event, [sunday_only], policy=policy)[0]
    assert statuses(result)[("explicit_constraint", condition)] == "unknown"
    assert result.eligibility == "needs_review"
    assert condition in " ".join(result.explanation.unknowns)
    assert condition not in " ".join(result.explanation.strengths)
    denying_sunday = person(3, skills=[], availability=[evidence(
        "domingos", "availability", polarity="denies")])
    assert evaluate(event, [denying_sunday], policy=policy) == []
    partial_organizer = project(category="Deportivo", constraints=[condition],
                                confirmed_constraints=["domingos"],
                                confirmed_roles=[], roster=[])
    full_candidate = person(4, skills=[], availability=[evidence(
        "domingos en Monterrey", "availability")])
    assessed = evaluate(partial_organizer, [full_candidate], policy=policy)[0]
    assert statuses(assessed)[("explicit_constraint", condition)] == "unknown"
