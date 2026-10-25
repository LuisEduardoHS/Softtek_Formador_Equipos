"""HTTP auth, reviewed AI persistence, and recoverable failures for 6A."""
import os
import asyncio

os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("AUTH_SECRET", "test-secret-for-six-a-with-at-least-32-characters")

import pytest
import sqlite3
from pathlib import Path
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.db.database import Base, get_db
from app.main import app
from app.models.evento import Evento
from app.models.participante import ParticipanteEvento
from app.models.usuario import PerfilUsuario, Usuario
from app.core.security import create_access_token
from app.services.ai.schemas import StructuredEventRequirements, StructuredProfile
from app.services.ai.ollama_client import OllamaServiceError
from app.services.ai import integration


@pytest.fixture
def context(monkeypatch):
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False},
                           poolclass=StaticPool)
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        db.add_all([
            Usuario(id_usuario=1, nombre="Ana", correo="a@example.test", carrera="Sistemas",
                    password_hash="hash", estado_cuenta="Activa"),
            Usuario(id_usuario=2, nombre="Luis", correo="b@example.test", carrera="Arte",
                    password_hash="hash", estado_cuenta="Activa"),
        ])
        db.commit()

    def override():
        with Session(engine) as db:
            yield db

    app.dependency_overrides[get_db] = override
    monkeypatch.setenv("AUTH_SECRET", "test-secret-for-six-a-with-at-least-32-characters")
    client = TestClient(app)
    yield client, engine
    app.dependency_overrides.clear()
    client.close()
    engine.dispose()


def headers(user_id):
    return {"Authorization": f"Bearer {create_access_token(user_id)}"}


def profile_payload():
    return {"nombre": "Ana", "carrera": "Sistemas",
            "fortalezas": [{"nombre": "Python", "nivel": "intermedio"}],
            "reforzar": ["Blender"], "intereses": ["Videojuegos"],
            "experiencia": [], "resumen_publico": "Programo en Python.",
            "disponibilidad": ["dom-tarde"], "visibilidad": {
                "fortalezas": True, "intereses": True, "disponibilidad": True,
                "reforzar": False, "correo": False}}


def requirements():
    return {"categoria": "Academico", "titulo_normalizado": "Tutorías",
            "resumen": "Buscamos Python", "habilidades_obligatorias": ["Python"],
            "habilidades_deseables": ["Docker"], "roles_buscados": ["backend"],
            "intereses_relacionados": [], "restricciones_explicitas": ["domingos"]}


def _merge_event(engine):
    with Session(engine) as db:
        db.add(Evento(id_evento=71, creador_id=1, titulo="Proyecto integrado",
                      categoria_principal="Academico", estado="Abierto",
                      detalles_especificos={"integrantes": 3, "roles": [
                          {"id": "backend", "nombre": "Backend", "habilidades": ["Python"]}]},
                      requisitos_ia=requirements(), requisitos_confirmados_at=integration.utc_now(),
                      requisitos_fuente_revision="old", estado_ia="listo",
                      embedding_requisitos=[0.2] * 768, embedding_fuente_revision="old"))
        db.commit()


def test_merged_join_request_preserves_auth_and_creates_requester_membership(context):
    client, engine = context
    _merge_event(engine)
    body = {"rol_esperado": "backend", "mensaje_explicacion": "Puedo apoyar con Python"}
    url = "/eventos/71/solicitudes?solicitante_id=2"
    assert client.post(url, json=body).status_code == 401
    assert client.post(url, json=body, headers=headers(1)).status_code == 403
    sent = client.post(url, json=body, headers=headers(2))
    assert sent.status_code == 200, sent.text
    assert client.post(url, json=body, headers=headers(2)).status_code == 409
    request_id = sent.json()["id"]
    response = client.patch(f"/invitaciones/{request_id}", json={"estado": "Aceptada"},
                            headers=headers(1))
    assert response.status_code == 200, response.text
    with Session(engine) as db:
        member = db.query(ParticipanteEvento).filter_by(id_evento=71).one()
        assert member.id_usuario == 2
        assert member.rol == "Backend"
    event = client.get("/eventos/71", headers=headers(2)).json()
    assert event["creador_nombre"] == "Ana"
    assert event["detalles_especificos"]["roles"][0]["cubiertoPor"] == "2"
    assert "embedding_requisitos" not in event
    notifications = client.get("/notificaciones/2", headers=headers(2)).json()
    assert any("aceptó tu solicitud" in item["texto"] for item in notifications)


