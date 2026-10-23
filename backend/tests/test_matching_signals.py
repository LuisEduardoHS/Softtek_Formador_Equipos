import math

import pytest

from app.services.ai.matching.complementarity import assess_team_gaps, complementarity_score
from app.services.ai.matching.normalization import EquivalenceCatalog
from app.services.ai.matching.schemas import CandidateInput, EventInput, Evidence, Participant
from app.services.ai.matching.similarity import InvalidEmbeddingError, cosine_similarity


def fact(value, kind="skill", source="user_declared", polarity="affirms", confirmed=True):
    return Evidence(value=value, kind=kind, source=source,
                    polarity=polarity, confirmed=confirmed)


def person(user_id, skills=None, *, profile=None, visibility="visible", roles=None):
    return CandidateInput(user_id=user_id, declared_skills=skills,
                          profile=profile, visibility=visibility, role_preferences=roles)


def project(*, category="Académico", required=(), preferred=(), roles=(),
            confirmed_skills=(), open_roles=None, participants=()):
    return EventInput(
        event_id=10, creator_id=1, state="open",
        requirements={"categoria": category,
                      "habilidades_obligatorias": list(required),
                      "habilidades_deseables": list(preferred),
                      "roles_buscados": list(roles)},
        confirmed_requirements=[fact(term, source="organizer_confirmed")
                                for term in confirmed_skills],
        outstanding_roles=None if open_roles is None else [
            fact(term, "role", "organizer_confirmed") for term in open_roles
        ],
        participants=None if participants is None else list(participants),
    )


def cosine(a, b, *, models=("fixture-v1", "fixture-v1"), versions=("rev1", "rev1")):
    return cosine_similarity(a, b, left_model=models[0], right_model=models[1],
                             left_version=versions[0], right_version=versions[1])


def test_identical_orthogonal_and_opposite_vectors():
    assert cosine([3.0, 4.0], [3.0, 4.0]) == pytest.approx(1.0)
    assert cosine([1.0, 0.0], [0.0, 1.0]) == pytest.approx(0.0)
    assert cosine([1.0, 0.0], [-1.0, 0.0]) == pytest.approx(-1.0)


def test_missing_or_incompatible_embeddings_are_unknown_not_zero():
    assert cosine(None, [1.0, 0.0]) is None
    assert cosine([1.0, 0.0], [1.0]) is None
    assert cosine([1.0], [1.0], models=("model-a", "model-b")) is None
    assert cosine([1.0], [1.0], versions=("rev1", "rev2")) is None
    assert cosine_similarity([1.0], [1.0], left_model=None, right_model="fixture",
                             left_version="rev1", right_version="rev1") is None
    assert cosine([1.0], [1.0], models=("nomic-embed-text", "nomic-embed-text")) is None


@pytest.mark.parametrize("bad", [[], [0.0, 0.0], [float("nan")],
                                       [float("inf")], [True], ["1"]])
def test_malformed_embedding_raises_controlled_error(bad):
    with pytest.raises(InvalidEmbeddingError):
        cosine(bad, [1.0] * len(bad))


def test_large_finite_vectors_remain_numerically_stable():
    assert math.isfinite(cosine([1e150, 1e150], [1e150, -1e150]))


def test_sports_role_covered_vs_confirmed_vacancy():
    roster = [Participant(user_id=3, role="portero", confirmed=True)]
    match = project(category="Deportivo", roles=["portero"], open_roles=["portero"],
                    participants=roster)
    covered = assess_team_gaps(match)
    assert covered.open_roles == ()
    keeper = person(2, [fact("portero")])
    assert complementarity_score(match, keeper, covered).coverage is None

    vacant = project(category="Deportivo", roles=["portero"], open_roles=["portero"])
    gaps = assess_team_gaps(vacant)
    assert gaps.open_roles == ("portero",)
    assert complementarity_score(vacant, keeper, gaps).filled_roles == ("portero",)
    assert complementarity_score(vacant, keeper, gaps).coverage == 1
    interested = person(4, [], roles=[fact("portero", "role_preference")])
    assert complementarity_score(vacant, interested, gaps).coverage == 0


def test_academic_required_gap_credits_new_capacity_not_redundancy():
    event = project(required=["Python", "Docker"], confirmed_skills=["Python", "Docker"],
                    participants=[Participant(user_id=3, role=None, confirmed=True)])
    team = {3: person(3, [fact("Python")])}
    gaps = assess_team_gaps(event, team)
    assert gaps.missing_required_skills == ("Docker",)
    redundant = complementarity_score(event, person(4, [fact("Python")]), gaps)
    useful = complementarity_score(event, person(5, [fact("Docker")]), gaps)
    assert redundant.coverage == 0
    assert useful.coverage == 1
    assert useful.filled_required_skills == ("Docker",)


def test_game_jam_uses_only_catalogued_ue5_equivalence_and_confirmed_skills():
    event = project(category="Competencia", required=["Unreal Engine 5"],
                    confirmed_skills=["Unreal Engine 5"])
    gaps = assess_team_gaps(event)
    assert gaps.missing_required_skills == ("Unreal Engine 5",)
    assert complementarity_score(event, person(2, [fact("UE5")]), gaps).coverage == 1
    assert complementarity_score(event, person(3, [fact("Unreal Engine")]), gaps).coverage == 0
    no_alias = EquivalenceCatalog(version="without-ue5", aliases={})
    assert complementarity_score(event, person(2, [fact("UE5")]),
                                 assess_team_gaps(event, catalog=no_alias), no_alias).coverage == 0


def test_interests_areas_mejora_unreviewed_and_negated_skills_give_no_credit():
    event = project(required=["Python"], confirmed_skills=["Python"])
    gaps = assess_team_gaps(event)
    profile = {"habilidades": [], "intereses": ["Python"], "areas_mejora": ["Python"],
               "resumen_publico": ""}
    assert complementarity_score(event, person(2, [], profile=profile), gaps).coverage == 0
    pending = person(3, [fact("Python", source="ai_unreviewed", confirmed=False)])
    denied = person(4, [fact("Python", polarity="denies")])
    assert complementarity_score(event, pending, gaps).coverage == 0
    assert complementarity_score(event, denied, gaps).coverage == 0


def test_unknown_roster_and_member_data_do_not_invent_skill_gaps():
    unknown = project(required=["Python"], confirmed_skills=["Python"], participants=None)
    assert assess_team_gaps(unknown) is None
    assert complementarity_score(unknown, person(2, [fact("Python")]), None) is None
    partial = project(required=["Python"], confirmed_skills=["Python"],
                      participants=[Participant(user_id=3, role=None, confirmed=False)])
    assert assess_team_gaps(partial) is None
    known_roster = project(required=["Python"], confirmed_skills=["Python"],
                           participants=[Participant(user_id=3, role=None, confirmed=True)])
    assert assess_team_gaps(known_roster).missing_required_skills is None
    assert assess_team_gaps(known_roster, {3: person(3, [], visibility="hidden")}).missing_required_skills is None


def test_unconfirmed_event_requirement_is_not_reported_as_missing():
    event = project(required=["Blender"], confirmed_skills=[])
    assert assess_team_gaps(event).missing_required_skills == ()
    assert complementarity_score(event, person(2, [fact("Blender")]),
                                 assess_team_gaps(event)).coverage is None
