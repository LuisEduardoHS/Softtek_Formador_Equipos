"""Fase 6B snapshots, access checks and public HTTP contracts."""
import os

os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("AUTH_SECRET", "test-secret-for-six-b-with-at-least-32-characters")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.core.security import create_access_token
from app.db.database import Base, get_db
from app.main import app
from app.models.evento import Evento
from app.models.participante import ParticipanteEvento
from app.models.solicitud import SolicitudEquipo
from app.models.usuario import PerfilUsuario, Usuario
from app.services.ai.recommendations.orm_adapter import candidate_from_orm, event_from_orm
from app.services.ai.integration import utc_now


def _profile(user_id, skills, *, consent=True, goals=None, confirmed=True, visible=True):
    return PerfilUsuario(
        usuario_id=user_id,
        datos_crudos={"fortalezas": [{"nombre": value, "nivel": None} for value in skills],
                      "intereses": [], "disponibilidad": ["domingos"],
                      "visibilidad": {"fortalezas": visible, "intereses": True,
                                      "disponibilidad": True, "reforzar": False, "correo": False},
                      "pausado": False, "consentimiento_recomendaciones": consent},
        perfil_estructurado_ia={"habilidades": skills, "areas_mejora": goals or [],
                               "intereses": [], "experiencia": [], "resumen_publico": ""} if confirmed else None,
        perfil_confirmado_at=utc_now() if confirmed else None,
        perfil_estado_ia="pendiente_embedding" if confirmed else "pendiente_revision",
    )


@pytest.fixture
def snapshot(monkeypatch):
    monkeypatch.setenv("AUTH_SECRET", "test-secret-for-six-b-with-at-least-32-characters")
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        for uid in range(1, 7):
            db.add(Usuario(id_usuario=uid, nombre=f"Persona {uid}", correo=f"user{uid}@example.com",
                           carrera="Sistemas", password_hash="hash", estado_cuenta="Activa"))
        db.flush()
        db.add_all([
            _profile(1, []), _profile(2, ["Python"]),
            _profile(3, ["Python"], consent=False),
            _profile(4, [], goals=["Python"]), _profile(5, ["Python"]),
            _profile(6, []),
        ])
        db.add(Evento(id_evento=11, creador_id=1, titulo="Proyecto Python",
                      categoria_principal="Academico", descripcion_libre="Proyecto académico",
                      estado="Abierto", requisitos_confirmados_at=utc_now(),
                      estado_ia="pendiente_embedding", requisitos_ia={
                          "categoria": "Academico", "titulo_normalizado": "Proyecto Python",
                          "resumen": "Buscamos Python", "habilidades_obligatorias": ["Python"],
                          "habilidades_deseables": ["Docker"], "roles_buscados": [],
                          "intereses_relacionados": [], "restricciones_explicitas": [],
                      }))
        db.add(ParticipanteEvento(id_evento=11, id_usuario=6, rol="Integrante"))
        db.add(SolicitudEquipo(id_evento=11, id_remitente=1, id_destinatario=5,
                               estado="Pendiente"))
        db.commit()

    def override():
        with Session(engine) as db:
            yield db

    app.dependency_overrides[get_db] = override
    client = TestClient(app)
    yield client, engine
    client.close()
    app.dependency_overrides.clear()
    engine.dispose()


def _auth(uid):
    return {"Authorization": f"Bearer {create_access_token(uid)}"}


def test_orm_evidence_consent_missing_vector_and_learning_goal(snapshot):
    _, engine = snapshot
    with Session(engine) as db:
        owner = candidate_from_orm(db.get(Usuario, 2), db.get(PerfilUsuario, 2))
        learner = candidate_from_orm(db.get(Usuario, 4), db.get(PerfilUsuario, 4))
        hidden = candidate_from_orm(db.get(Usuario, 3), db.get(PerfilUsuario, 3))
        event = event_from_orm(db.get(Evento, 11), db.query(ParticipanteEvento).all())
    assert owner.visibility == "visible"
    assert [item.value for item in owner.declared_skills] == ["Python"]
    assert owner.profile_embedding is None and owner.embedding_model is None
    assert learner.declared_skills == []
    assert learner.profile.areas_mejora == []
    assert hidden.visibility == "hidden"
    assert event.event_embedding is None
    assert event.confirmed_requirements[0].value == "Python"


