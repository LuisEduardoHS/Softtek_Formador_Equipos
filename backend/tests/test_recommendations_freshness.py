"""Pure snapshot and action checks for both recommendation audiences."""

import pytest
from pydantic import ValidationError

from app.services.ai.matching.policy import RankingPolicy
from app.services.ai.matching.schemas import CandidateInput, EventInput, Evidence, Participant
from app.services.ai.recommendations import (
    ActionRecord, OrganizerRecommendationContext, SourceVersions,
    UserRecommendationContext, assess_freshness, build_snapshot_fingerprint,
    classify_pair_records, context_action_state, is_repeated_recommendation,
    recommend_candidates, recommend_projects, same_action_pair,
)


def fact(value, *, source="user_declared", polarity="affirms"):
    return Evidence(source=source, kind="skill", value=value, polarity=polarity,
                    confirmed=True, source_ref="secret:record")


def prepared():
    event = EventInput(
        event_id=20, creator_id=1, state="open", participants=[], outstanding_roles=[],
        explicit_constraints=[],
        requirements={"categoria": "Académico", "habilidades_obligatorias": ["Python"]},
        confirmed_requirements=[fact("Python", source="organizer_confirmed")],
        event_embedding=[1.0, 0.0], embedding_model="fixture",
        embedding_source_version="pipeline-v1",
    )
    candidate = CandidateInput(
        user_id=2, visibility="visible", account_state="active",
        declared_skills=[fact("Python")], role_preferences=[], availability=[],
        profile={"habilidades": [], "intereses": [], "areas_mejora": ["Kubernetes"],
                 "resumen_publico": "Nombre reservado Ana"},
        profile_embedding=[1.0, 0.0], embedding_model="fixture",
        embedding_source_version="pipeline-v1",
    )
    organizer = OrganizerRecommendationContext(
        authenticated_organizer_id=1, authorized_event_id=20,
        discoverable_candidate_ids=frozenset({2}), confirmed_member_ids=frozenset(),
        pending_candidate_ids=frozenset(),
    )
    user = UserRecommendationContext(
        authenticated_user_id=2, discovery_consent=True,
        discoverable_event_ids=frozenset({20}), confirmed_member_event_ids=frozenset(),
        pending_invitation_event_ids=frozenset(),
        pending_application_event_ids=frozenset(),
    )
    policy = RankingPolicy()
    versions = SourceVersions(
        profile="profile-v1", event="event-v1", team="team-v1", access="access-v1",
        actions="actions-v1", profile_embedding="profile-vector-v1",
        event_embedding="event-vector-v1", profile_embedding_source="profile-v1",
        event_embedding_source="event-v1",
    )
    return event, candidate, organizer, user, policy, versions


def recommendations(event, candidate, organizer, user):
    return (recommend_candidates(event, [candidate], organizer)[0],
            recommend_projects(candidate, [event], user)[0])


def stamp(item, event, candidate, context, versions, policy, *, team_members=None,
          action_records=None):
    return build_snapshot_fingerprint(item, candidate, event, context, versions, policy,
                                      team_members=team_members,
                                      action_records=action_records)


def test_identical_complete_snapshots_repeat_for_both_audiences_without_raw_data():
    event, candidate, organizer, user, policy, versions = prepared()
    organizer_item, user_item = recommendations(event, candidate, organizer, user)
    for item, context in ((organizer_item, organizer), (user_item, user)):
        first = stamp(item, event, candidate, context, versions, policy)
        second = stamp(item, event.model_copy(deep=True), candidate.model_copy(deep=True),
                       context, versions, policy)
        assert assess_freshness(first, second).status == "current"
        assert is_repeated_recommendation(first, second) is True
        payload = repr(first)
        for private in ("Python", "Kubernetes", "Ana", "secret:record", "[1.0"):
            assert private not in payload
    assert same_action_pair(organizer_item, user_item, right_user_id=2)
    assert is_repeated_recommendation(
        stamp(organizer_item, event, candidate, organizer, versions, policy),
        stamp(user_item, event, candidate, user, versions, policy),
    ) is False


