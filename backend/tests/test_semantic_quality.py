"""Observed Llama mistakes must be repaired from explicit source, never similarity."""
import json
from unittest.mock import MagicMock

import pytest

from app.services.ai.profile_parser import ProfileParser
from app.services.ai.event_parser import EventParser
from app.services.ai.skill_terms import canonical_skill, reviewed_skills, skill_statements
from app.services.ai.matching.normalization import apply_equivalence
from test_qa_stability_security import qa, auth, profile as reviewed_profile
from app.services.ai import integration
from app.models.usuario import PerfilUsuario, Usuario
from app.services.ai.recommendations.orm_adapter import candidate_from_orm
from sqlalchemy.orm import Session


def profile(source, **output):
    ai = MagicMock()
    ai.generate_structured.return_value = json.dumps({"resumen_publico": "", **output})
    return ProfileParser(ai).parse_profile(source)


@pytest.mark.parametrize("label,expected", [
    ("programar con SQL", "SQL"), ("Sé programar con SQL", "SQL"),
    ("Experiencia en Blender", "Blender"), ("Experiencia en Unreal Engine 5", "Unreal Engine 5"),
    ("Experiencia en Figma", "Figma"), ("Experiencia en UX/UI", "UX/UI"),
])
def test_catalog_aliases_shared_by_extraction_and_matching(label, expected):
    assert canonical_skill(label) == expected
    assert apply_equivalence(label) == apply_equivalence(expected)
    assert apply_equivalence("No sé " + label) != apply_equivalence(expected)
    assert apply_equivalence("Quiero aprender " + label) != apply_equivalence(expected)


def test_sql_semantic_duplicate_has_one_canonical_label():
    assert reviewed_skills(["SQL", "programar con SQL", "programar en SQL", "sql"]) == ["SQL"]
    assert canonical_skill("programar SQL") == "SQL"
    assert canonical_skill("sé programar Python") == "Python"


def test_explicit_tools_survive_phrases_or_missing_model_labels():
    p = profile("Tengo experiencia en Blender y Unreal Engine 5.", habilidades=["Experiencia en Blender"])
    assert p.habilidades == ["Blender", "Unreal Engine 5"]
    p = profile("Diseño interfaces UX/UI en Figma y he realizado prototipos para una app.",
                habilidades=["Diseño interfaces UX/UI en Figma"])
    assert set(p.habilidades) == {"UX/UI", "Figma"}


@pytest.mark.parametrize("source", ["No sé Python.", "No tengo experiencia en Figma.",
                                    "No he usado Blender ni UE5."])
def test_denial_is_neither_competence_nor_automatic_learning_goal(source):
    p = profile(source, habilidades=["Python", "Figma", "Blender", "Unreal Engine 5"],
                areas_mejora=["Python", "Figma", "Blender", "Unreal Engine 5"])
    assert p.habilidades == [] and p.areas_mejora == []


def test_absence_of_experience_not_positive_or_goal_and_explicit_design_goal_recovers():
    p = profile("No tengo experiencia laboral ni profesional. Quiero aprender diseño.",
                experiencia=["No tiene experiencia laboral ni profesional", "Experiencia profesional"],
                areas_mejora=["experiencia laboral", "experiencia profesional"], intereses=["diseño"])
    assert p.experiencia == [] and p.areas_mejora == ["diseño"] and p.intereses == []
    assert "experiencia" not in p.resumen_publico.lower()


def test_explicit_positive_experience_retained_with_negated_professional_experience():
    p = profile("He participado en torneos amateurs. No tengo experiencia profesional.",
                experiencia=["torneos amateurs", "No tengo experiencia profesional", "experiencia profesional"])
    assert p.experiencia == ["torneos amateurs"]


def test_ambiguous_source_does_not_ground_invented_model_skills():
    p = profile("Me gustaría hacer algo interesante con otras personas, no sé qué aportar.",
                habilidades=["Python", "SQL", "Figma", "liderazgo"], areas_mejora=["Python"])
    assert p.habilidades == [] and p.areas_mejora == []
    assert profile("Sé Python.", habilidades=["Python", "C++"]).habilidades == ["Python"]


