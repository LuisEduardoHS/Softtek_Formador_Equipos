"""User-facing project recommendations over prepared snapshots, without I/O."""

import pytest
from pydantic import ValidationError

from app.services.ai.matching.eligibility import EligibilityPolicy
from app.services.ai.matching.policy import RankingPolicy
from app.services.ai.matching.schemas import CandidateInput, EventInput, Evidence, Participant
from app.services.ai.recommendations import UserRecommendationContext, recommend_projects


def fact(value, kind="skill", *, source="user_declared", polarity="affirms",
         confirmed=True):
    return Evidence(value=value, kind=kind, source=source, polarity=polarity,
                    confirmed=confirmed, source_ref="private:92")


def user(*, skills=None, availability=None, improvement=(), visibility="visible",
         account="active", vector=None, model="fixture"):
    return CandidateInput(
        user_id=2, visibility=visibility, account_state=account,
        declared_skills=skills, availability=availability,
        profile={"habilidades": [], "intereses": [], "areas_mejora": list(improvement),
                 "resumen_publico": ""} if improvement else None,
        profile_embedding=vector, embedding_model=model if vector is not None else None,
        embedding_source_version="v1" if vector is not None else None,
    )


def project(event_id, *, category="Académico", owner=1, required=(), preferred=(),
            roles=(), confirmed_roles=(), constraints=(), roster=(), state="open",
            vector=None):
    return EventInput(
        event_id=event_id, creator_id=owner, state=state,
        requirements={"categoria": category,
                      "habilidades_obligatorias": list(required),
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
        event_embedding=vector, embedding_model="fixture" if vector is not None else None,
        embedding_source_version="v1" if vector is not None else None,
    )


def context(*events, actor=2, consent=True, members=(), invitations=(), applications=()):
    return UserRecommendationContext(
        authenticated_user_id=actor, discovery_consent=consent,
        discoverable_event_ids=frozenset(events),
        confirmed_member_event_ids=frozenset(members),
        pending_invitation_event_ids=frozenset(invitations),
        pending_application_event_ids=frozenset(applications),
    )


def test_academic_projects_use_confirmed_core_and_preference_without_cross_event_score():
    person = user(skills=[fact("Python"), fact("Docker")])
    basic = project(10, required=("Python",))
    preferred = project(20, required=("Python",), preferred=("Docker",))
    results = recommend_projects(person, [basic, preferred], context(10, 20))
    assert [item.event_id for item in results] == [20, 10]
    assert all(item.eligibility == "eligible" for item in results)
    assert results[0].evidence_group == "sufficient_evidence"
    assert any("Docker" in line for line in results[0].explanation.strengths)
    assert all("ranking_score" not in item.model_dump() for item in results)


def test_sports_strict_sunday_conflict_excludes_even_with_high_cosine():
    person = user(skills=[fact("portero")],
                  availability=[fact("domingos", "availability", polarity="denies")],
                  vector=[1.0, 0.0])
    strict = project(10, category="Deportivo", roles=("portero",),
                     confirmed_roles=("portero",),
                     constraints=("disponibilidad los domingos",), vector=[1.0, 0.0])
    open_role = project(20, category="Deportivo", roles=("portero",),
                        confirmed_roles=("portero",), vector=[0.0, 1.0])
    policy = RankingPolicy(eligibility=EligibilityPolicy(
        strict_constraint_terms=frozenset({"disponibilidad los domingos"})))
    results = recommend_projects(person, [strict, open_role], context(10, 20), policy=policy)
    assert [item.event_id for item in results] == [20]
    assert any("portero" in line for line in results[0].explanation.strengths)


def test_games_equivalence_does_not_promote_learning_goal_or_ai_fact():
    person = user(skills=[fact("UE5"), fact("Blender", source="ai_unreviewed", confirmed=False)],
                  improvement=("Blender",))
    unreal = project(30, category="Videojuegos", required=("Unreal Engine 5",),
                     preferred=("Blender",))
    blender = project(31, category="Videojuegos", required=("Blender",))
    results = recommend_projects(person, [blender, unreal], context(30, 31))
    assert [item.event_id for item in results] == [30, 31]
    assert results[0].eligibility == "eligible"
    assert results[1].eligibility == "needs_review"
    assert any("Unreal Engine 5" in line for line in results[0].explanation.strengths)
    assert all("Blender" not in line for item in results
               for line in item.explanation.strengths)


def test_closed_owned_member_pending_and_private_events_are_excluded():
    person = user(skills=[fact("Python")])
    events = [
        project(1, required=("Python",)),
        project(2, required=("Python",), state="closed"),
        project(3, required=("Python",), owner=2),
        project(4, required=("Python",)),
        project(5, required=("Python",)),
        project(6, required=("Python",)),
        project(7, required=("Secreto",)),
        project(8, required=("Python",), roster=[
            Participant(user_id=2, role="Integrante", confirmed=True)]),
    ]
    prepared = context(1, 2, 3, 4, 5, 6, 8, members=(4,),
                       invitations=(5,), applications=(6,))
    results = recommend_projects(person, events, prepared)
    assert [item.event_id for item in results] == [1]
    assert "Secreto" not in str(results)
    assert "Integrante" not in str(results)


def test_unknowns_insufficient_embeddings_and_stable_ties_top_n():
    person = user(skills=[fact("Python")], vector=[1.0, 0.0], model="other")
    unknown = project(5, required=("Blender",), roster=None, state="unknown",
                      vector=[1.0, 0.0])
    first = project(9, required=("Python",))
    second = project(7, required=("Python",))
    prepared = context(5, 7, 9)
    one = recommend_projects(person, [unknown, first, second], prepared, top_n=2)
    two = recommend_projects(person, [second, first, unknown], prepared, top_n=2)
    assert [item.event_id for item in one] == [7, 9]
    assert one == two
    all_results = recommend_projects(person, [unknown, first, second], prepared)
    assert all_results[-1].event_id == 5
    assert all_results[-1].eligibility == "needs_review"
    assert all_results[-1].evidence_group == "insufficient_evidence"
    assert any("embeddings comparables" in line
               for line in all_results[-1].explanation.unknowns)
    assert recommend_projects(person, [], context()) == []


def test_eligibility_and_evidence_sufficiency_are_separate_labels():
    person = user(skills=[fact("Python"), fact("Docker")])
    eligible_without_evidence = project(11, category="General")
    review_with_evidence = project(12, required=("Python",), preferred=("Docker",),
                                   state="unknown")
    results = recommend_projects(person, [review_with_evidence, eligible_without_evidence],
                                 context(11, 12))
    assert [(item.event_id, item.eligibility, item.evidence_group) for item in results] == [
        (11, "eligible", "insufficient_evidence"),
        (12, "needs_review", "sufficient_evidence"),
    ]


def test_privacy_authorization_and_public_projection():
    person = user(skills=[fact("Python")], vector=[1.0, 0.0])
    visible = project(1, required=("Python",), vector=[1.0, 0.0])
    private = project(2, required=("Proyecto reservado",))
    results = recommend_projects(person, [private, visible], context(1))
    assert [item.event_id for item in results] == [1]
    payload = str([item.model_dump() for item in results])
    for secret in ("private:92", "source_ref", "ranking_score", "score_components",
                   "profile_embedding", "event_embedding", "Proyecto reservado"):
        assert secret not in payload
    with pytest.raises(PermissionError, match="No se autorizó"):
        recommend_projects(person, [visible], context(1, actor=99))
    with pytest.raises(PermissionError, match="No se autorizó"):
        recommend_projects(person, [visible], context(1, consent=False))
    with pytest.raises(PermissionError, match="No se autorizó"):
        recommend_projects(user(visibility="hidden"), [visible], context(1))
    with pytest.raises(ValidationError):
        UserRecommendationContext(authenticated_user_id=2, discovery_consent=True,
                                  discoverable_event_ids=frozenset({1}))


def test_invalid_snapshot_duplicate_ids_and_top_n_are_rejected():
    person = user(skills=[])
    same = project(10)
    prepared = context(10)
    with pytest.raises(ValueError, match="únicos"):
        recommend_projects(person, [same, same], prepared)
    with pytest.raises(ValueError, match="top_n"):
        recommend_projects(person, [same], prepared, top_n=0)
    with pytest.raises(ValueError, match="top_n"):
        recommend_projects(person, [same], prepared, top_n=True)
    with pytest.raises(ValidationError):
        context(0)
