import pytest
from pydantic import ValidationError

from app.services.ai.matching.eligibility import EligibilityPolicy
from app.services.ai.matching.explanations import explain_match
from app.services.ai.matching.policy import RankingPolicy
from app.services.ai.matching.ranking import rank_candidates, score_candidate
from app.services.ai.matching.schemas import (CandidateInput, EventInput, Evidence,
                                              MatchRequest, MatchResult, Participant,
                                              RequirementAssessment)


def fact(value, kind="skill", *, source="user_declared", polarity="affirms", confirmed=True):
    return Evidence(value=value, kind=kind, source=source,
                    polarity=polarity, confirmed=confirmed)


def event(*, required=(), preferred=(), roles=(), themes=(), participants=(),
          embeddings=None, version="source-v1", model="fixture"):
    return EventInput(
        event_id=10, creator_id=1, state="open",
        requirements={"categoria": "Académico", "habilidades_obligatorias": list(required),
                      "habilidades_deseables": list(preferred), "roles_buscados": list(roles),
                      "intereses_relacionados": list(themes)},
        confirmed_requirements=[fact(term, source="organizer_confirmed")
                                for term in (*required, *preferred)],
        participants=None if participants is None else list(participants),
        event_embedding=embeddings,
        embedding_model=model if embeddings is not None else None,
        embedding_source_version=version if embeddings is not None else None,
    )


def candidate(user_id, *, skills=None, interests=(), preferences=None,
              visibility="visible", account="active", embeddings=None,
              version="source-v1", model="fixture"):
    profile = ({"habilidades": [], "intereses": list(interests),
                "areas_mejora": [], "resumen_publico": ""} if interests else None)
    return CandidateInput(
        user_id=user_id, profile=profile, declared_skills=skills,
        role_preferences=preferences, visibility=visibility, account_state=account,
        profile_embedding=embeddings,
        embedding_model=model if embeddings is not None else None,
        embedding_source_version=version if embeddings is not None else None,
    )


def run_rank(project, people, *, policy=None, top_n=None, team_members=None):
    policy = policy or RankingPolicy()
    request = MatchRequest(event=project, candidates=people,
                           policy_version=policy.version, top_n=top_n)
    return rank_candidates(request, policy, team_members=team_members)


def test_default_policy_and_weight_validation():
    policy = RankingPolicy()
    assert policy.weights == {
        "required_skills": 0.40, "complementarity": 0.25,
        "preferred_skills": 0.15, "semantic_similarity": 0.10,
        "interests": 0.10,
    }
    for kwargs in ({"required_weight": 0.41}, {"interest_weight": -0.1},
                   {"required_weight": float("nan")}, {"min_available_signals": 0},
                   {"min_known_requirements": -1},
                   {"version": " "}):
        with pytest.raises(ValueError):
            RankingPolicy(**kwargs)


def test_score_reweights_available_signals_and_preserves_zero_vs_none():
    project = event(required=["Python"], preferred=["Docker"])
    person = candidate(2, skills=[fact("Python"), fact("Docker", polarity="denies")])
    from app.services.ai.matching.requirements import assess_requirements
    assessments = assess_requirements(project, person)
    breakdown = score_candidate(assessments, RankingPolicy())
    assert breakdown.components["required_skills"] == 1
    assert breakdown.components["preferred_skills"] == 0
    assert breakdown.components["semantic_similarity"] is None
    assert breakdown.score == pytest.approx(0.4 / 0.55)
    assert breakdown.available_signals == 2
    assert score_candidate([], RankingPolicy()).score is None
    assert score_candidate([], RankingPolicy(), semantic_similarity=0).components[
        "semantic_similarity"] == 0.5
    with pytest.raises(ValueError):
        score_candidate([], RankingPolicy(), interests=1.1)


def test_eligibility_precedes_score_and_negative_beats_high_cosine():
    project = event(required=["Python"], embeddings=[1.0, 0.0])
    skilled = candidate(3, skills=[fact("Python")], embeddings=[0.0, 1.0])
    denied = candidate(2, skills=[fact("Python", polarity="denies")],
                       embeddings=[1.0, 0.0])
    results = run_rank(project, [denied, skilled])
    assert [item.candidate_id for item in results] == [3, 2]
    assert results[0].eligibility == "eligible"
    assert results[1].eligibility == "needs_review"
    strict = RankingPolicy(eligibility=EligibilityPolicy(
        exclude_confirmed_missing_required_skills=True))
    assert [item.candidate_id for item in run_rank(project, [denied, skilled], policy=strict)] == [3]


def test_confirmed_strict_schedule_conflict_excludes_despite_identical_embeddings():
    project = event(embeddings=[1.0, 0.0])
    project.requirements.restricciones_explicitas = ["disponibilidad los domingos"]
    project.explicit_constraints = [fact("disponibilidad los domingos", "constraint",
                                         source="organizer_confirmed")]
    unavailable = candidate(2, skills=[], embeddings=[1.0, 0.0])
    unavailable.availability = [fact("domingos", "availability", polarity="denies")]
    available = candidate(3, skills=[], embeddings=[0.0, 1.0])
    available.availability = [fact("domingos", "availability")]
    policy = RankingPolicy(eligibility=EligibilityPolicy(
        strict_constraint_terms=frozenset({"disponibilidad los domingos"})))
    assert [item.candidate_id for item in run_rank(project, [unavailable, available],
                                                   policy=policy)] == [3]


