"""MVP participation, review/retry and extraction regressions over real ORM rows."""
import json
import os
import asyncio
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from unittest.mock import MagicMock

os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("AUTH_SECRET", "mvp-test-secret-at-least-thirty-two-characters")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.main import app
from app.db.database import Base, get_db
from app.core.security import create_access_token
from app.models.evento import Evento
from app.models.participante import ParticipanteEvento
from app.models.solicitud import SolicitudEquipo
from app.models.usuario import Usuario, PerfilUsuario
from app.services.ai import integration
from app.services.ai.event_parser import EventParser
from app.services.ai.profile_parser import ProfileParser
from app.services.ai.matching.normalization import apply_equivalence
from app.services.ai.matching.requirements import assess_requirements
from app.services.ai.matching.schemas import CandidateInput, EventInput, Evidence
from app.services.ai.schemas import StructuredEventRequirements
from app.services.ai.schemas import StructuredProfile
from app.services.ai.recommendations.orm_adapter import event_from_orm
from app.services.ai.ollama_client import OllamaServiceError


def auth(uid):
    return {"Authorization": f"Bearer {create_access_token(uid)}"}


@pytest.fixture
def world(tmp_path, monkeypatch):
    monkeypatch.setenv("AUTH_SECRET", "mvp-test-secret-at-least-thirty-two-characters")
    engine = create_engine(f"sqlite:///{(tmp_path / 'mvp.sqlite').as_posix()}",
                           connect_args={"check_same_thread": False, "timeout": 10})
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        db.add_all([Usuario(id_usuario=i, nombre=f"Persona {i}", correo=f"mvp{i}@example.test",
                            carrera="Sistemas", password_hash="unused", estado_cuenta="Activa")
                    for i in range(1, 6)])
        db.flush()
        db.add_all([PerfilUsuario(usuario_id=i, datos_crudos={"pausado": False}) for i in range(1, 6)])
        db.add(Evento(id_evento=1, creador_id=1, titulo="Proyecto Python", categoria_principal="Academico",
                      descripcion_libre="Python obligatorio y SQL deseable.", estado="Abierto",
                      estado_ia="listo", requisitos_confirmados_at=integration.utc_now(),
                      requisitos_fuente_revision="original", embedding_fuente_revision="original",
                      embedding_requisitos=[0.2] * 768,
                      requisitos_ia={"habilidades_obligatorias": ["Python"], "roles_buscados": ["Backend", "Diseño"]},
                      detalles_especificos={"integrantes": 3, "roles": [
                          {"id": "backend", "nombre": "Backend", "habilidades": ["Python"]},
                          {"id": "design", "nombre": "Diseño", "habilidades": []}]}))
        db.commit()
    def override():
        with Session(engine) as db:
            yield db
    app.dependency_overrides[get_db] = override
    with TestClient(app) as client:
        yield client, engine
    app.dependency_overrides.clear()
    engine.dispose()


def invite(client, user=2, role="Backend"):
    return client.post("/invitaciones/?de_id=1", headers=auth(1), json={
        "id_evento": 1, "id_destinatario": user, "rol_esperado": role, "mensaje_explicacion": "Hola"})


def apply(client, user=2, role="backend"):
    return client.post(f"/eventos/1/solicitudes?solicitante_id={user}", headers=auth(user),
                       json={"rol_esperado": role})


def accept(client, request_id, actor):
    return client.patch(f"/invitaciones/{request_id}", headers=auth(actor), json={"estado": "Aceptada"})


def test_capacity_counts_creator_once_and_rejects_late_acceptance(world):
    client, engine = world
    with Session(engine) as db:
        event = db.get(Evento, 1)
        event.detalles_especificos = {**event.detalles_especificos, "integrantes": 2}
        db.commit()
    first, second = invite(client, 2), invite(client, 3, "Diseño")
    assert first.status_code == second.status_code == 200
    assert accept(client, first.json()["id"], 2).status_code == 200
    failed = accept(client, second.json()["id"], 3)
    assert failed.status_code == 409 and "capacidad" in failed.json()["detail"]
    assert invite(client, 4, "Diseño").status_code == 409
    with Session(engine) as db:
        assert db.query(ParticipanteEvento).count() == 1
        assert db.get(SolicitudEquipo, second.json()["id"]).estado == "Pendiente"