def test_interest_goal_and_positive_declaration_are_separate():
    p = profile("Sé Python. Me gustan los videojuegos. Quiero aprender Docker.",
                habilidades=["Python", "Docker", "videojuegos"], intereses=["videojuegos", "Docker"],
                areas_mejora=["Docker", "Python"])
    assert p.habilidades == ["Python"]
    assert p.intereses == ["videojuegos"] and p.areas_mejora == ["Docker"]


@pytest.mark.parametrize('negative,state', [('No me interesa Python.', 'denied_interest'),
                                          ('No quiero aprender Python.', 'denied_goal')])
def test_negated_interest_or_goal_does_not_negate_an_explicit_ability(negative,state):
    source = 'Sé Python. ' + negative
    p = profile(source, habilidades=['Python'], intereses=['Python'], areas_mejora=['Python'])
    assert p.habilidades == ['Python'] and p.intereses == [] and p.areas_mejora == []
    assert state in skill_statements(source)['Python']


@pytest.mark.parametrize("source,required,preferred", [
    ("Buscamos diseñador UX/UI. Figma es obligatorio para prototipar una app.", ["Figma"], []),
    ("Python y SQL son opcionales, no son obligatorios.", [], ["Python", "SQL"]),
    ("SQL obligatorio. Python no es obligatorio. No exigimos Docker.", ["SQL"], []),
])
def test_event_repair_uses_explicit_requirement_polarity(source, required, preferred):
    ai = MagicMock()
    ai.generate_structured.return_value = json.dumps({"restricciones_explicitas": [source]})
    p = EventParser(ai).parse_event(source, "Academico")
    assert p.habilidades_obligatorias == required
    assert p.habilidades_deseables == preferred
    assert p.restricciones_explicitas == []


def test_vague_labels_are_not_project_constraints():
    ai = MagicMock()
    ai.generate_structured.return_value = json.dumps({"restricciones_explicitas": ["herramientas", "roles", "aplicación web"]})
    p = EventParser(ai).parse_event("Haremos una aplicación web; no hemos decidido herramientas ni roles.")
    assert p.restricciones_explicitas == []


def test_real_model_learning_prefix_deduplicates_only_inside_goal_category():
    p = profile("No tengo experiencia laboral ni profesional. Quiero aprender diseño.",
                areas_mejora=["aprender diseño", "diseño"])
    assert p.areas_mejora == ["diseño"]
    assert canonical_skill("aprender diseño") == "aprender diseño"


def test_experience_does_not_invent_links_between_separate_source_clauses():
    p = profile("Tengo experiencia en Blender y Unreal Engine 5. He modelado escenarios 3D.",
                experiencia=["Modelado de escenarios 3D en Blender y Unreal Engine 5"])
    assert "Modelado de escenarios 3D en Blender y Unreal Engine 5" not in p.experiencia
    assert "He modelado escenarios 3D" in p.experiencia


def test_role_missing_from_model_is_recovered_only_from_literal_positive_search():
    ai = MagicMock()
    ai.generate_structured.return_value = '{}'
    assert EventParser(ai).parse_event("Buscamos analista con SQL obligatorio.").roles_buscados == ["analista"]
    assert EventParser(ai).parse_event("No buscamos analista. Nos interesa SQL.").roles_buscados == []


def test_model_cannot_promote_a_role_domain_to_an_extra_required_skill():
    ai = MagicMock()
    ai.generate_structured.return_value = json.dumps({"habilidades_obligatorias": ["UX/UI", "Figma"]})
    p = EventParser(ai).parse_event("Buscamos diseñador UX/UI. Figma obligatorio.")
    assert p.habilidades_obligatorias == ["Figma"]


def test_project_prompt_does_not_seed_foreign_goalkeeper_example():
    ai = MagicMock()
    ai.generate_structured.return_value = '{}'
    EventParser(ai).parse_event("Figma obligatorio.")
    instructions = ai.generate_structured.call_args.kwargs['prompt'].split('<descripcion_libre>')[0]
    assert 'portero' not in instructions