def test_private_inactive_creator_and_existing_participant_are_absent():
    project = event(participants=[Participant(user_id=8, role=None, confirmed=True)])
    people = [candidate(2, skills=[]), candidate(3, visibility="hidden"),
              candidate(4, visibility="unknown"), candidate(5, account="inactive"),
              candidate(1), candidate(8)]
    results = run_rank(project, people)
    assert [item.candidate_id for item in results] == [2]
    assert "3" not in repr(results) and "4" not in repr(results)


def test_incompatible_embedding_model_or_version_stays_none():
    project = event(required=["Python"], embeddings=[1.0, 0.0])
    wrong_model = candidate(2, skills=[fact("Python")], embeddings=[1.0, 0.0], model="other")
    wrong_version = candidate(3, skills=[fact("Python")], embeddings=[1.0, 0.0], version="older")
    results = run_rank(project, [wrong_model, wrong_version])
    assert all(item.score_components["semantic_similarity"] is None for item in results)
    assert all("embeddings comparables" in " ".join(item.explanation.unknowns) for item in results)


def test_incomplete_team_disables_complementarity_component():
    project = event(required=["Python"], participants=[
        Participant(user_id=8, role=None, confirmed=True)])
    results = run_rank(project, [candidate(2, skills=[fact("Python")])])
    assert results[0].score_components["complementarity"] is None
    assert results[0].ranking_score == 1
    assert results[0].evidence_coverage.known == 1
    hidden_member = {8: candidate(8, skills=[], visibility="hidden")}
    assert run_rank(project, [candidate(2, skills=[fact("Python")])],
                    team_members=hidden_member)[0].score_components["complementarity"] is None


def test_interest_is_thematic_only_and_learning_goal_never_fulfills_skill():
    project = event(required=["Python"], themes=["Videojuegos"])
    interested = candidate(2, skills=[], interests=["Videojuegos"])
    interested.profile.areas_mejora.append("Python")
    result = run_rank(project, [interested])[0]
    assert result.score_components["required_skills"] is None
    assert result.score_components["interests"] == 1
    assert result.eligibility == "needs_review"
    assert any("intereses" in line for line in result.explanation.strengths)
    assert not any("Evidencia confirmada para habilidad" in line for line in result.explanation.strengths)


def test_insufficient_information_group_and_stable_order_top_n():
    project = event(required=["Python"], embeddings=[1.0, 0.0], participants=None)
    sufficient = candidate(9, skills=[fact("Python")], embeddings=[1.0, 0.0])
    one_signal = candidate(4, skills=[fact("Python")])
    no_signal = candidate(2, skills=None)
    results = run_rank(project, [no_signal, one_signal, sufficient])
    assert [item.candidate_id for item in results] == [9, 4, 2]
    assert results[-1].ranking_score is None
    assert results[-1].evidence_coverage.unknown == 1
    assert [item.candidate_id for item in run_rank(project, [one_signal, sufficient, no_signal],
                                                   top_n=2)] == [9, 4]


def test_two_weak_signals_do_not_look_more_certain_than_confirmed_evidence():
    project = event(preferred=["Docker"], themes=["Videojuegos"],
                    embeddings=[1.0, 0.0], participants=None)
    confirmed = candidate(3, skills=[fact("Docker")], embeddings=[0.0, 1.0])
    thematic = candidate(2, skills=None, interests=["Videojuegos"],
                         embeddings=[1.0, 0.0])
    results = run_rank(project, [thematic, confirmed])
    assert [item.candidate_id for item in results] == [3, 2]
    assert results[0].evidence_coverage.known == 1
    assert results[1].evidence_coverage.known == 0
    assert results[1].ranking_score > results[0].ranking_score


def test_reproducible_ties_and_duplicate_or_version_rejection():
    project = event(required=["Python"])
    first = candidate(3, skills=[fact("Python")])
    second = candidate(2, skills=[fact("Python")])
    assert [item.candidate_id for item in run_rank(project, [first, second])] == [2, 3]
    with pytest.raises(ValidationError):
        MatchRequest(event=project, candidates=[first, first], policy_version=RankingPolicy().version)
    with pytest.raises(ValueError):
        rank_candidates(MatchRequest(event=project, candidates=[first], policy_version="other"),
                        RankingPolicy())
    duplicate = RequirementAssessment(requirement="UE5", kind="required_skill",
                                      status="unknown", reason="pendiente")
    equivalent = RequirementAssessment(requirement="Unreal Engine 5", kind="required_skill",
                                       status="unknown", reason="pendiente")
    with pytest.raises(ValueError):
        score_candidate([duplicate, equivalent], RankingPolicy())
    unsupported = RequirementAssessment(
        requirement="Python", kind="required_skill", status="met", reason="synthetic",
        evidence=[fact("Python", source="organizer_confirmed")],
    )
    with pytest.raises(ValueError):
        score_candidate([unsupported], RankingPolicy())


def test_explanations_are_deterministic_evidence_based_and_have_no_percentage():
    project = event(required=["Python", "Docker"])
    person = candidate(2, skills=[fact("Python"), fact("Docker", polarity="denies")])
    result = run_rank(project, [person])[0]
    assert explain_match(result) == result.explanation
    assert any("Python" in item for item in result.explanation.strengths)
    assert any("Docker" in item for item in result.explanation.gaps)
    assert "%" not in repr(result.explanation)
    assert "compatible" not in repr(result.explanation).lower()
    unsupported = MatchResult(
        event_id=10, candidate_id=2, eligibility="eligible", policy_version="v1",
        requirements=[RequirementAssessment(requirement="Python", kind="required_skill",
                                            status="met", reason="synthetic")],
    )
    assert explain_match(unsupported).strengths == []