def test_role_occupancy_uses_members_not_stale_json(world):
    client, engine = world
    first, second = apply(client, 2), apply(client, 3)
    assert first.status_code == second.status_code == 200
    assert accept(client, first.json()["id"], 1).status_code == 200
    assert accept(client, second.json()["id"], 1).status_code == 409
    assert apply(client, 4).status_code == 409
    with Session(engine) as db:
        assert not db.get(Evento, 1).detalles_especificos["roles"][0].get("cubiertoPor")
        assert db.query(ParticipanteEvento).one().id_usuario == 2


def test_explicit_multiple_vacancies_allow_two_members_but_not_three(world):
    client, engine = world
    with Session(engine) as db:
        event = db.get(Evento, 1)
        event.detalles_especificos = {"integrantes": 5, "roles": [
            {"id": "backend", "nombre": "Backend", "vacantes": 2}]}
        db.commit()
    for uid in (2, 3):
        response = apply(client, uid)
        assert response.status_code == 200
        assert accept(client, response.json()["id"], 1).status_code == 200
    assert apply(client, 4).status_code == 409


@pytest.mark.parametrize("first_kind", ["invite", "apply"])
def test_pending_duplicates_rejected_in_both_directions(world, first_kind):
    client, _ = world
    first = invite(client) if first_kind == "invite" else apply(client)
    assert first.status_code == 200
    assert invite(client).status_code == 409
    assert apply(client).status_code == 409


@pytest.mark.parametrize("change", ["closed", "paused", "inactive", "role_removed", "already_member"])
def test_acceptance_revalidates_current_rows(world, change):
    client, engine = world
    response = invite(client)
    assert response.status_code == 200
    with Session(engine) as db:
        if change == "closed": db.get(Evento, 1).estado = "Cerrado"
        elif change == "paused": db.get(PerfilUsuario, 2).datos_crudos = {"pausado": True}
        elif change == "inactive": db.get(Usuario, 2).estado_cuenta = "Inactiva"
        elif change == "role_removed":
            event = db.get(Evento, 1)
            event.detalles_especificos = {**event.detalles_especificos, "roles": []}
        else: db.add(ParticipanteEvento(id_evento=1, id_usuario=2, rol="Backend"))
        db.commit()
    assert accept(client, response.json()["id"], 2).status_code in {403, 409}
    with Session(engine) as db:
        assert db.get(SolicitudEquipo, response.json()["id"]).estado == "Pendiente"


def test_two_concurrent_acceptances_cannot_consume_last_slot(world):
    client, engine = world
    with Session(engine) as db:
        event = db.get(Evento, 1)
        event.detalles_especificos = {**event.detalles_especificos, "integrantes": 2}
        db.commit()
    ids = [invite(client, 2).json()["id"], invite(client, 3, "Diseño").json()["id"]]
    barrier = Barrier(2)
    def run(pair):
        barrier.wait(timeout=5)
        return accept(client, pair[0], pair[1]).status_code
    with ThreadPoolExecutor(max_workers=2) as workers:
        assert sorted(workers.map(run, zip(ids, (2, 3)))) == [200, 409]
    with Session(engine) as db:
        assert db.query(ParticipanteEvento).count() == 1
        assert db.query(SolicitudEquipo).filter_by(estado="Aceptada").count() == 1


def test_concurrent_acceptances_cannot_fill_unique_role_twice(world):
    client, engine = world
    ids = [invite(client, 2).json()["id"], invite(client, 3).json()["id"]]
    barrier = Barrier(2)
    def run(pair):
        barrier.wait(timeout=5)
        return accept(client, pair[0], pair[1]).status_code
    with ThreadPoolExecutor(max_workers=2) as workers:
        assert sorted(workers.map(run, zip(ids, (2, 3)))) == [200, 409]
    with Session(engine) as db:
        assert db.query(ParticipanteEvento).filter_by(rol="Backend").count() == 1


def test_creator_already_present_in_orm_is_not_counted_twice(world):
    client, engine = world
    with Session(engine) as db:
        event = db.get(Evento, 1)
        event.detalles_especificos = {**event.detalles_especificos, "integrantes": 2}
        db.add(ParticipanteEvento(id_evento=1, id_usuario=1, rol="Creador"))
        db.commit()
    invitation = invite(client)
    assert invitation.status_code == 200
    assert accept(client, invitation.json()["id"], 2).status_code == 200
    assert client.get("/eventos/1", headers=auth(1)).json()["cupos_disponibles"] == 0