def test_profile_event_team_and_embedding_changes_are_stale():
    event, candidate, organizer, _, policy, versions = prepared()
    item = recommend_candidates(event, [candidate], organizer)[0]
    old = stamp(item, event, candidate, organizer, versions, policy)

    changed_profile = candidate.model_copy(deep=True)
    changed_profile.declared_skills.append(fact("Docker"))
    assert "profile" in assess_freshness(
        old, stamp(item, event, changed_profile, organizer, versions, policy)
    ).changed

    changed_event = event.model_copy(deep=True)
    changed_event.requirements.habilidades_deseables.append("Docker")
    assert "event" in assess_freshness(
        old, stamp(item, changed_event, candidate, organizer, versions, policy)
    ).changed

    changed_team = event.model_copy(deep=True)
    changed_team.participants = [Participant(user_id=3, role="analista", confirmed=True)]
    team_member = CandidateInput(user_id=3, visibility="visible", account_state="active",
                                 declared_skills=[fact("SQL")])
    assert "team" in assess_freshness(
        old, stamp(item, changed_team, candidate, organizer, versions, policy,
                   team_members={3: team_member})
    ).changed

    changed_vector = candidate.model_copy(deep=True)
    changed_vector.profile_embedding = [0.0, 1.0]
    assert "profile_embedding" in assess_freshness(
        old, stamp(item, event, changed_vector, organizer, versions, policy)
    ).changed
    changed_event_vector = event.model_copy(deep=True)
    changed_event_vector.event_embedding = [0.0, 1.0]
    assert "event_embedding" in assess_freshness(
        old, stamp(item, changed_event_vector, candidate, organizer, versions, policy)
    ).changed


def test_revisions_policy_access_and_pending_actions_invalidate_both_sides():
    event, candidate, organizer, user, policy, versions = prepared()
    organizer_item, user_item = recommendations(event, candidate, organizer, user)
    old_org = stamp(organizer_item, event, candidate, organizer, versions, policy)
    old_user = stamp(user_item, event, candidate, user, versions, policy)

    revision_changed = versions.model_copy(update={"profile": "profile-v2",
                                           "profile_embedding_source": "profile-v2"})
    assert "profile" in assess_freshness(
        old_org, stamp(organizer_item, event, candidate, organizer, revision_changed, policy)
    ).changed
    new_policy = RankingPolicy(version="policy-v2")
    policy_snapshot = stamp(organizer_item, event, candidate, organizer, versions, new_policy)
    assert "policy" in assess_freshness(old_org, policy_snapshot).changed
    assert is_repeated_recommendation(policy_snapshot, policy_snapshot) is False

    hidden = organizer.model_copy(update={"discoverable_candidate_ids": frozenset()})
    assert "access" in assess_freshness(
        old_org, stamp(organizer_item, event, candidate, hidden, versions, policy)
    ).changed
    pending = organizer.model_copy(update={"pending_candidate_ids": frozenset({2})})
    assert context_action_state(organizer_item, pending, event) == "pending"
    assert "actions" in assess_freshness(
        old_org, stamp(organizer_item, event, candidate, pending, versions, policy)
    ).changed

    invited = user.model_copy(update={"pending_invitation_event_ids": frozenset({20})})
    applied = user.model_copy(update={"pending_application_event_ids": frozenset({20})})
    assert context_action_state(user_item, invited, event) == "pending_invitation"
    assert context_action_state(user_item, applied, event) == "pending_application"
    assert "actions" in assess_freshness(
        old_user, stamp(user_item, event, candidate, invited, versions, policy)
    ).changed
    member = user.model_copy(update={"confirmed_member_event_ids": frozenset({20})})
    assert context_action_state(user_item, member, event) == "member"
    assert "actions" in assess_freshness(
        old_user, stamp(user_item, event, candidate, member, versions, policy)
    ).changed


def test_request_record_and_member_skill_changes_alter_fingerprint():
    event, candidate, organizer, _, policy, versions = prepared()
    item = recommend_candidates(event, [candidate], organizer)[0]
    first = stamp(item, event, candidate, organizer, versions, policy, action_records=[])
    invitation = ActionRecord(event_id=20, sender_id=1, recipient_id=2, state="Pendiente")
    second = stamp(item, event, candidate, organizer, versions, policy,
                   action_records=[invitation])
    assert "actions" in assess_freshness(first, second).changed

    roster = event.model_copy(deep=True)
    roster.participants = [Participant(user_id=3, role="analista", confirmed=True)]
    member = CandidateInput(user_id=3, visibility="visible", account_state="active",
                            declared_skills=[fact("SQL")])
    old_team = stamp(item, roster, candidate, organizer, versions, policy,
                     team_members={3: member})
    improved = member.model_copy(deep=True)
    improved.declared_skills.append(fact("Docker"))
    new_team = stamp(item, roster, candidate, organizer, versions, policy,
                     team_members={3: improved})
    assert "team" in assess_freshness(old_team, new_team).changed