@pytest.mark.parametrize("category", ["Academico", "Personal", "Deportivo", "Videojuegos", "General"])
def test_merged_edit_preserves_categories_and_invalidates_old_ai_evidence(context, category):
    client, engine = context
    _merge_event(engine)
    body = {"categoria_principal": category, "descripcion_libre": "Descripción revisada",
            "integrantes": 3, "detalles_especificos": {"roles": [
                {"id": "backend", "nombre": "Backend", "habilidades": ["Go"]}]},
            "requisitos_ia": {"roles": []}}
    url = "/eventos/71?usuario_id=1"
    assert client.put(url, json=body).status_code == 401
    assert client.put(url, json=body, headers=headers(2)).status_code == 403
    response = client.put(url, json=body, headers=headers(1))
    assert response.status_code == 200, response.text
    assert response.json()["categoria_principal"] == category
    assert response.json()["detalles_especificos"]["tipo"] == category.casefold()
    assert response.json()["requisitos_confirmados"] is False
    with Session(engine) as db:
        event = db.get(Evento, 71)
        assert event.embedding_requisitos is None
        assert event.requisitos_confirmados_at is None
        assert event.requisitos_ia == {}
        assert event.requisitos_borrador_ia["habilidades_obligatorias"] == ["Python"]
        assert event.estado_ia == "pendiente_revision"


def test_auth_401_403_and_private_profile(context):
    client, _ = context
    assert client.get("/perfil/1").status_code == 401
    assert client.get("/eventos/").status_code == 401
    assert client.get("/perfil/1", headers=headers(2)).status_code == 403
    assert client.put("/perfil/1", json={"nombre": "Intruso"}, headers=headers(2)).status_code == 403
    assert client.get("/invitaciones/1", headers=headers(2)).status_code == 403
    assert client.get("/notificaciones/1", headers=headers(2)).status_code == 403
    assert client.get("/auth/me", headers=headers(1)).json()["id_usuario"] == 1
    assert client.get("/auth/me", headers={"Authorization": "Bearer invalid"}).status_code == 401


def test_invitation_actor_and_event_state(context):
    client, engine = context
    with Session(engine) as db:
        db.add(Evento(id_evento=7, creador_id=1, titulo="Proyecto",
                      categoria_principal="Academico", estado="Borrador"))
        db.commit()
    body = {"id_destinatario": 2, "id_evento": 7}
    assert client.post("/invitaciones/?de_id=1", json=body).status_code == 401
    assert client.post("/invitaciones/?de_id=1", json=body, headers=headers(2)).status_code == 403
    assert client.post("/invitaciones/?de_id=1", json=body, headers=headers(1)).status_code == 409
    with Session(engine) as db:
        db.get(Evento, 7).estado = "Abierto"
        db.commit()
    sent = client.post("/invitaciones/?de_id=1", json=body, headers=headers(1))
    assert sent.status_code == 200
    invitation_id = sent.json()["id"]
    assert client.patch(f"/invitaciones/{invitation_id}", json={"estado": "Aceptada"},
                        headers=headers(1)).status_code == 403


def test_register_login_and_inactive_account(context):
    client, engine = context
    register = client.post("/auth/registro", json={
        "nombre": "Eva", "correo": "eva@example.com", "carrera": "Diseño",
        "password": "correct-horse-battery-staple"})
    assert register.status_code == 200, register.text
    token = register.json()["access_token"]
    assert client.get("/auth/me", headers={"Authorization": f"Bearer {token}"}).status_code == 200
    assert client.post("/auth/login", json={"correo": "eva@example.com", "password": "wrong"}).status_code == 401
    login = client.post("/auth/login", json={
        "correo": "eva@example.com", "password": "correct-horse-battery-staple"})
    assert login.status_code == 200
    with Session(engine) as db:
        user = db.get(Usuario, register.json()["usuario"]["id_usuario"])
        user.estado_cuenta = "Inactiva"
        db.commit()
    assert client.get("/auth/me", headers={"Authorization": f"Bearer {token}"}).status_code == 403
    assert client.post("/auth/login", json={
        "correo": "eva@example.com", "password": "correct-horse-battery-staple"}).status_code == 403