def test_concurrent_opposite_requests_have_only_one_pending_pair(world):
    client, engine = world
    barrier = Barrier(2)
    def run(kind):
        barrier.wait(timeout=5)
        return (invite(client) if kind == "invite" else apply(client)).status_code
    with ThreadPoolExecutor(max_workers=2) as workers:
        assert sorted(workers.map(run, ["invite", "apply"])) == [200, 409]
    with Session(engine) as db:
        assert db.query(SolicitudEquipo).filter_by(estado="Pendiente").count() == 1


def edit_body(revision=None):
    return {"categoria_principal": "Academico", "descripcion_libre": "SQL obligatorio para el proyecto actualizado",
            "integrantes": 3, "detalles_especificos": {"roles": [
                {"id": "backend", "nombre": "Backend", "habilidades": ["SQL"]}]},
            "requisitos_ia": {}, "fuente_revision": revision}


def test_edit_reconfirm_retry_and_no_obsolete_requirements(world, monkeypatch):
    client, engine = world
    original = client.get("/eventos/1", headers=auth(1)).json()
    edited = client.put("/eventos/1?usuario_id=1", headers=auth(1), json=edit_body(original["fuente_revision"]))
    assert edited.status_code == 200, edited.text
    assert edited.json()["estado_ia"] == "pendiente_revision"
    assert edited.json()["requisitos_ia"] == {}
    assert client.get("/equipos/1", headers=auth(1)).json()[0]["proyecto"]["requisitos_ia"] == {}
    assert client.post("/eventos/1/embedding/reintentar", headers=auth(1)).status_code == 409
    req = {"categoria": "Academico", "habilidades_obligatorias": ["SQL"], "roles_buscados": ["Backend"]}
    review = {"requirements": req, "confirmado_por_creador": True, "fuente_revision": original["fuente_revision"]}
    assert client.post("/eventos/1/confirmar", headers=auth(1), json=review).status_code == 409
    # A second edit must preserve the previous reviewed draft without publishing it.
    assert client.put("/eventos/1?usuario_id=1", headers=auth(1), json=edit_body()).status_code == 200
    with Session(engine) as db:
        assert db.get(Evento, 1).requisitos_borrador_ia["habilidades_obligatorias"] == ["Python"]
    def offline(_): raise OllamaServiceError("offline")
    monkeypatch.setattr(integration, "generate_reviewed_event_vector", offline)
    current = client.get("/eventos/1", headers=auth(1)).json()
    review["fuente_revision"] = current["fuente_revision"]
    confirmed = client.post("/eventos/1/confirmar", headers=auth(1), json=review)
    assert confirmed.status_code == 200, confirmed.text
    assert confirmed.json()["estado_ia"] == "pendiente_embedding"
    assert confirmed.json()["requisitos_ia"]["habilidades_obligatorias"] == ["SQL"]
    monkeypatch.setattr(integration, "generate_reviewed_event_vector", lambda _: [0.4] * 768)
    retried = client.post("/eventos/1/embedding/reintentar", headers=auth(1))
    assert retried.status_code == 200 and retried.json()["estado_ia"] == "listo"
    assert "embedding_requisitos" not in retried.json()


def test_repeated_response_and_members_cannot_be_invited_again(world):
    client, _ = world
    invitation = invite(client).json()["id"]
    assert accept(client, invitation, 2).status_code == 200
    assert accept(client, invitation, 2).status_code == 409
    assert invite(client, 2, "Diseño").status_code == 409


def test_occupied_role_cannot_be_removed_by_edit(world):
    client, _ = world
    invitation = invite(client).json()["id"]
    assert accept(client, invitation, 2).status_code == 200
    body = edit_body()
    body["detalles_especificos"]["roles"] = [{"id": "other", "nombre": "Otro"}]
    assert client.put("/eventos/1?usuario_id=1", headers=auth(1), json=body).status_code == 409


@pytest.mark.parametrize("alias,term", [("programar en Python", "Python"), ("Sé programar en Python", "Python"),
                                         ("programación en SQL", "SQL"), ("programar en SQL", "SQL")])
def test_positive_equivalences(alias, term):
    assert apply_equivalence(alias) == apply_equivalence(term)
    assert apply_equivalence(f"no sé {alias}") != apply_equivalence(term)
    assert apply_equivalence(f"quiero aprender {alias}") != apply_equivalence(term)


@pytest.mark.parametrize("text,positive", [("Sé programar en Python y SQL.", ["Python", "SQL"]),
    ("No sé Python ni SQL.", []), ("Quiero aprender Python y SQL.", []),
    ("No sé Python, pero domino SQL.", ["SQL"]), ("Sé Python pero quiero mejorar Python.", ["Python"])])