def test_missing_metadata_or_incomplete_team_yields_unknown_not_current():
    event, candidate, organizer, _, policy, versions = prepared()
    item = recommend_candidates(event, [candidate], organizer)[0]
    complete = stamp(item, event, candidate, organizer, versions, policy)
    for missing in ("profile", "event", "team", "access", "actions",
                    "profile_embedding", "event_embedding", "profile_embedding_source"):
        incomplete = versions.model_copy(update={missing: None})
        report = assess_freshness(complete, stamp(item, event, candidate, organizer,
                                                  incomplete, policy))
        assert report.status == "unknown", missing
        assert is_repeated_recommendation(complete, stamp(
            item, event, candidate, organizer, incomplete, policy
        )) is None

    roster_unknown = event.model_copy(deep=True)
    roster_unknown.participants = None
    report = assess_freshness(
        complete, stamp(item, roster_unknown, candidate, organizer, versions, policy)
    )
    assert report.status == "unknown"
    assert "team" in report.unknown
    newer_team = versions.model_copy(update={"team": "team-v2"})
    changed_report = assess_freshness(
        complete, stamp(item, roster_unknown, candidate, organizer, newer_team, policy)
    )
    assert changed_report.status == "stale"
    assert "team" in changed_report.changed


def test_stale_embedding_source_is_detected_even_against_identical_snapshot():
    event, candidate, organizer, _, policy, versions = prepared()
    item = recommend_candidates(event, [candidate], organizer)[0]
    old = stamp(item, event, candidate, organizer, versions, policy)
    outdated = versions.model_copy(update={"profile": "profile-v2"})
    current = stamp(item, event, candidate, organizer, outdated, policy)
    report = assess_freshness(old, current)
    assert report.status == "stale"
    assert "profile_embedding" in report.changed
    assert is_repeated_recommendation(current, current) is False


def test_confirmed_absence_of_embeddings_is_not_missing_metadata():
    event, candidate, organizer, _, policy, versions = prepared()
    event = event.model_copy(deep=True)
    candidate = candidate.model_copy(deep=True)
    event.event_embedding = None
    event.embedding_model = None
    event.embedding_source_version = None
    candidate.profile_embedding = None
    candidate.embedding_model = None
    candidate.embedding_source_version = None
    known_absence = versions.model_copy(update={
        "profile_embedding": "absent-profile-v1", "event_embedding": "absent-event-v1",
    })
    item = recommend_candidates(event, [candidate], organizer)[0]
    first = stamp(item, event, candidate, organizer, known_absence, policy)
    second = stamp(item, event, candidate, organizer, known_absence, policy)
    assert assess_freshness(first, second).status == "current"


def test_real_request_directions_states_and_membership_are_conservative():
    event, _, _, _, _, _ = prepared()
    invitation = ActionRecord(event_id=20, sender_id=1, recipient_id=2, state="Pendiente")
    application = ActionRecord(event_id=20, sender_id=2, recipient_id=1, state="pending")
    assert classify_pair_records(event, 2, [invitation]) == "pending_invitation"
    assert classify_pair_records(event, 2, [application]) == "pending_application"
    assert classify_pair_records(event, 2, [invitation, application]) == "pending_both"
    assert classify_pair_records(event, 2, []) == "available"
    assert classify_pair_records(event, 2, None) == "unknown"
    assert classify_pair_records(event, 2, [ActionRecord(
        event_id=20, sender_id=1, recipient_id=2, state="Aceptada"
    )]) == "unknown"
    assert classify_pair_records(event, 2, [ActionRecord(
        event_id=20, sender_id=1, recipient_id=2, state="Rechazada"
    )]) == "available"
    joined = event.model_copy(deep=True)
    joined.participants = [Participant(user_id=2, role="programador", confirmed=True)]
    assert classify_pair_records(joined, 2, [invitation]) == "member"


def test_pair_deduplication_validation_and_incomplete_sources():
    event, candidate, organizer, user, policy, versions = prepared()
    organizer_item, user_item = recommendations(event, candidate, organizer, user)
    assert same_action_pair(organizer_item, organizer_item)
    assert same_action_pair(organizer_item, user_item, right_user_id=2)
    with pytest.raises(ValueError):
        same_action_pair(user_item, organizer_item)
    with pytest.raises(ValueError):
        SourceVersions(profile="ana@example.com")
    with pytest.raises(ValidationError):
        ActionRecord(event_id=0, sender_id=1, recipient_id=2, state="Pendiente")
    with pytest.raises(PermissionError):
        stamp(organizer_item, event, candidate, user, versions, policy)
    other = organizer_item.model_copy(update={"candidate_id": 99})
    with pytest.raises(ValueError):
        stamp(other, event, candidate, organizer, versions, policy)
