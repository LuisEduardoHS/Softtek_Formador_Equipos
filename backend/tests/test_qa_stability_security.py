"""Regressions from the real QA audit; isolated HTTP/ORM, never the main DB."""
import os
import json
from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import uuid4
from threading import Barrier
from concurrent.futures import ThreadPoolExecutor

os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("AUTH_SECRET", "qa-regression-secret-with-at-least-32-characters")

import httpx
import pytest
from fastapi.testclient import TestClient
from passlib.context import CryptContext
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.main import app
from app.db.database import Base, get_db
from app.core.security import create_access_token
from app.models.usuario import Usuario, PerfilUsuario
from app.models.evento import Evento
from app.services.ai.ollama_client import OllamaClient, OllamaServiceError
from app.services.ai import integration
from app.services.ai.recommendations.orm_adapter import event_from_orm


@pytest.fixture
def qa(tmp_path, monkeypatch):
    monkeypatch.setenv("AUTH_SECRET", "qa-regression-secret-with-at-least-32-characters")
    engine = create_engine(f"sqlite:///{(tmp_path/'qa.sqlite').as_posix()}",
                           connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        db.add_all([Usuario(id_usuario=i, nombre=f"QA {i}", correo=f"qa{i}@example.com",
                            carrera="QA", password_hash="unused", estado_cuenta="Activa")
                    for i in (1, 2)])
        db.flush()
        db.add_all([PerfilUsuario(usuario_id=i, datos_crudos={}) for i in (1, 2)])
        db.commit()
    def override():
        with Session(engine) as db:
            yield db
    app.dependency_overrides[get_db] = override
    with TestClient(app, raise_server_exceptions=False) as client:
        yield client, engine
    app.dependency_overrides.clear()
    engine.dispose()


def auth(uid=1):
    return {"Authorization": "Bearer " + create_access_token(uid)}


def profile():
    return {"nombre": "QA", "carrera": "QA", "fortalezas": [{"nombre": "Python"}],
            "reforzar": [], "intereses": ["web"], "experiencia": [],
            "resumen_publico": "Python", "disponibilidad": ["lun-tarde"],
            "visibilidad": {"fortalezas": True, "intereses": True, "disponibilidad": True,
                            "reforzar": False, "correo": False},
            "consentimiento_recomendaciones": True}


def event():
    return {"titulo": "QA Python", "categoria_principal": "Academico",
            "descripcion_libre": "Python obligatorio para un proyecto ficticio.",
            "detalles_especificos": {"integrantes": 3, "roles": [
                {"id": "backend", "nombre": "Backend", "habilidades": ["Python"]}]},
            "requisitos_confirmados": {"categoria": "Academico", "habilidades_obligatorias": ["Python"],
                                       "roles_buscados": ["Backend"]},
            "confirmado_por_creador": True}


@pytest.mark.parametrize("raw", [
    {"visibilidad": ["not-an-object"]}, {"visibilidad": {"correo": "false"}},
    {"visibilidad": {"fortalezas": {}}}, {"visibilidad": {"unknown": True}},
    {"fortalezas": [{"nombre": {"bad": "object"}}]}, {"habilidades": [23]},
    {"intereses": [{"bad": "object"}]}, {"reforzar": "Docker"},
    {"disponibilidad": [False]}, {"bio": {}}, {"semestre": "one"}, {"pausado": "false"},
    {"consentimiento_recomendaciones": "true"}, {"experiencia": [{}]},
])
def test_qa01_invalid_self_profile_rejected_and_other_user_directory_survives(qa, raw):
    client, engine = qa
    assert client.put("/perfil/1", headers=auth(), json={"datos_crudos": raw}).status_code == 422
    directory = client.get("/perfil/estudiantes/", headers=auth(2))
    assert directory.status_code == 200
    assert {p["usuario_id"] for p in directory.json()} == {1, 2}
    with Session(engine) as db:
        assert db.get(PerfilUsuario, 1).datos_crudos == {}


@pytest.mark.parametrize("raw", [[], {"visibilidad": []}, {"visibilidad": {"correo": "yes"},
    "fortalezas": [{"nombre": {}}], "intereses": [{}], "bio": {}, "semestre": []}])
def test_qa01_legacy_damage_is_read_safely_without_persisting_repairs(qa, raw):
    client, engine = qa
    with Session(engine) as db:
        p = db.get(PerfilUsuario, 1)
        p.datos_crudos = raw
        p.atributos_dinamicos = ["bad"]
        db.commit()
    public = client.get("/perfil/publico/1", headers=auth(2))
    assert public.status_code == 200
    assert public.json()["correo"] is None
    assert client.get("/perfil/estudiantes/", headers=auth(2)).status_code == 200
    assert client.get("/perfil/1", headers=auth()).status_code == 200
    with Session(engine) as db:
        assert db.get(PerfilUsuario, 1).datos_crudos == raw


def test_qa01_legacy_structured_profile_does_not_send_objects_to_react(qa):
    client, engine = qa
    damaged = {"habilidades": [{}], "experiencia": [{}], "resumen_publico": {}}
    with Session(engine) as db:
        p = db.get(PerfilUsuario, 1)
        p.perfil_estructurado_ia = damaged
        p.perfil_estado_ia = "listo"
        db.commit()
    r = client.get("/perfil/1", headers=auth())
    assert r.status_code == 200 and r.json()["perfil_estructurado_ia"] is None
    with Session(engine) as db:
        assert db.get(PerfilUsuario, 1).perfil_estructurado_ia == damaged


@pytest.mark.parametrize("patch", [
    {"habilidades": [{"unexpected": "object"}]}, {"habilidades": "Python"},
    {"habilidades": [""]}, {"habilidades": ["x" * 151]}, {"habilidades": [False]},
    {"nombre": "x" * 51}, {"nombre": {}}, {"id": {}}, {"id": "x" * 101},
    {"vacantes": "2"}, {"indispensable": "false"},
])
def test_qa04_invalid_role_cannot_be_persisted(qa, patch):
    client, engine = qa
    body = event()
    body["detalles_especificos"]["roles"][0].update(patch)
    assert client.post("/eventos/", headers=auth(), json=body).status_code == 422
    with Session(engine) as db:
        assert db.query(Evento).count() == 0


def test_qa04_legacy_roles_are_safe_in_detail_list_and_team(qa):
    client, engine = qa
    with Session(engine) as db:
        db.add(Evento(id_evento=1, creador_id=1, titulo="Legado QA", categoria_principal="Academico",
                      estado="Abierto", detalles_especificos={"integrantes": "bad", "roles": [
                          {"id": {}, "nombre": "Backend", "vacantes": [],
                           "habilidades": [{"unexpected": "object"}, "Python"]}, None,
                          {"nombre": {"bad": "object"}}]}))
        db.commit()
    detail = client.get("/eventos/1", headers=auth(2))
    assert detail.status_code == 200
    roles = detail.json()["detalles_especificos"]["roles"]
    assert len(roles) == 1 and roles[0]["habilidades"] == ["Python"]
    assert isinstance(roles[0]["id"], str) and roles[0]["vacantes"] == 1
    assert client.get("/eventos/", headers=auth(2)).status_code == 200
    team = client.get("/equipos/1", headers=auth())
    assert team.status_code == 200
    assert team.json()[0]["proyecto"]["detalles_especificos"]["roles"][0]["habilidades"] == ["Python"]


def test_qa04_legacy_invalid_vacancies_do_not_break_recommendations():
    e = Evento(id_evento=1, creador_id=1, estado="Abierto", requisitos_confirmados_at=integration.utc_now(),
               requisitos_ia=event()["requisitos_confirmados"], detalles_especificos={"roles": [
                   {"nombre": "Backend", "vacantes": []}]})
    snapshot = event_from_orm(e, [])
    assert snapshot.outstanding_roles is None
    assert snapshot.requirements.habilidades_obligatorias == ["Python"]


@pytest.mark.parametrize("error", [ConnectionError("offline"), TimeoutError("timeout"), httpx.ReadTimeout("timeout")])
@pytest.mark.parametrize("method", ["generate_text", "generate_structured", "generate_embedding"])
def test_qa03_sdk_transport_errors_are_translated(error, method):
    ai = OllamaClient()
    ai.client = MagicMock()
    ai.client.chat.side_effect = error
    ai.client.embed.side_effect = error
    with pytest.raises(OllamaServiceError):
        getattr(ai, method)("QA Python", *([{"type": "object"}] if method == "generate_structured" else []))


def offline_sdk(monkeypatch):
    def fail(*args, **kwargs):
        raise ConnectionError("isolated offline endpoint")
    monkeypatch.setattr("ollama.Client.embed", fail)
    monkeypatch.setattr("ollama.Client.chat", fail)


def test_qa03_confirmations_and_idempotent_creation_survive_actual_sdk_error_type(qa, monkeypatch):
    client, engine = qa
    offline_sdk(monkeypatch)
    confirmed = client.post("/perfil/confirmar", headers=auth(), json=profile())
    assert confirmed.status_code == 200
    assert confirmed.json()["perfil_estado_ia"] == "pendiente_embedding"
    key = str(uuid4())
    hdrs = {**auth(), "Idempotency-Key": key}
    created = client.post("/eventos/", headers=hdrs, json=event())
    assert created.status_code == 201
    assert created.json()["estado_ia"] == "pendiente_embedding"
    replay = client.post("/eventos/", headers=hdrs, json=event())
    assert replay.status_code == 201 and replay.json()["id_evento"] == created.json()["id_evento"]
    changed = {**event(), "titulo": "Otra publicación"}
    assert client.post("/eventos/", headers=hdrs, json=changed).status_code == 409
    eid = created.json()["id_evento"]
    assert client.post(f"/eventos/{eid}/confirmar", headers=auth(), json={
        "requirements": event()["requisitos_confirmados"], "confirmado_por_creador": True}).status_code == 200
    with Session(engine) as db:
        assert db.query(Evento).count() == 1
        assert db.get(PerfilUsuario, 1).embedding_perfil is None
    monkeypatch.setattr("ollama.Client.embed", lambda *a, **kw: SimpleNamespace(embeddings=[[0.1]*768]))
    assert client.post("/perfil/embedding/reintentar", headers=auth()).json()["perfil_estado_ia"] == "listo"
    assert client.post(f"/eventos/{eid}/embedding/reintentar", headers=auth()).json()["estado_ia"] == "listo"


@pytest.mark.parametrize("previous_state", [None, "listo", "pendiente_embedding"])
def test_qa03_failed_interpretation_preserves_confirmed_state_and_draft(qa, monkeypatch, previous_state):
    client, engine = qa
    if previous_state:
        monkeypatch.setattr(integration, "generate_reviewed_profile_vector", lambda _: [0.1]*768)
        assert client.post("/perfil/confirmar", headers=auth(), json=profile()).status_code == 200
        with Session(engine) as db:
            p = db.get(PerfilUsuario, 1)
            p.perfil_estado_ia = previous_state
            old = p.perfil_estructurado_ia
            old_revision = p.perfil_fuente_revision
            db.commit()
    offline_sdk(monkeypatch)
    r = client.post("/perfil/interpretar", headers=auth(), json={"fortalezas": "Sé SQL"})
    assert r.status_code == 503
    assert client.post("/eventos/interpretar", headers=auth(), json={
        "descripcion_libre": "Python obligatorio", "categoria_principal": "Academico"}).status_code == 503
    with Session(engine) as db:
        p = db.get(PerfilUsuario, 1)
        assert p.datos_crudos["borrador_texto_ia"]["fortalezas"] == "Sé SQL"
        assert p.perfil_estado_ia == (previous_state or "interpretacion_pendiente")
        if previous_state:
            assert p.perfil_estructurado_ia == old and p.perfil_fuente_revision == old_revision
    if previous_state:
        public = client.get("/perfil/1", headers=auth()).json()
        assert public["perfil_estructurado_ia"]["habilidades"] == ["Python"]


def registration(password="QA-test-password", **patch):
    return {"nombre": "Cuenta QA", "correo": "new@example.com", "carrera": "QA", "password": password, **patch}


@pytest.mark.parametrize("password", ["", "short", "x"*129, "x"*8+"\x00", "x"*8+"\ud800"])
def test_qa02_registration_password_policy(qa, password):
    client, engine = qa
    r = client.post("/auth/registro", content=json.dumps(registration(password), ensure_ascii=True),
                    headers={"Content-Type": "application/json"})
    assert r.status_code == 422
    assert all("input" not in error for error in r.json()["detail"])
    with Session(engine) as db:
        assert db.query(Usuario).count() == 2


@pytest.mark.parametrize("password", ["A"*72+"SUFIJO-UNO", "ñ"*40+"🔐-uno"])
def test_qa02_new_long_ascii_unicode_passwords_are_not_truncated(qa, password):
    client, engine = qa
    r = client.post("/auth/registro", json=registration(password))
    assert r.status_code == 200
    email = "new@example.com"
    assert client.post("/auth/login", json={"correo": email, "password": password[:-1]+"X"}).status_code == 401
    assert client.post("/auth/login", json={"correo": email, "password": password}).status_code == 200
    with Session(engine) as db:
        assert db.get(Usuario, r.json()["usuario"]["id_usuario"]).password_hash.startswith("$bcrypt-sha256$")


@pytest.mark.parametrize("password", ["old", "ñandú-contraseña", "A"*72])
def test_qa02_legacy_bcrypt_login_migrates_without_reset(qa, password):
    client, engine = qa
    old_hash = CryptContext(schemes=["bcrypt"]).hash(password)
    with Session(engine) as db:
        db.get(Usuario, 1).password_hash = old_hash
        db.commit()
    assert client.post("/auth/login", json={"correo": "qa1@example.com", "password": password}).status_code == 200
    with Session(engine) as db:
        new_hash = db.get(Usuario, 1).password_hash
        assert new_hash != old_hash and new_hash.startswith("$bcrypt-sha256$")
    assert client.post("/auth/login", json={"correo": "qa1@example.com", "password": password}).status_code == 200


def test_qa02_ambiguous_legacy_long_password_rejected_without_upgrading(qa):
    client, engine = qa
    old_hash = CryptContext(schemes=["bcrypt"]).hash("A"*72+"original")
    with Session(engine) as db:
        db.get(Usuario, 1).password_hash = old_hash
        db.commit()
    r = client.post("/auth/login", json={"correo": "qa1@example.com", "password": "A"*72+"different"})
    assert r.status_code == 422 and "72" in r.json()["detail"]
    with Session(engine) as db:
        assert db.get(Usuario, 1).password_hash == old_hash


@pytest.mark.parametrize("patch", [{"nombre": "x"*151}, {"nombre": " "}, {"carrera": "x"*101},
                                    {"estado_geografico": "x"*51}, {"municipio": "x"*51}])
def test_qa13_registration_mysql_lengths_validated_before_insert(qa, patch):
    client, engine = qa
    assert client.post("/auth/registro", json=registration(**patch)).status_code == 422
    with Session(engine) as db:
        assert db.query(Usuario).count() == 2


def test_qa03_replay_is_actor_scoped_and_survives_project_edit(qa, monkeypatch):
    client, engine = qa
    monkeypatch.setattr(integration, "generate_reviewed_event_vector", lambda _: [0.1]*768)
    key = str(uuid4())
    hdrs = {**auth(), "Idempotency-Key": key}
    first = client.post("/eventos/", headers=hdrs, json=event()).json()
    assert not any(k.startswith("_creation_") for k in first["detalles_especificos"])
    other = client.post("/eventos/", headers={**auth(2), "Idempotency-Key": key}, json=event())
    assert other.status_code == 201 and other.json()["id_evento"] != first["id_evento"]
    updated = client.put(f'/eventos/{first["id_evento"]}?usuario_id=1', headers=auth(), json={
        "categoria_principal": "Academico", "descripcion_libre": "Texto revisado",
        "detalles_especificos": event()["detalles_especificos"], "integrantes": 3, "requisitos_ia": {}})
    assert updated.status_code == 200
    replay = client.post("/eventos/", headers=hdrs, json=event())
    assert replay.status_code == 201 and replay.json()["id_evento"] == first["id_evento"]
    assert replay.json()["descripcion_libre"] == "Texto revisado"
    with Session(engine) as db:
        assert db.query(Evento).count() == 2


def test_qa03_invalid_idempotency_key_or_reserved_metadata_rejected(qa):
    client, engine = qa
    assert client.post("/eventos/", headers={**auth(), "Idempotency-Key": "bad"}, json=event()).status_code == 422
    body = event()
    body["detalles_especificos"]["_creation_request_id"] = str(uuid4())
    assert client.post("/eventos/", headers=auth(), json=body).status_code == 422
    with Session(engine) as db:
        assert db.query(Evento).count() == 0


def test_qa03_concurrent_retries_create_one_event(qa, monkeypatch):
    client, engine = qa
    monkeypatch.setattr(integration, "generate_reviewed_event_vector", lambda _: [0.1]*768)
    key = str(uuid4())
    hdrs = {**auth(), "Idempotency-Key": key}
    barrier = Barrier(2)
    def create(_):
        barrier.wait()
        return client.post("/eventos/", headers=hdrs, json=event())
    with ThreadPoolExecutor(2) as pool:
        responses = list(pool.map(create, [1, 2]))
    assert [r.status_code for r in responses] == [201, 201]
    assert len({r.json()["id_evento"] for r in responses}) == 1
    with Session(engine) as db:
        assert db.query(Evento).count() == 1