def test_organizer_endpoint_filters_privacy_members_pending_and_scores(snapshot):
    client, _ = snapshot
    assert client.get("/recomendaciones/eventos/11/candidatos").status_code == 401
    assert client.get("/recomendaciones/eventos/11/candidatos", headers=_auth(2)).status_code == 403
    assert client.get("/recomendaciones/eventos/11/candidatos?top_n=21", headers=_auth(1)).status_code == 422
    response = client.get("/recomendaciones/eventos/11/candidatos", headers=_auth(1))
    assert response.status_code == 200, response.text
    items = response.json()
    assert [item["candidate_id"] for item in items] == [2, 4]
    assert items[0]["evidence_coverage"]["known"] >= 1
    assert "Python" in str(items[0]["explanation"])
    assert "Python" not in str(items[1]["explanation"].get("strengths", []))
    for item in items:
        assert not ({"nombre", "correo", "profile_embedding", "ranking_score", "score_components"} & item.keys())


def test_user_projects_permission_consent_and_pending(snapshot):
    client, engine = snapshot
    assert client.get("/recomendaciones/usuarios/2/proyectos", headers=_auth(1)).status_code == 403
    assert client.get("/recomendaciones/usuarios/3/proyectos", headers=_auth(3)).status_code == 403
    assert client.get("/recomendaciones/usuarios/5/proyectos", headers=_auth(5)).json() == []
    response = client.get("/recomendaciones/usuarios/2/proyectos", headers=_auth(2))
    assert response.status_code == 200, response.text
    assert [item["event_id"] for item in response.json()] == [11]
    assert "score" not in str(response.json())
    with Session(engine) as db:
        db.get(Evento, 11).estado = "Cerrado"
        db.commit()
    assert client.get("/recomendaciones/usuarios/2/proyectos", headers=_auth(2)).json() == []


def test_unconfirmed_legacy_requirements_never_become_confirmed(snapshot):
    client, engine = snapshot
    with Session(engine) as db:
        event = db.get(Evento, 11)
        event.requisitos_confirmados_at = None
        db.commit()
        mapped = event_from_orm(event, db.query(ParticipanteEvento).all())
    assert mapped.requirements is None
    assert mapped.confirmed_requirements is None
    response = client.get("/recomendaciones/eventos/11/candidatos", headers=_auth(1))
    assert response.status_code == 200
    assert all(item["eligibility"] == "needs_review" for item in response.json())


def test_notification_reuses_engine_and_does_not_reveal_hidden_profile(snapshot):
    client, _ = snapshot
    response = client.get("/notificaciones/1", headers=_auth(1))
    assert response.status_code == 200, response.text
    recommendations = [item for item in response.json() if item["grupo"] == "ia"]
    assert {item["id"] for item in recommendations} == {
        "recomendacion-11-2", "recomendacion-11-4"
    }
    assert all("user3@example.com" not in item["texto"] for item in recommendations)
    assert client.get("/notificaciones/1", headers=_auth(2)).status_code == 403


def test_adapter_discards_unversioned_or_stale_vectors(snapshot):
    _, engine = snapshot
    with Session(engine) as db:
        profile = db.get(PerfilUsuario, 2)
        profile.perfil_estado_ia = "listo"
        profile.embedding_perfil = [0.5] * 768
        profile.perfil_embedding_model = "nomic-embed-text"
        profile.perfil_embedding_pipeline = "profile-v1"
        profile.perfil_fuente_revision = "revision-actual"
        profile.perfil_embedding_fuente_revision = "revision-anterior"
        assert candidate_from_orm(db.get(Usuario, 2), profile).profile_embedding is None
        profile.perfil_embedding_fuente_revision = "revision-actual"
        assert len(candidate_from_orm(db.get(Usuario, 2), profile).profile_embedding) == 768
        profile.perfil_fuente_revision = None
        profile.perfil_embedding_fuente_revision = None
        assert candidate_from_orm(db.get(Usuario, 2), profile).profile_embedding is None


def test_recommendations_recheck_consent_and_membership_each_request(snapshot):
    client, engine = snapshot
    url = "/recomendaciones/eventos/11/candidatos"
    assert [item["candidate_id"] for item in client.get(url, headers=_auth(1)).json()] == [2, 4]
    with Session(engine) as db:
        db.get(PerfilUsuario, 2).datos_crudos = {
            **db.get(PerfilUsuario, 2).datos_crudos,
            "consentimiento_recomendaciones": False,
        }
        db.add(ParticipanteEvento(id_evento=11, id_usuario=4, rol="Integrante"))
        db.commit()
    assert client.get(url, headers=_auth(1)).json() == []


def test_missing_availability_is_unknown_not_confirmed_empty(snapshot):
    _, engine = snapshot
    with Session(engine) as db:
        profile = db.get(PerfilUsuario, 2)
        profile.datos_crudos = {key: value for key, value in profile.datos_crudos.items()
                              if key != "disponibilidad"}
        missing = candidate_from_orm(db.get(Usuario, 2), profile)
        assert missing.availability is None
        profile.datos_crudos = {**profile.datos_crudos, "disponibilidad": []}
        empty = candidate_from_orm(db.get(Usuario, 2), profile)
        assert empty.availability == []