@pytest.mark.parametrize("source,restrictions", [
    ("Figma obligatorio para prototipar una app accesible.", ["prototipar una app accesible en Figma", "accesible en Figma"]),
    ("Python y SQL son opcionales, no son obligatorios.", ["Python", "SQL", "no obligatorio"]),
    ("Python y SQL son opcionales, no son obligatorios.", ["condiciones de participación no especificadas"]),
    ("Queremos hacer algo creativo; no hemos decidido herramientas ni roles.", ["Queremos hacer algo creativo; no hemos decidido herramientas ni roles."]),
])
def test_real_model_topic_and_optional_labels_are_not_constraints(source, restrictions):
    ai = MagicMock()
    ai.generate_structured.return_value = json.dumps({"restricciones_explicitas": restrictions})
    assert EventParser(ai).parse_event(source).restricciones_explicitas == []


def test_non_catalog_concepts_are_not_inferred_as_aliases():
    assert canonical_skill("crear consultas") == "crear consultas"
    assert apply_equivalence("Unreal Engine 4") != apply_equivalence("UE5")
    assert reviewed_skills(["año", "ano"]) == ["año", "ano"]
    p = profile("Me interesa Blender y quiero aprender Figma.", habilidades=["Blender", "Figma"])
    assert p.habilidades == []


def test_empty_confirmed_profile_has_distinct_state_and_no_retry_service_call(qa, monkeypatch):
    client, engine = qa
    generator = MagicMock(side_effect=AssertionError("Nomic must not be called for empty content"))
    monkeypatch.setattr(integration, "generate_reviewed_profile_vector", generator)
    body = {**reviewed_profile(), "fortalezas": [], "intereses": [], "experiencia": [],
            "reforzar": ["Docker"], "resumen_publico": ""}
    response = client.post("/perfil/confirmar", headers=auth(), json=body)
    assert response.status_code == 200 and response.json()["perfil_estado_ia"] == "sin_contenido"
    assert response.json()["perfil_estructurado_ia"]["areas_mejora"] == ["Docker"]
    assert client.post("/perfil/embedding/reintentar", headers=auth()).status_code == 409
    generator.assert_not_called()
    with Session(engine) as db:
        p = db.get(PerfilUsuario, 1)
        candidate = candidate_from_orm(db.get(Usuario, 1), p, self_access=True)
        assert candidate.declared_skills == [] and p.embedding_perfil is None
    monkeypatch.setattr(integration, "generate_reviewed_profile_vector", lambda _: [0.1]*768)
    response = client.post("/perfil/confirmar", headers=auth(), json=reviewed_profile())
    assert response.json()["perfil_estado_ia"] == "listo"


def test_nonempty_profile_service_failure_still_pending_embedding(qa, monkeypatch):
    client, _ = qa
    def offline(_):
        raise ConnectionError("QA offline")
    monkeypatch.setattr(integration, "generate_reviewed_profile_vector", offline)
    response = client.post("/perfil/confirmar", headers=auth(), json=reviewed_profile())
    assert response.status_code == 200 and response.json()["perfil_estado_ia"] == "pendiente_embedding"


def test_human_review_merges_safe_alias_duplicates_and_rejects_conflicting_levels(qa, monkeypatch):
    client, _ = qa
    monkeypatch.setattr(integration, "generate_reviewed_profile_vector", lambda _: [0.1]*768)
    body = {**reviewed_profile(), "fortalezas": [{"nombre": "SQL"}, {"nombre": "programar con SQL"}]}
    r = client.post("/perfil/confirmar", headers=auth(), json=body)
    assert r.status_code == 200 and [v["nombre"] for v in r.json()["datos_crudos"]["fortalezas"]] == ["SQL"]
    body["fortalezas"] = [{"nombre": "SQL", "nivel": "básico"}, {"nombre": "programar con SQL", "nivel": "avanzado"}]
    assert client.post("/perfil/confirmar", headers=auth(), json=body).status_code == 422
