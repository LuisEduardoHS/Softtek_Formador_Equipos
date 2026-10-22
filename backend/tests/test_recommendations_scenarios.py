"""Cross-service scenarios over prepared, authorized snapshots (no database)."""

import json

from app.services.ai.matching.eligibility import EligibilityPolicy
from app.services.ai.matching.policy import RankingPolicy
from app.services.ai.matching.schemas import CandidateInput, EventInput, Evidence, Participant
from app.services.ai.recommendations import (
    ActionRecord, OrganizerRecommendationContext, SourceVersions,
    UserRecommendationContext, assess_freshness, build_snapshot_fingerprint,
    classify_pair_records, context_action_state, is_repeated_recommendation,
    personalize_recommendation, recommend_candidates, recommend_projects,
    same_action_pair,
)


def fact(value, kind="skill", *, source="user_declared", polarity="affirms",
         confirmed=True):
    return Evidence(value=value, kind=kind, source=source, polarity=polarity,
                    confirmed=confirmed, source_ref="private:record")


def person(user_id=2, *, skills=(), availability=(), improvement=(),
           visibility="visible", vector=None, model="fixture"):
    return CandidateInput(
        user_id=user_id, visibility=visibility, account_state="active",
        declared_skills=list(skills), role_preferences=[], availability=list(availability),
        profile={"habilidades": [], "intereses": [], "areas_mejora": list(improvement),
                 "resumen_publico": "Nombre privado Ana"},
        profile_embedding=vector,
        embedding_model=model if vector is not None else None,
        embedding_source_version="pipeline-v1" if vector is not None else None,
    )


def event(event_id, *, category="Académico", required=(), preferred=(), roles=(),
          open_roles=(), constraints=(), participants=(), state="open", creator=1,
          vector=None, model="fixture"):
    return EventInput(
        event_id=event_id, creator_id=creator, state=state,
        requirements={"categoria": category, "habilidades_obligatorias": list(required),
                      "habilidades_deseables": list(preferred), "roles_buscados": list(roles),
                      "restricciones_explicitas": list(constraints)},
        confirmed_requirements=[fact(term, source="organizer_confirmed")
                                for term in (*required, *preferred)],
        outstanding_roles=[fact(term, "role", source="organizer_confirmed")
                           for term in open_roles],
        explicit_constraints=[fact(term, "constraint", source="organizer_confirmed")
                              for term in constraints],
        participants=None if participants is None else list(participants),
        event_embedding=vector,
        embedding_model=model if vector is not None else None,
        embedding_source_version="pipeline-v1" if vector is not None else None,
    )


def organizer_context(event_id, *, visible=(2,), members=(), pending=(), creator=1):
    return OrganizerRecommendationContext(
        authenticated_organizer_id=creator, authorized_event_id=event_id,
        discoverable_candidate_ids=frozenset(visible),
        confirmed_member_ids=frozenset(members),
        pending_candidate_ids=frozenset(pending),
    )


def user_context(*event_ids, user_id=2, members=(), invitations=(), applications=()):
    return UserRecommendationContext(
        authenticated_user_id=user_id, discovery_consent=True,
        discoverable_event_ids=frozenset(event_ids),
        confirmed_member_event_ids=frozenset(members),
        pending_invitation_event_ids=frozenset(invitations),
        pending_application_event_ids=frozenset(applications),
    )


def versions():
    return SourceVersions(
        profile="profile-v1", event="event-v1", team="team-v1", access="access-v1",
        actions="actions-v1", profile_embedding="profile-vector-v1",
        event_embedding="event-vector-v1", profile_embedding_source="profile-v1",
        event_embedding_source="event-v1",
    )


def stamp(item, candidate, project, context, revisions=None, *, policy=None,
          team_members=None):
    return build_snapshot_fingerprint(
        item, candidate, project, context, revisions or versions(),
        policy or RankingPolicy(), team_members=team_members, action_records=[],
    )