def test_profile_review_persists_only_confirmed_and_embedding_metadata(context, monkeypatch):
    client, engine = context
    monkeypatch.setattr("app.api.routes.perfiles.ProfileParser.parse_profile",
                        lambda self, description: StructuredProfile(
                            habilidades=["Python"], areas_mejora=["Blender"],
                            intereses=["Videojuegos"], experiencia=[], resumen_publico="Python"))
    monkeypatch.setattr(integration, "generate_reviewed_profile_vector", lambda _: [0.1] * 768)
    suggestion = client.post("/perfil/interpretar", json={
        "fortalezas": "Tengo Python", "reforzar": "Quiero aprender Blender",
        "intereses": "Videojuegos"}, headers=headers(1))
    assert suggestion.status_code == 200
    assert suggestion.json()["origen"] == "ia_sin_confirmar"
    with Session(engine) as db:
        draft = db.get(PerfilUsuario, 1)
        assert draft.perfil_estructurado_ia is None
        assert draft.perfil_borrador_ia["habilidades"] == ["Python"]
    result = client.post("/perfil/confirmar", json=profile_payload(), headers=headers(1))
    assert result.status_code == 200, result.text
    assert result.json()["perfil_estado_ia"] == "listo"
    assert "embedding_perfil" not in result.json()
    with Session(engine) as db:
        saved = db.get(PerfilUsuario, 1)
        assert saved.perfil_estructurado_ia["habilidades"] == ["Python"]
        assert saved.perfil_estructurado_ia["areas_mejora"] == ["Blender"]
        assert saved.perfil_embedding_fuente_revision == saved.perfil_fuente_revision
        assert saved.perfil_embedding_model == "nomic-embed-text"
        assert len(saved.embedding_perfil) == 768
    public = client.get("/perfil/publico/1", headers=headers(2)).json()
    assert "perfil_borrador_ia" not in public
    assert "embedding_perfil" not in public
    assert "reforzar" not in public["datos_crudos"]


def test_profile_confirmation_requires_explicit_visibility(context):
    client, _ = context
    invalid = profile_payload()
    invalid["visibilidad"] = {"correo": False}
    assert client.post("/perfil/confirmar", json=invalid, headers=headers(1)).status_code == 422


def test_parser_failure_keeps_profile_draft_and_manual_confirmation(context, monkeypatch):
    client, engine = context
    def fail(*_):
        raise OllamaServiceError("offline")
    monkeypatch.setattr("app.api.routes.perfiles.ProfileParser.parse_profile", fail)
    monkeypatch.setattr(integration, "generate_reviewed_profile_vector", fail)
    response = client.post("/perfil/interpretar", json={"fortalezas": "Python"}, headers=headers(1))
    assert response.status_code == 503
    with Session(engine) as db:
        assert db.get(PerfilUsuario, 1).datos_crudos["borrador_texto_ia"]["fortalezas"] == "Python"
    saved = client.post("/perfil/confirmar", json=profile_payload(), headers=headers(1))
    assert saved.status_code == 200
    assert saved.json()["perfil_estado_ia"] == "pendiente_embedding"
    with Session(engine) as db:
        assert db.get(PerfilUsuario, 1).embedding_perfil is None


def test_event_creator_spoof_review_and_private_draft(context, monkeypatch):
    client, engine = context
    monkeypatch.setattr(integration, "generate_reviewed_event_vector", lambda _: [0.2] * 768)
    base = {"titulo": "Tutorías", "categoria_principal": "Academico",
            "descripcion_libre": "Buscamos Python y Docker es deseable.",
            "detalles_especificos": {"roles": [{"nombre": "backend", "habilidades": ["Python"]}]}}
    assert client.post("/eventos/", json={**base, "creador_id": 2}, headers=headers(1)).status_code == 403
    assert client.post("/eventos/", json={**base, "requisitos_ia": {"admin": True}},
                       headers=headers(1)).status_code == 422
    assert client.post("/eventos/", json={**base, "requisitos_confirmados": requirements()},
                       headers=headers(1)).status_code == 422
    draft = client.post("/eventos/", json=base, headers=headers(1))
    assert draft.status_code == 201, draft.text
    event_id = draft.json()["id_evento"]
    assert draft.json()["estado"] == "Borrador"
    assert client.get(f"/eventos/{event_id}", headers=headers(2)).status_code == 404
    assert client.post(f"/eventos/{event_id}/confirmar", json={"requirements": requirements(), "confirmado_por_creador": True},
                       headers=headers(2)).status_code == 403
    confirmed = client.post(f"/eventos/{event_id}/confirmar", json={"requirements": requirements(), "confirmado_por_creador": True},
                            headers=headers(1))
    assert confirmed.status_code == 200, confirmed.text
    assert confirmed.json()["estado_ia"] == "listo"
    assert "embedding_requisitos" not in confirmed.json()
    with Session(engine) as db:
        event = db.get(Evento, event_id)
        assert event.requisitos_ia["habilidades_obligatorias"] == ["Python"]
        assert event.embedding_fuente_revision == event.requisitos_fuente_revision
        assert len(event.embedding_requisitos) == 768


