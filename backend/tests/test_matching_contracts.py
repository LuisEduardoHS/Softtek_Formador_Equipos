import json

import pytest
from pydantic import ValidationError

from app.services.ai.matching.normalization import (
    DEFAULT_EQUIVALENCES,
    EquivalenceCatalog,
    apply_equivalence,
    normalize_term,
    validate_evidence,
)
from app.services.ai.matching.schemas import (
    CandidateInput,
    EventInput,
    Evidence,
    MatchRequest,
    MatchResult,
    RequirementAssessment,
)


def evidence(value="Python", *, kind="skill", source="user_declared", polarity="affirms",
             confirmed=True, source_ref="profile:1"):
    return {
        "source": source, "kind": kind, "value": value, "polarity": polarity,
        "confirmed": confirmed, "source_ref": source_ref,
    }


@pytest.mark.parametrize("category", ["Académico", "Deportivo", "Competencia", "Videojuegos", "Otro"])
def test_request_accepts_different_project_categories_without_inference(category):
    request = MatchRequest.model_validate({
        "event": {
            "event_id": 7, "creator_id": 2, "state": "open",
            "requirements": {"categoria": category, "roles_buscados": []},
            "confirmed_requirements": [], "participants": [],
        },
        "candidates": [{"user_id": 3, "visibility": "unknown"}],
        "policy_version": "phase4.v1", "top_n": 10,
    })
    assert request.event.requirements.categoria == category
    assert request.event.confirmed_requirements == []
    assert request.event.outstanding_roles is None
    assert request.candidates[0].declared_skills is None


def test_absent_empty_and_unreviewed_remain_distinct():
    absent = CandidateInput(user_id=1)
    empty = CandidateInput(user_id=2, declared_skills=[])
    unreviewed = CandidateInput(user_id=3, declared_skills=[evidence(
        "Python", source="ai_unreviewed", confirmed=False
    )])
    assert absent.declared_skills is None
    assert empty.declared_skills == []
    assert unreviewed.declared_skills[0].confirmed is False
    assert unreviewed.declared_skills[0].source == "ai_unreviewed"


def test_negation_is_evidence_not_a_positive_skill():
    candidate = CandidateInput(user_id=1, declared_skills=[evidence(
        "No sé Python", polarity="denies"
    )])
    assert candidate.declared_skills[0].polarity == "denies"
    assert candidate.declared_skills[0].value == "No sé Python"
    with pytest.raises(ValidationError):
        CandidateInput(user_id=1, declared_skills=[evidence(
            "No sé Python", polarity="affirms"
        )])
    with pytest.raises(ValidationError):
        CandidateInput(user_id=1, declared_skills=[evidence("Quiero aprender Python")])


def test_learning_goals_and_interests_cannot_enter_skill_evidence():
    for kind in ("learning_goal", "interest"):
        with pytest.raises(ValidationError):
            CandidateInput(user_id=1, declared_skills=[evidence("Python", kind=kind)])


def test_profile_learning_area_is_not_promoted_to_declared_skill():
    candidate = CandidateInput.model_validate({
        "user_id": 1,
        "profile": {"habilidades": [], "intereses": ["Robótica"],
                    "areas_mejora": ["Python"], "resumen_publico": ""},
    })
    assert candidate.profile.areas_mejora == ["Python"]
    assert candidate.declared_skills is None


def test_duplicates_are_removed_only_with_same_provenance_and_polarity():
    candidate = CandidateInput(user_id=1, declared_skills=[
        evidence(" UE5 "), evidence("Unreal Engine 5"),
        evidence("Unreal Engine 5", polarity="denies"),
        evidence("Unreal Engine 5", source_ref="profile:2"),
    ])
    assert len(candidate.declared_skills) == 3
    assert candidate.declared_skills[0].value == "UE5"


def test_normalization_preserves_symbols_and_uses_versioned_alias():
    assert normalize_term("  ÁRTE   3D  ") == "arte 3d"
    assert normalize_term("C++") != normalize_term("C#")
    assert apply_equivalence(" UE5 ") == apply_equivalence("Unreal Engine 5")
    assert DEFAULT_EQUIVALENCES.version == "2026-10-26.v4"
    assert apply_equivalence("fútbol") == "futbol"
    assert apply_equivalence("portero") != apply_equivalence("defensa")


def test_catalog_rejects_ambiguous_or_chained_equivalences():
    with pytest.raises(ValidationError):
        EquivalenceCatalog(version="v1", aliases={"UE5": "Unreal Engine 5", "ue5": "Otro"})
    with pytest.raises(ValidationError):
        EquivalenceCatalog(version="v1", aliases={"A": "B", "B": "C"})
    with pytest.raises(ValidationError):
        EquivalenceCatalog(version=" ", aliases={})