def test_academic_bidirectional_ranking_evidence_duplicates_and_private_projection():
    project = event(20, required=("Python",), preferred=("Docker",), vector=[1.0, 0.0])
    qualified = person(skills=(fact("Python"), fact("Docker")), vector=[1.0, 0.0],
                       improvement=("Kubernetes",))
    uncertain = person(3, skills=(fact("Python", polarity="denies"),),
                       improvement=("Docker",))
    hidden = person(4, skills=(fact("Python"),), visibility="hidden")
    org = organizer_context(20, visible=(2, 3, 4))
    candidates = recommend_candidates(project, [uncertain, hidden, qualified], org)
    assert [item.candidate_id for item in candidates] == [2, 3]
    assert candidates[0].eligibility == "eligible"
    assert candidates[1].eligibility == "needs_review"
    assert any("Python" in line for line in candidates[0].explanation.strengths)
    assert all("Docker" not in line for line in candidates[1].explanation.strengths)

    basic = event(10, required=("Python",))
    projects = recommend_projects(qualified, [basic, project], user_context(10, 20))
    assert [item.event_id for item in projects] == [20, 10]
    assert same_action_pair(candidates[0], projects[0], right_user_id=2)
    org_stamp = stamp(candidates[0], qualified, project, org)
    user_stamp = stamp(projects[0], qualified, project, user_context(10, 20))
    assert assess_freshness(org_stamp, org_stamp).status == "current"
    assert assess_freshness(user_stamp, user_stamp).status == "current"
    assert is_repeated_recommendation(org_stamp, org_stamp) is True
    assert is_repeated_recommendation(org_stamp, user_stamp) is False
    public = json.dumps([item.model_dump() for item in (*candidates, *projects)])
    for secret in ("Nombre privado", "private:record", "Kubernetes", "profile_embedding",
                   "ranking_score", "score_components", "candidate_id\": 4"):
        assert secret not in public


def test_sports_vacancy_strict_sunday_conflict_and_covered_role():
    project = event(30, category="Deportivo", roles=("portero",),
                    open_roles=("portero",), constraints=("disponibilidad los domingos",),
                    vector=[1.0, 0.0])
    available = person(skills=(fact("portero"),), availability=(
        fact("disponibilidad los domingos", "availability"),))
    conflicting = person(3, skills=(fact("portero"),), availability=(
        fact("domingos", "availability", polarity="denies"),), vector=[1.0, 0.0])
    policy = RankingPolicy(eligibility=EligibilityPolicy(
        strict_constraint_terms=frozenset({"disponibilidad los domingos"})))
    org = organizer_context(30, visible=(2, 3, 4), members=(4,))
    candidates = recommend_candidates(project, [conflicting, available,
                                                 person(4, skills=(fact("portero"),))],
                                      org, policy=policy)
    assert [item.candidate_id for item in candidates] == [2]
    assert any("portero" in line for line in candidates[0].explanation.strengths)
    assert [item.event_id for item in recommend_projects(
        conflicting, [project], user_context(30, user_id=3), policy=policy)] == []
    assert [item.event_id for item in recommend_projects(
        available, [project], user_context(30), policy=policy)] == [30]

    covered = project.model_copy(update={
        "participants": [Participant(user_id=4, role="portero", confirmed=True)],
        "outstanding_roles": [],
    })
    covered_result = recommend_candidates(covered, [available], org, policy=policy,
                                          team_members={4: person(4, skills=(fact("portero"),))})
    assert len(covered_result) == 1
    assert all("rol solicitado: portero" not in line.lower()
               for line in covered_result[0].explanation.strengths)


def test_games_equivalence_unknown_skill_and_general_filters_in_both_directions():
    games = event(40, category="Videojuegos", required=("Unreal Engine 5",),
                  preferred=("Blender",), vector=[1.0, 0.0])
    developer = person(skills=(fact("UE5"), fact("Blender", source="ai_unreviewed",
                                               confirmed=False)),
                       improvement=("Blender",), vector=[1.0, 0.0])
    other = person(3, skills=(), improvement=("Unreal Engine 5",))
    org = organizer_context(40, visible=(2, 3, 4), pending=(4,))
    results = recommend_candidates(games, [other, developer, person(4)], org)
    assert [item.candidate_id for item in results] == [2, 3]
    assert results[0].eligibility == "eligible"
    assert results[1].eligibility == "needs_review"
    assert any("Unreal Engine 5" in line for line in results[0].explanation.strengths)
    assert all("Blender" not in line for line in results[0].explanation.strengths)

    closed = event(41, category="General", state="closed")
    own = event(42, category="General", creator=2)
    member = event(43, category="General", participants=(
        Participant(user_id=2, role="integrante", confirmed=True),))
    invited = event(44, category="General")
    private = event(45, category="General", required=("Secreto interno",))
    visible = event(46, category="General", required=("Python",), participants=None)
    context = user_context(40, 41, 42, 43, 44, 46, invitations=(44,))
    projects = recommend_projects(developer, [private, invited, member, own, closed,
                                              visible, games], context)
    assert [item.event_id for item in projects] == [40, 46]
    assert projects[1].eligibility == "needs_review"
    assert projects[1].evidence_group == "insufficient_evidence"
    assert "Secreto interno" not in repr(projects)
    assert recommend_projects(developer, [games], user_context(40, members=(40,))) == []