def test_profile_repairs_model_skills_without_promoting_negations(text, positive):
    ai = MagicMock()
    ai.generate_structured.return_value = json.dumps({"habilidades": ["programar en Python", "SQL"], "resumen_publico": ""})
    parsed = ProfileParser(ai).parse_profile(text)
    assert parsed.habilidades == positive


@pytest.mark.parametrize("text,required,preferred", [
    ("Python obligatorio y SQL deseable.", ["Python"], ["SQL"]),
    ("Imprescindible programar en Python; SQL opcional.", ["Python"], ["SQL"]),
    ("No exigimos Python ni SQL.", [], []),
    ("No exigimos Python; SQL obligatorio.", ["SQL"], []),
    ("Python no es obligatorio; SQL es deseable.", [], ["SQL"]),
])
def test_event_repairs_omissions_and_negated_requirements(text, required, preferred):
    ai = MagicMock()
    ai.generate_structured.return_value = json.dumps({"habilidades_obligatorias": [], "habilidades_deseables": []})
    parsed = EventParser(ai).parse_event(text, "Academico")
    assert parsed.habilidades_obligatorias == required
    assert parsed.habilidades_deseables == preferred


def test_event_title_is_not_a_participation_constraint():
    ai = MagicMock()
    ai.generate_structured.return_value = json.dumps({"restricciones_explicitas": ["Prueba cierre MVP", "sábados"]})
    parsed = EventParser(ai).parse_event("SQL obligatorio; reuniones los sábados.", "Academico", {"titulo": "Prueba cierre MVP"})
    assert parsed.restricciones_explicitas == ["sábados"]


def test_model_cannot_reintroduce_negated_skill_as_constraint():
    ai = MagicMock()
    ai.generate_structured.return_value = json.dumps({"habilidades_obligatorias": ["Python", "SQL"],
        "restricciones_explicitas": ["No exigimos Python ni SQL.", "sábados en Monterrey"]})
    parsed = EventParser(ai).parse_event("No exigimos Python ni SQL. Entrenamos sábados en Monterrey.", "Academico")
    assert parsed.habilidades_obligatorias == []
    assert parsed.restricciones_explicitas == ["sábados en Monterrey"]


def test_matching_confirmed_denial_never_becomes_a_positive_alias():
    event = EventInput(event_id=1, creator_id=1, requirements=StructuredEventRequirements(habilidades_obligatorias=["Python"]),
                       confirmed_requirements=[Evidence(source="organizer_confirmed", kind="skill", value="Python", confirmed=True, polarity="affirms")])
    candidate = CandidateInput(user_id=2, declared_skills=[Evidence(source="user_declared", kind="skill",
                               value="no sé programar en Python", confirmed=True, polarity="denies")])
    result = assess_requirements(event, candidate)
    assert result[0].status == "unmet_confirmed"


def test_late_event_embedding_does_not_restore_edited_requirements(world, monkeypatch):
    _, engine = world
    def delayed_result(_):
        with Session(engine) as other:
            event = other.get(Evento, 1)
            event.requisitos_fuente_revision = None
            event.requisitos_confirmados_at = None
            event.requisitos_ia = {}
            event.embedding_requisitos = None
            event.estado_ia = "pendiente_revision"
            other.commit()
        return [0.5] * 768
    monkeypatch.setattr(integration, "generate_reviewed_event_vector", delayed_result)
    with Session(engine) as db:
        event = db.get(Evento, 1)
        asyncio.run(integration.process_event_embedding(db, event, StructuredEventRequirements(habilidades_obligatorias=["Python"])))
        db.commit()
        assert event.embedding_requisitos is None
        assert event.estado_ia == "pendiente_revision"
        assert event.requisitos_ia == {}


