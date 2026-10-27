"""HTTP regressions for real UI contracts; all writes are isolated SQLite fixtures."""
import pytest
from sqlalchemy.orm import Session
from test_qa_stability_security import qa, auth, profile, event
from app.models.usuario import PerfilUsuario, Usuario
from app.models.evento import Evento
from app.models.participante import ParticipanteEvento


@pytest.fixture(autouse=True)
def no_external_embeddings(monkeypatch):
    async def pending(*args, **kwargs):
        pass
    monkeypatch.setattr("app.api.routes.eventos.process_event_embedding", pending)
    monkeypatch.setattr("app.api.routes.perfiles.process_profile_embedding", pending)


def create(client, slots=1, skills=None):
    data = event()
    data["detalles_especificos"]["roles"][0].update(vacantes=slots, habilidades=[])
    data["requisitos_confirmados"]["habilidades_obligatorias"] = skills or ["Python", "SQL"]
    response = client.post("/eventos/", headers=auth(), json=data)
    assert response.status_code == 201, response.text
    return response.json()


def test_no_usable_role_is_not_available_even_with_global_capacity(qa):
    client, engine = qa
    project = create(client)
    with Session(engine) as db:
        db.add(ParticipanteEvento(id_evento=project["id_evento"], id_usuario=2, rol="Backend"))
        db.commit()
    view = client.get(f'/eventos/{project["id_evento"]}', headers=auth()).json()
    assert view["cupos_disponibles"] == 1
    assert view["acepta_participacion"] is False
    assert view["roles_disponibles"] == []
    assert client.get(f'/recomendaciones/eventos/{project["id_evento"]}/candidatos', headers=auth()).json() == []


def test_recommendations_filter_unusable_vacancies_but_keep_matching_open_projects(qa):
    client, engine = qa
    with Session(engine) as db:
        db.add(Usuario(id_usuario=3, nombre="QA 3", correo="qa3@example.com", carrera="QA",
                       password_hash="unused", estado_cuenta="Activa"))
        db.flush()
        db.add(PerfilUsuario(usuario_id=3, datos_crudos={}))
        db.commit()
    body = profile()
    body["fortalezas"].append({"nombre": "SQL"})
    assert client.post('/perfil/confirmar', headers=auth(3), json=body).status_code == 200
    project = create(client)
    eid = project["id_evento"]
    candidates_url = f'/recomendaciones/eventos/{eid}/candidatos'
    projects_url = '/recomendaciones/usuarios/3/proyectos'
    assert any(r["candidate_id"] == 3 for r in client.get(candidates_url, headers=auth()).json())
    assert any(r["event_id"] == eid for r in client.get(projects_url, headers=auth(3)).json())
    with Session(engine) as db:
        db.add(ParticipanteEvento(id_evento=eid, id_usuario=2, rol="Backend"))
        db.commit()
    assert client.get(candidates_url, headers=auth()).json() == []
    assert client.get(projects_url, headers=auth(3)).json() == []


def test_pending_application_disables_action_without_changing_physical_vacancies(qa):
    client, engine = qa
    project = create(client)
    eid = project["id_evento"]
    assert client.get(f'/eventos/{eid}', headers=auth(2)).json()["puede_solicitar"] is True
    assert client.post(f'/eventos/{eid}/solicitudes?solicitante_id=2', headers=auth(2),
                       json={"rol_esperado": "backend"}).status_code == 200
    view = client.get(f'/eventos/{eid}', headers=auth(2)).json()
    assert view["acepta_participacion"] is True and view["puede_solicitar"] is False


def test_multiple_role_slots_and_legacy_generic_participant(qa):
    client, engine = qa
    project = create(client, slots=2)
    with Session(engine) as db:
        db.add(ParticipanteEvento(id_evento=project["id_evento"], id_usuario=2, rol="Backend"))
        db.commit()
    view = client.get(f'/eventos/{project["id_evento"]}', headers=auth()).json()
    assert view["acepta_participacion"] is True
    assert view["roles_disponibles"][0]["vacantes_disponibles"] == 1
    data = event()
    data["detalles_especificos"]["roles"] = []
    response = client.post('/eventos/', headers=auth(), json=data).json()
    assert response["roles_disponibles"][0]["nombre"] == "Participante"


def test_coverage_uses_global_confirmed_requirements_and_actual_skills(qa):
    client, engine = qa
    create(client)
    assert client.post('/perfil/confirmar', headers=auth(), json=profile()).status_code == 200
    coverage = client.get('/equipos/1', headers=auth()).json()[0]["cobertura_habilidades"]
    assert coverage["total"] == 2
    assert coverage["cubiertas"] == ["Python"]
    assert coverage["por_acreditar"] == ["SQL"]
    assert coverage["estado"] == "conocida"


def test_coverage_unknown_without_confirmation_and_no_false_zero_complete(qa):
    client, engine = qa
    create(client)
    coverage = client.get('/equipos/1', headers=auth()).json()[0]["cobertura_habilidades"]
    assert coverage["estado"] == "desconocida"
    assert coverage["cubiertas"] == []