def test_freshness_profile_embedding_model_missing_metadata_and_changed_access():
    project = event(50, required=("Python",), vector=[1.0, 0.0])
    candidate = person(skills=(fact("Python"),), vector=[1.0, 0.0])
    org = organizer_context(50)
    user = user_context(50)
    org_item = recommend_candidates(project, [candidate], org)[0]
    user_item = recommend_projects(candidate, [project], user)[0]
    for item, context in ((org_item, org), (user_item, user)):
        old = stamp(item, candidate, project, context)
        assert assess_freshness(old, stamp(item, candidate, project, context)).status == "current"
        changed_profile = candidate.model_copy(update={
            "declared_skills": [fact("Python"), fact("Docker")]})
        report = assess_freshness(old, stamp(item, changed_profile, project, context))
        assert report.status == "stale" and "profile" in report.changed
        changed_model = candidate.model_copy(update={"embedding_model": "fixture-v2"})
        report = assess_freshness(old, stamp(item, changed_model, project, context))
        assert report.status == "stale" and "profile_embedding" in report.changed
        no_revision = versions().model_copy(update={"event_embedding": None})
        report = assess_freshness(old, stamp(item, candidate, project, context, no_revision))
        assert report.status == "unknown" and "event_embedding" in report.unknown
        assert is_repeated_recommendation(old, stamp(item, candidate, project,
                                                     context, no_revision)) is None
        if context is org:
            revoked = org.model_copy(update={"discoverable_candidate_ids": frozenset()})
            assert recommend_candidates(project, [candidate], revoked) == []
        else:
            revoked = user.model_copy(update={"discoverable_event_ids": frozenset()})
            assert recommend_projects(candidate, [project], revoked) == []
        report = assess_freshness(old, stamp(item, candidate, project, revoked))
        assert report.status == "stale" and "access" in report.changed


def test_recompute_after_snapshot_change_before_invitation_or_application():
    project = event(60, required=("Python",))
    candidate = person(skills=(fact("Python"),))
    org = organizer_context(60)
    user = user_context(60)
    org_item = recommend_candidates(project, [candidate], org)[0]
    user_item = recommend_projects(candidate, [project], user)[0]
    old_org = stamp(org_item, candidate, project, org)
    old_user = stamp(user_item, candidate, project, user)

    # Time of use: the project closed and an invitation was created after ranking.
    closed = project.model_copy(update={"state": "closed"})
    pending_org = org.model_copy(update={"pending_candidate_ids": frozenset({2})})
    pending_user = user.model_copy(update={"pending_invitation_event_ids": frozenset({60})})
    assert assess_freshness(old_org, stamp(org_item, candidate, closed, pending_org)).status == "stale"
    assert assess_freshness(old_user, stamp(user_item, candidate, closed, pending_user)).status == "stale"
    assert context_action_state(org_item, pending_org, closed) == "pending"
    assert context_action_state(user_item, pending_user, closed) == "pending_invitation"
    assert classify_pair_records(closed, 2, [ActionRecord(
        event_id=60, sender_id=1, recipient_id=2, state="Pendiente")]) == "pending_invitation"
    assert recommend_candidates(closed, [candidate], pending_org) == []
    assert recommend_projects(candidate, [closed], pending_user) == []

    # A roster update alone also invalidates the earlier result.
    joined = project.model_copy(update={
        "participants": [Participant(user_id=2, role="integrante", confirmed=True)]})
    assert assess_freshness(old_org, stamp(
        org_item, candidate, joined, org, team_members={2: candidate})).status == "stale"
    assert recommend_candidates(joined, [candidate], org) == []
    assert recommend_projects(candidate, [joined], user) == []


class HallucinatingLlama:
    def __init__(self):
        self.prompts = []

    def generate_structured(self, prompt, schema):
        self.prompts.append(prompt)
        return json.dumps({"strengths": [{"fact_id": "s0", "variant": 1,
                                          "invented_skill": "Kubernetes"}],
                           "gaps": [], "unknowns": []})


def test_llama_fallback_cannot_change_order_eligibility_or_private_facts():
    project = event(70, required=("Python",))
    best = person(skills=(fact("Python"),), improvement=("Kubernetes",))
    unknown = person(3, skills=())
    org = organizer_context(70, visible=(2, 3))
    ordered = recommend_candidates(project, [unknown, best], org)
    generator = HallucinatingLlama()
    enriched = [personalize_recommendation(item, use_llm=True, ai=generator)
                for item in ordered]
    assert enriched == ordered
    assert [item.candidate_id for item in enriched] == [2, 3]
    assert [item.eligibility for item in enriched] == ["eligible", "needs_review"]
    user_items = recommend_projects(best, [project], user_context(70))
    assert [personalize_recommendation(item, use_llm=True, ai=generator)
            for item in user_items] == user_items
    assert generator.prompts
    assert all("Kubernetes" not in prompt and "Nombre privado" not in prompt
               and "Python" not in prompt and "private:record" not in prompt
               for prompt in generator.prompts)
