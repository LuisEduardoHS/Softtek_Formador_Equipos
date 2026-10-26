"""Constrained optional Llama wording, with deterministic explanations as fallback."""

import json

import pytest

from app.services.ai.matching.schemas import CandidateInput, EventInput, Evidence, PublicExplanation
from app.services.ai.recommendations import (
    OrganizerRecommendationContext, UserRecommendationContext,
    personalize_recommendation, recommend_candidates, recommend_projects,
)


def fact(value, *, source="user_declared", polarity="affirms"):
    return Evidence(value=value, kind="skill", source=source, polarity=polarity,
                    confirmed=True, source_ref="secret:record")


def prepared_pair():
    event = EventInput(
        event_id=42, creator_id=1, state="open", participants=[],
        requirements={"categoria": "Académico", "habilidades_obligatorias": ["Python", "Blender"],
                      "habilidades_deseables": ["Docker"]},
        confirmed_requirements=[fact(value, source="organizer_confirmed")
                                for value in ("Python", "Blender", "Docker")],
        event_embedding=[1.0, 0.0], embedding_model="fixture",
        embedding_source_version="v1",
    )
    user = CandidateInput(
        user_id=2, visibility="visible", account_state="active",
        declared_skills=[fact("Python"), fact("Docker", polarity="denies")],
        profile={"habilidades": [], "intereses": [], "areas_mejora": ["Kubernetes"],
                 "resumen_publico": "Nombre privado Ana"},
        profile_embedding=[1.0, 0.0], embedding_model="fixture",
        embedding_source_version="v1",
    )
    return event, user


def candidate_recommendation():
    event, user = prepared_pair()
    context = OrganizerRecommendationContext(
        authenticated_organizer_id=1, authorized_event_id=42,
        discoverable_candidate_ids=frozenset({2}), confirmed_member_ids=frozenset(),
        pending_candidate_ids=frozenset(),
    )
    return recommend_candidates(event, [user], context)[0]


def project_recommendation():
    event, user = prepared_pair()
    context = UserRecommendationContext(
        authenticated_user_id=2, discovery_consent=True,
        discoverable_event_ids=frozenset({42}),
        confirmed_member_event_ids=frozenset(),
        pending_invitation_event_ids=frozenset(),
        pending_application_event_ids=frozenset(),
    )
    return recommend_projects(user, [event], context)[0]


def choices_from_prompt(prompt, *, variant=1):
    facts = json.loads(prompt[prompt.index("{"):])
    return {group: [{"fact_id": item["fact_id"],
                    "variant": min(variant, item["variants"] - 1)} for item in entries]
            for group, entries in facts.items()}


class MockGenerator:
    def __init__(self, response=None, error=None):
        self.response = response
        self.error = error
        self.calls = []

    def generate_structured(self, prompt, schema):
        self.calls.append((prompt, schema))
        if self.error is not None:
            raise self.error
        if callable(self.response):
            return self.response(prompt)
        return self.response


def valid_response(prompt):
    return json.dumps(choices_from_prompt(prompt), ensure_ascii=False)


@pytest.mark.parametrize("build", [candidate_recommendation, project_recommendation])
def test_explicit_enrichment_preserves_facts_status_and_public_contract(build):
    original = build()
    model = MockGenerator(response=valid_response)
    changed = personalize_recommendation(original, use_llm=True, ai=model)
    assert type(changed) is type(original)
    assert changed.eligibility == original.eligibility
    assert changed.evidence_group == original.evidence_group
    assert changed.evidence_coverage == original.evidence_coverage
    assert changed.policy_version == original.policy_version
    assert changed.explanation != original.explanation
    assert any("Python" in line and "evidencia confirmada" in line.lower()
               for line in changed.explanation.strengths)
    assert any("Docker" in line and "contradicción" in line.lower()
               for line in changed.explanation.gaps)
    assert any("Blender" in line and "verificar" in line.lower()
               for line in changed.explanation.unknowns)
    assert original.explanation.strengths[0].startswith("Evidencia confirmada")
    assert "ranking_score" not in changed.model_dump()
    assert len(model.calls) == 1


def test_model_prompt_contains_only_anonymous_fact_categories():
    original = candidate_recommendation()
    model = MockGenerator(response=valid_response)
    personalize_recommendation(original, use_llm=True, ai=model)
    prompt, schema = model.calls[0]
    assert "s0" in prompt and "g0" in prompt and "u0" in prompt
    assert "habilidad_obligatoria" in prompt
    for private in ("Python", "Blender", "Docker", "Kubernetes", "Ana",
                    "secret:record", "42", "embedding", "1.0", "profile"):
        assert private not in prompt
    assert schema["additionalProperties"] is False


def test_default_path_never_calls_model_and_empty_facts_also_skip_it():
    original = candidate_recommendation()
    model = MockGenerator(error=AssertionError("should not be called"))
    assert personalize_recommendation(original, ai=model) == original
    assert model.calls == []
    empty = original.model_copy(update={"explanation": PublicExplanation()})
    assert personalize_recommendation(empty, use_llm=True, ai=model) == empty
    assert model.calls == []


@pytest.mark.parametrize("response", [
    "", "   ", "not json", "{}", '{"uncertain":true}',
    '{"strengths":[],"gaps":[],"unknowns":[]}',
    '{"strengths":[],"strengths":[],"gaps":[],"unknowns":[]}',
])
def test_invalid_empty_or_uncertain_output_falls_back(response):
    original = candidate_recommendation()
    model = MockGenerator(response=response)
    assert personalize_recommendation(original, use_llm=True, ai=model) == original


def test_hallucinated_fact_text_and_unknown_id_fall_back():
    original = candidate_recommendation()

    def invented_text(prompt):
        choices = choices_from_prompt(prompt)
        choices["strengths"][0]["text"] = "Domina Kubernetes y lidera el equipo"
        return json.dumps(choices)

    def invented_id(prompt):
        choices = choices_from_prompt(prompt)
        choices["strengths"][0]["fact_id"] = "s999"
        return json.dumps(choices)

    for response in (invented_text, invented_id):
        assert personalize_recommendation(
            original, use_llm=True, ai=MockGenerator(response=response)
        ) == original


def test_negation_and_unknown_cannot_be_omitted_or_promoted():
    original = candidate_recommendation()
    assert original.explanation.gaps and original.explanation.unknowns

    def omit_negation(prompt):
        choices = choices_from_prompt(prompt)
        choices["gaps"] = []
        return json.dumps(choices)

    def promote_unknown(prompt):
        choices = choices_from_prompt(prompt)
        choices["strengths"].append(choices["unknowns"].pop(0))
        return json.dumps(choices)

    for response in (omit_negation, promote_unknown):
        assert personalize_recommendation(
            original, use_llm=True, ai=MockGenerator(response=response)
        ) == original


def test_ollama_exception_and_bad_variant_fall_back_without_changing_rank():
    original = project_recommendation()
    failed = MockGenerator(error=RuntimeError("connection error"))
    assert personalize_recommendation(original, use_llm=True, ai=failed) == original

    def bad_variant(prompt):
        choices = choices_from_prompt(prompt)
        choices["gaps"][0]["variant"] = 99
        return json.dumps(choices)

    assert personalize_recommendation(
        original, use_llm=True, ai=MockGenerator(response=bad_variant)
    ) == original
    with pytest.raises(TypeError):
        personalize_recommendation(original, use_llm=1)
