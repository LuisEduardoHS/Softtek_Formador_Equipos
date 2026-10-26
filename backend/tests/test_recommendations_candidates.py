"""Organizer recommendations over prepared, validated snapshots only."""

import pytest
from pydantic import ValidationError

from app.services.ai.matching.eligibility import EligibilityPolicy
from app.services.ai.matching.policy import RankingPolicy
from app.services.ai.matching.schemas import CandidateInput, EventInput, Evidence, Participant
from app.services.ai.recommendations import OrganizerRecommendationContext, recommend_candidates


def fact(value, kind="skill", *, source="user_declared", polarity="affirms", confirmed=True):
    return Evidence(value=value, kind=kind, source=source,
                    polarity=polarity, confirmed=confirmed, source_ref="private:42")


def event(*, category="Académico", required=(), preferred=(), roles=(),
          constraints=(), roster=(), vector=None, confirmed_roles=()):
    return EventInput(
        event_id=20, creator_id=1, state="open",
        requirements={"categoria": category, "habilidades_obligatorias": list(required),
                      "habilidades_deseables": list(preferred),
                      "roles_buscados": list(roles),
                      "restricciones_explicitas": list(constraints)},
        confirmed_requirements=[fact(term, source="organizer_confirmed")
                                for term in (*required, *preferred)],
        outstanding_roles=[fact(term, "role", source="organizer_confirmed")
                           for term in confirmed_roles],
        explicit_constraints=[fact(term, "constraint", source="organizer_confirmed")
                              for term in constraints],
        participants=None if roster is None else list(roster),
        event_embedding=vector,
        embedding_model="fixture" if vector is not None else None,
        embedding_source_version="v1" if vector is not None else None,
    )


def candidate(user_id, *, skills=None, preferences=None, availability=None,
              improvement=(), visibility="visible", account="active", vector=None,
              model="fixture"):
    return CandidateInput(
        user_id=user_id, visibility=visibility, account_state=account,
        declared_skills=skills, role_preferences=preferences, availability=availability,
        profile={"habilidades": [], "intereses": [], "areas_mejora": list(improvement),
                 "resumen_publico": ""} if improvement else None,
        profile_embedding=vector,
        embedding_model=model if vector is not None else None,
        embedding_source_version="v1" if vector is not None else None,
    )


def context(*ids, members=(), pending=(), organizer=1, authorized_event=20):
    return OrganizerRecommendationContext(
        authenticated_organizer_id=organizer,
        authorized_event_id=authorized_event,
        discoverable_candidate_ids=frozenset(ids),
        confirmed_member_ids=frozenset(members),
        pending_candidate_ids=frozenset(pending),
    )


def test_academic_required_preferred_and_review_are_distinct():
    project = event(required=("Python",), preferred=("Docker",))
    people = [candidate(4, skills=None),
              candidate(3, skills=[fact("Python"), fact("Docker", polarity="denies")]),
              candidate(2, skills=[fact("Python"), fact("Docker")])]
    results = recommend_candidates(project, people, context(2, 3, 4))
    assert [item.candidate_id for item in results] == [2, 3, 4]
    assert [item.eligibility for item in results] == ["eligible", "eligible", "needs_review"]
    assert results[0].evidence_group == "sufficient_evidence"
    assert results[2].evidence_group == "insufficient_evidence"
    assert any("Python" in text for text in results[0].explanation.strengths)
    assert any("Docker" in text for text in results[1].explanation.gaps)
    assert any("por verificar" in text.lower() for text in results[2].explanation.unknowns)


def test_sports_real_vacancy_and_strict_sunday_beat_high_cosine():
    project = event(category="Deportivo", roles=("portero",),
                    confirmed_roles=("portero",),
                    constraints=("disponibilidad los domingos",), vector=[1.0, 0.0])
    valid = candidate(2, skills=[fact("portero")],
                      availability=[fact("domingos", "availability")], vector=[0.0, 1.0])
    unavailable = candidate(3, skills=[fact("portero")],
                            availability=[fact("domingos", "availability", polarity="denies")],
                            vector=[1.0, 0.0])
    preference_only = candidate(4, skills=[],
                                preferences=[fact("portero", "role_preference")],
                                availability=[fact("domingos", "availability")])
    policy = RankingPolicy(eligibility=EligibilityPolicy(
        strict_constraint_terms=frozenset({"disponibilidad los domingos"})))
    results = recommend_candidates(project, [unavailable, preference_only, valid],
                                   context(2, 3, 4), policy=policy)
    assert [item.candidate_id for item in results] == [2, 4]
    assert results[0].eligibility == "eligible"
    assert results[1].eligibility == "needs_review"
    assert any("portero" in text for text in results[0].explanation.strengths)
    assert not any("Evidencia confirmada para rol" in text
                   for text in results[1].explanation.strengths)