def test_profile_retry_does_not_reconfirm_obsolete_data(world, monkeypatch):
    client, engine = world
    with Session(engine) as db:
        profile = db.get(PerfilUsuario, 2)
        profile.perfil_estructurado_ia = {"habilidades": ["Python"], "resumen_publico": "Python"}
        profile.perfil_fuente_revision = "old"
        profile.perfil_confirmado_at = integration.utc_now()
        profile.perfil_estado_ia = "listo"
        profile.embedding_perfil = [0.1] * 768
        db.commit()
    response = client.put("/perfil/2", headers=auth(2), json={"datos_crudos": {"fortalezas": [{"nombre": "SQL"}]}})
    assert response.status_code == 200
    assert response.json()["perfil_estado_ia"] == "obsoleto"
    assert response.json()["perfil_estructurado_ia"] is None
    assert client.post("/perfil/embedding/reintentar", headers=auth(2)).status_code == 409
    monkeypatch.setattr(integration, "generate_reviewed_profile_vector", lambda _: [0.2] * 768)
    payload = {"nombre": "Persona 2", "fortalezas": [{"nombre": "programar en SQL"}],
               "visibilidad": {"fortalezas": True, "intereses": True, "disponibilidad": True, "reforzar": False, "correo": False},
               "consentimiento_recomendaciones": True}
    confirmed = client.post("/perfil/confirmar", headers=auth(2), json=payload)
    assert confirmed.status_code == 200, confirmed.text
    assert confirmed.json()["perfil_estado_ia"] == "listo"
    assert confirmed.json()["perfil_estructurado_ia"]["habilidades"] == ["SQL"]
    assert confirmed.json()["datos_crudos"]["fortalezas"][0]["nombre"] == "SQL"
    payload["fortalezas"] = [{"nombre": "no sé Python"}]
    assert client.post("/perfil/confirmar", headers=auth(2), json=payload).status_code == 422


def test_late_profile_embedding_failure_does_not_erase_success(world, monkeypatch):
    _, engine = world
    with Session(engine) as db:
        profile = db.get(PerfilUsuario, 2)
        profile.perfil_estado_ia = "pendiente_embedding"
        profile.perfil_fuente_revision = "current"
        profile.perfil_confirmado_at = integration.utc_now()
        db.commit()
    def failure_after_success(_):
        with Session(engine) as other:
            profile = other.get(PerfilUsuario, 2)
            profile.perfil_estado_ia = "listo"
            profile.embedding_perfil = [0.7] * 768
            other.commit()
        raise OllamaServiceError("late failure")
    monkeypatch.setattr(integration, "generate_reviewed_profile_vector", failure_after_success)
    with Session(engine) as db:
        profile = db.get(PerfilUsuario, 2)
        asyncio.run(integration.process_profile_embedding(db, profile, StructuredProfile(habilidades=["Python"], resumen_publico="")))
        db.commit()
        assert profile.perfil_estado_ia == "listo"
        assert profile.embedding_perfil == [0.7] * 768


@pytest.mark.parametrize("kind", ["event", "profile"])
def test_embedding_keeps_captured_revision_when_session_reload_sees_new_confirmation(world, monkeypatch, kind):
    _, engine = world
    with Session(engine) as db:
        if kind == "event":
            record = db.get(Evento, 1)
            record.requisitos_fuente_revision = "new-confirmation"
            record.embedding_requisitos = [0.8] * 768
        else:
            record = db.get(PerfilUsuario, 2)
            record.perfil_fuente_revision = "new-confirmation"
            record.perfil_confirmado_at = integration.utc_now()
            record.perfil_estado_ia = "listo"
            record.embedding_perfil = [0.8] * 768
        db.commit()
        # The object has expired at commit and now reloads the newer revision.
        # The payload being embedded still belongs to the older confirmation.
        if kind == "event":
            monkeypatch.setattr(integration, "generate_reviewed_event_vector", lambda _: [0.1] * 768)
            asyncio.run(integration.process_event_embedding(db, record, StructuredEventRequirements(), expected_revision="old-confirmation"))
            db.commit()
            assert record.embedding_requisitos == [0.8] * 768
        else:
            monkeypatch.setattr(integration, "generate_reviewed_profile_vector", lambda _: [0.1] * 768)
            asyncio.run(integration.process_profile_embedding(db, record, StructuredProfile(resumen_publico=""), expected_revision="old-confirmation"))
            db.commit()
            assert record.embedding_perfil == [0.8] * 768


def test_recommendation_adapter_tracks_multiple_vacancies_and_full_capacity(world):
    _, engine = world
    with Session(engine) as db:
        event = db.get(Evento, 1)
        event.detalles_especificos = {"integrantes": 3, "roles": [{"id": "backend", "nombre": "Backend", "vacantes": 2}]}
        first = ParticipanteEvento(id_evento=1, id_usuario=2, rol="Backend")
        db.add(first)
        db.flush()
        mapped = event_from_orm(event, [first])
        assert mapped.state == "open"
        assert "Backend" in [r.value for r in mapped.outstanding_roles]
        second = ParticipanteEvento(id_evento=1, id_usuario=3, rol="Backend")
        mapped = event_from_orm(event, [first, second])
        assert mapped.state == "closed"
        assert "Backend" not in [r.value for r in mapped.outstanding_roles]