def test_evidence_validation_requires_explicit_provenance_and_polarity():
    assert validate_evidence(evidence()).kind == "skill"
    with pytest.raises(ValidationError):
        validate_evidence({"source": "user_declared", "value": "Python", "confirmed": True})
    with pytest.raises(ValidationError):
        validate_evidence(evidence(source="ai_unreviewed", confirmed=True))
    with pytest.raises(ValidationError):
        validate_evidence(evidence(value=" "))
    with pytest.raises((TypeError, ValidationError)):
        validate_evidence([evidence()])


@pytest.mark.parametrize("bad", [0, -1, True, "1"])
def test_identifiers_must_be_positive_integers(bad):
    with pytest.raises(ValidationError):
        CandidateInput(user_id=bad)
    with pytest.raises(ValidationError):
        EventInput(event_id=bad, creator_id=2)


def test_json_contract_rejects_unknown_fields_wrong_shapes_and_bad_states():
    with pytest.raises(ValidationError):
        MatchRequest.model_validate_json(json.dumps({
            "event": {"event_id": 1, "creator_id": 2, "state": "published"},
            "candidates": [], "policy_version": "v1",
        }))
    with pytest.raises(ValidationError):
        CandidateInput.model_validate({"user_id": 1, "declared_skills": {}, "extra": 1})
    with pytest.raises(ValidationError):
        CandidateInput.model_validate({"user_id": 1, "location": {"correo": "x@example.com"}})
    with pytest.raises(ValidationError):
        MatchRequest.model_validate({
            "event": {"event_id": 1, "creator_id": 2},
            "candidates": [{"user_id": 3}, {"user_id": 3}], "policy_version": "v1",
        })


def test_event_evidence_and_participants_are_validated():
    with pytest.raises(ValidationError):
        EventInput(event_id=1, creator_id=2, confirmed_requirements=[evidence(
            "Python", source="ai_unreviewed", confirmed=False
        )])
    with pytest.raises(ValidationError):
        EventInput(event_id=1, creator_id=2, outstanding_roles=[evidence("Python", kind="skill")])
    with pytest.raises(ValidationError):
        EventInput(event_id=1, creator_id=2, participants=[
            {"user_id": 3, "confirmed": True}, {"user_id": 3, "confirmed": False},
        ])


def test_optional_embeddings_require_metadata_and_valid_numbers():
    valid = CandidateInput(user_id=1, profile_embedding=[0.1] * 768,
                           embedding_model="nomic-embed-text", embedding_source_version="v1")
    assert len(valid.profile_embedding) == 768
    for payload in (
        {"profile_embedding": [0.1] * 3, "embedding_model": "nomic-embed-text", "embedding_source_version": "v1"},
        {"profile_embedding": [float("nan")], "embedding_model": "other", "embedding_source_version": "v1"},
        {"profile_embedding": [0.1]},
        {"embedding_model": "nomic-embed-text"},
    ):
        with pytest.raises(ValidationError):
            CandidateInput(user_id=1, **payload)


def test_unmet_confirmed_requires_confirmed_negative_evidence():
    with pytest.raises(ValidationError):
        RequirementAssessment(requirement="domingo", kind="explicit_constraint",
                              status="unmet_confirmed", reason="No disponible")
    assessed = RequirementAssessment(
        requirement="domingo", kind="explicit_constraint", status="unmet_confirmed",
        evidence=[evidence("No puedo asistir el domingo", kind="availability", polarity="denies")],
        reason="Declaró indisponibilidad los domingos",
    )
    assert assessed.status == "unmet_confirmed"
    assert "evidence" not in assessed.model_dump()


def test_response_representation_omits_source_and_rejects_obvious_pii():
    source = Evidence.model_validate(evidence("contacto@example.com", source_ref="profile:1"))
    assert "contacto@example.com" not in repr(source)
    assert "source_ref" not in source.model_dump()
    result = MatchResult(event_id=1, candidate_id=2, eligibility="needs_review",
                         requirements=[RequirementAssessment(
                             requirement="Python", kind="required_skill", status="unknown",
                             evidence=[source], reason="Sin evidencia de Python",
                         )], policy_version="v1")
    assert "contacto@example.com" not in repr(result)
    assert "contacto@example.com" not in json.dumps(result.model_dump())
    with pytest.raises(ValidationError):
        MatchResult(event_id=1, candidate_id=2, eligibility="eligible", policy_version="v1",
                    explanation={"strengths": ["Escribe a contacto@example.com"]})


def test_result_scores_and_coverage_are_bounded_but_not_calculated():
    result = MatchResult(event_id=1, candidate_id=2, eligibility="needs_review",
                         policy_version="v1", ranking_score=None,
                         score_components={"semantic": None},
                         evidence_coverage={"known": 0, "unknown": 2})
    assert result.ranking_score is None
    assert result.evidence_coverage.unknown == 2
    with pytest.raises(ValidationError):
        MatchResult(event_id=1, candidate_id=2, eligibility="eligible", policy_version="v1",
                    ranking_score=1.2)