def test_event_interpretation_is_unconfirmed_and_recoverable(context, monkeypatch):
    client, _ = context
    monkeypatch.setattr("app.api.routes.eventos.EventParser.parse_event",
                        lambda self, description, category, details: StructuredEventRequirements(
                            categoria=category, habilidades_obligatorias=["Python"]))
    payload = {"descripcion_libre": "Se requiere Python", "categoria_principal": "Academico"}
    suggestion = client.post("/eventos/interpretar", json=payload, headers=headers(1))
    assert suggestion.status_code == 200
    assert suggestion.json()["origen"] == "ia_sin_confirmar"
    assert client.get("/eventos/", headers=headers(1)).json() == []
    def fail(*_):
        raise OllamaServiceError("offline")
    monkeypatch.setattr("app.api.routes.eventos.EventParser.parse_event", fail)
    assert client.post("/eventos/interpretar", json=payload, headers=headers(1)).status_code == 503


def test_direct_reviewed_event_persists_when_embedding_fails(context, monkeypatch):
    client, engine = context
    def fail(_):
        raise OllamaServiceError("offline")
    monkeypatch.setattr(integration, "generate_reviewed_event_vector", fail)
    created = client.post("/eventos/", json={
        "titulo": "Game Jam", "categoria_principal": "Academico",
        "descripcion_libre": "Python obligatorio; Docker deseable.",
        "requisitos_confirmados": requirements(), "confirmado_por_creador": True,
    }, headers=headers(1))
    assert created.status_code == 201, created.text
    assert created.json()["estado"] == "Abierto"
    assert created.json()["estado_ia"] == "pendiente_embedding"
    with Session(engine) as db:
        event = db.get(Evento, created.json()["id_evento"])
        assert event.requisitos_confirmados_at is not None
        assert event.embedding_requisitos is None


def test_late_embedding_does_not_replace_newer_revision(context, monkeypatch):
    _, engine = context
    with Session(engine) as db:
        profile = PerfilUsuario(usuario_id=1, perfil_fuente_revision="old",
                                perfil_confirmado_at=integration.utc_now(), perfil_estado_ia="pendiente_embedding")
        db.add(profile)
        db.commit()
    def late_result(_):
        with Session(engine) as other:
            other.get(PerfilUsuario, 1).perfil_fuente_revision = "new"
            other.commit()
        return [1.0] * 768
    monkeypatch.setattr(integration, "generate_reviewed_profile_vector", late_result)
    with Session(engine) as db:
        profile = db.get(PerfilUsuario, 1)
        structured = StructuredProfile(habilidades=["Python"], resumen_publico="Python")
        asyncio.run(integration.process_profile_embedding(db, profile, structured))
        db.commit()
        assert profile.embedding_perfil is None
        assert profile.perfil_fuente_revision == "new"


def test_versioned_migration_preserves_legacy_rows(tmp_path, monkeypatch):
    database = tmp_path / "legacy.sqlite"
    with sqlite3.connect(database) as connection:
        connection.execute("CREATE TABLE perfiles_usuarios (usuario_id INTEGER PRIMARY KEY, datos_crudos JSON)")
        connection.execute("CREATE TABLE eventos (id_evento INTEGER PRIMARY KEY, titulo TEXT, requisitos_ia JSON, embedding_requisitos JSON)")
        connection.execute("INSERT INTO perfiles_usuarios VALUES (4, '{\"fortalezas\":[\"Python\"]}')")
        connection.execute("INSERT INTO eventos VALUES (9, 'Legado', '{\"roles\":[\"backend\"]}', '{}')")
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{database.as_posix()}")
    config = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
    config.set_main_option("script_location", str(Path(__file__).resolve().parents[1] / "alembic"))
    command.upgrade(config, "head")
    with sqlite3.connect(database) as connection:
        profile_columns = {row[1] for row in connection.execute("PRAGMA table_info(perfiles_usuarios)")}
        event_columns = {row[1] for row in connection.execute("PRAGMA table_info(eventos)")}
        assert {"perfil_estructurado_ia", "embedding_perfil", "perfil_estado_ia"} <= profile_columns
        assert {"estado_ia", "embedding_model", "requisitos_confirmados_at"} <= event_columns
        assert connection.execute("SELECT datos_crudos FROM perfiles_usuarios WHERE usuario_id=4").fetchone()[0] == '{"fortalezas":["Python"]}'
        assert connection.execute("SELECT titulo FROM eventos WHERE id_evento=9").fetchone()[0] == "Legado"