def test_games_equivalence_and_improvement_do_not_invent_skill():
    project = event(category="Videojuegos", required=("Unreal Engine 5",),
                    preferred=("Blender",))
    qualified = candidate(2, skills=[fact("UE5"), fact("Blender")])
    learner = candidate(3, skills=[], improvement=("Unreal Engine 5", "Blender"))
    unreviewed = candidate(4, skills=[fact("UE5", source="ai_unreviewed", confirmed=False)])
    results = recommend_candidates(project, [learner, qualified, unreviewed], context(2, 3, 4))
    assert [item.candidate_id for item in results] == [2, 3, 4]
    assert results[1].evidence_coverage.known == 0
    assert results[1].evidence_group == "insufficient_evidence"
    assert all(item.evidence_coverage.known == 0 for item in results[1:])
    assert all(not any("Blender" in line or "Unreal Engine 5" in line
                       for line in item.explanation.strengths) for item in results[1:])


def test_ties_top_n_and_pending_exclusion_are_reproducible():
    project = event(category="General", required=("Python",))
    people = [candidate(user_id, skills=[fact("Python")]) for user_id in (5, 3, 2, 4)]
    prepared = context(2, 3, 4, 5, pending=(2,))
    first = recommend_candidates(project, people, prepared, top_n=2)
    second = recommend_candidates(project, list(reversed(people)), prepared, top_n=2)
    assert [item.candidate_id for item in first] == [3, 4]
    assert first == second
    with pytest.raises(ValidationError):
        recommend_candidates(project, [people[0], people[0]], prepared)


def test_missing_roster_and_embeddings_stay_review_or_insufficient():
    project = event(required=("Python",), roster=None, vector=[1.0, 0.0])
    unknown = candidate(2, skills=None, vector=[1.0, 0.0], model="other")
    known = candidate(3, skills=[fact("Python")])
    member = candidate(4, skills=[fact("Python")])
    results = recommend_candidates(project, [unknown, known, member],
                                   context(2, 3, 4, members=(4,)))
    assert [item.candidate_id for item in results] == [3, 2]
    assert all(item.eligibility == "needs_review" for item in results)
    assert all(item.evidence_group == "insufficient_evidence" for item in results)
    assert any("Participación" in text for text in results[0].explanation.unknowns)
    assert any("embeddings comparables" in text for text in results[1].explanation.unknowns)
    assert recommend_candidates(project, [], context()) == []


def test_privacy_owner_members_visibility_and_public_projection():
    project = event(required=("Python",), roster=[
        Participant(user_id=6, role="analista", confirmed=True)])
    visible = candidate(2, skills=[fact("Python")], vector=[1.0, 0.0])
    project.event_embedding = [1.0, 0.0]
    project.embedding_model = "fixture"
    project.embedding_source_version = "v1"
    people = [visible, candidate(1, skills=[]), candidate(6, skills=[]),
              candidate(3, skills=[], visibility="hidden"),
              candidate(4, skills=[], visibility="unknown"),
              candidate(5, skills=[]), candidate(7, skills=[], account="inactive")]
    results = recommend_candidates(project, people, context(1, 2, 3, 4, 6, 7))
    assert [item.candidate_id for item in results] == [2]
    payload = str([item.model_dump() for item in results])
    for secret in ("source_ref", "private:42", "ranking_score", "profile_embedding",
                   "declared_skills", "score_components", "analista"):
        assert secret not in payload
    with pytest.raises(PermissionError, match="No se autorizó"):
        recommend_candidates(project, people, context(2, organizer=99))
    with pytest.raises(PermissionError, match="No se autorizó"):
        recommend_candidates(project, people, context(2, authorized_event=99))
    with pytest.raises(ValidationError):
        OrganizerRecommendationContext(authenticated_organizer_id=1, authorized_event_id=20,
                                       discoverable_candidate_ids=frozenset({2}),
                                       confirmed_member_ids=frozenset())
    with pytest.raises(ValidationError):
        context(2, pending=(0,))