@pytest.mark.parametrize('kind', ['hidden', 'unconfirmed', 'no_requirements'])
def test_coverage_never_infers_skills_from_roles_or_private_profiles(qa, kind):
    client, engine = qa
    project = create(client)
    assert client.post('/perfil/confirmar', headers=auth(), json=profile()).status_code == 200
    other = profile()
    other["fortalezas"] = [{"nombre": "SQL"}]
    if kind == 'hidden': other["visibilidad"]["fortalezas"] = False
    assert client.post('/perfil/confirmar', headers=auth(2), json=other).status_code == 200
    with Session(engine) as db:
        db.add(ParticipanteEvento(id_evento=project["id_evento"], id_usuario=2, rol="Backend"))
        if kind == 'unconfirmed': db.get(PerfilUsuario, 2).perfil_confirmado_at = None
        if kind == 'no_requirements': db.get(Evento, project["id_evento"]).requisitos_confirmados_at = None
        db.commit()
    coverage = client.get('/equipos/1', headers=auth()).json()[0]["cobertura_habilidades"]
    assert coverage["estado"] == "desconocida"
    assert "SQL" not in coverage["cubiertas"]


@pytest.mark.parametrize('kind', ['paused', 'no_consent'])
def test_directory_name_search_also_respects_discovery_preferences(qa, kind):
    client, engine = qa
    body = profile()
    if kind == 'paused': body["pausado"] = True
    if kind == 'no_consent': body["consentimiento_recomendaciones"] = False
    assert client.post('/perfil/confirmar', headers=auth(), json=body).status_code == 200
    assert client.get('/perfil/estudiantes/?q=QA', headers=auth(2)).json() == []


def test_empty_directory_query_and_blank_career_are_safe_and_limit_after_privacy(qa):
    client, engine = qa
    body = profile()
    body["carrera"] = ""
    assert client.post('/perfil/confirmar', headers=auth(), json=body).status_code == 200
    assert len(client.get('/perfil/estudiantes/?limit=1', headers=auth(2)).json()) == 1
    assert len(client.get('/perfil/estudiantes/?q=Python', headers=auth(2)).json()) == 1


@pytest.mark.parametrize('filters,expected', [
    ('disponibilidad=tarde&habilidad=programar%20con%20SQL', [1]),
    ('disponibilidad=manana', []), ('carrera=Diseno', [1]), ('semestre=2', [1]),
])
def test_directory_filters_use_visible_confirmed_data_before_limit(qa, filters, expected):
    client, engine = qa
    body = profile()
    body['fortalezas'] = [{'nombre': 'SQL'}]
    body['carrera'] = 'Diseño'
    assert client.post('/perfil/confirmar', headers=auth(), json=body).status_code == 200
    with Session(engine) as db:
        p = db.get(PerfilUsuario, 1)
        p.datos_crudos = {**p.datos_crudos, 'semestre': 2}
        db.commit()
    other = profile()
    other['disponibilidad'] = []
    assert client.post('/perfil/confirmar', headers=auth(2), json=other).status_code == 200
    r = client.get('/perfil/estudiantes/?limit=1&'+filters, headers=auth(2))
    assert r.status_code == 200
    assert [p['usuario_id'] for p in r.json()] == expected


@pytest.mark.parametrize('kind', ['visible', 'hidden', 'paused', 'no_consent', 'unconfirmed'])
def test_directory_skill_search_only_confirmed_permitted_evidence(qa, kind):
    client, engine = qa
    body = profile()
    body["nombre"] = "Persona ficticia"
    body["carrera"] = "Otra carrera"
    assert client.post('/perfil/confirmar', headers=auth(), json=body).status_code == 200
    with Session(engine) as db:
        p = db.get(PerfilUsuario, 1)
        raw = dict(p.datos_crudos)
        if kind == 'hidden':
            raw["visibilidad"] = {**raw["visibilidad"], "fortalezas": False}
        if kind == 'paused': raw["pausado"] = True
        if kind == 'no_consent': raw["consentimiento_recomendaciones"] = False
        if kind == 'unconfirmed': p.perfil_confirmado_at = None
        p.datos_crudos = raw
        db.commit()
    result = client.get('/perfil/estudiantes/?q=programar%20en%20Python', headers=auth(2))
    assert result.status_code == 200
    assert [p["usuario_id"] for p in result.json()] == ([1] if kind == 'visible' else [])


def test_confirmation_requires_current_source_fingerprint(qa):
    client, engine = qa
    project = create(client)
    body = {"requirements": event()["requisitos_confirmados"], "confirmado_por_creador": True}
    url = f'/eventos/{project["id_evento"]}/confirmar'
    assert client.post(url, headers=auth(), json=body).status_code == 422
    body["fuente_revision"] = "0" * 64
    assert client.post(url, headers=auth(), json=body).status_code == 409
    body["fuente_revision"] = project["fuente_revision"]
    assert client.post(url, headers=auth(), json=body).status_code == 200


def test_confirmed_public_skill_keeps_human_reviewed_level(qa):
    client, engine = qa
    body = profile()
    body['fortalezas'] = [{'nombre': 'Python', 'nivel': 'Avanzado'}]
    assert client.post('/perfil/confirmar', headers=auth(), json=body).status_code == 200
    data = client.get('/perfil/publico/1', headers=auth(2)).json()['datos_crudos']
    assert data['fortalezas'] == [{'nombre': 'Python', 'nivel': 'Avanzado'}]
