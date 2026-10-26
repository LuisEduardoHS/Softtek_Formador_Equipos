"""The observed empty directory is consent, not missing embeddings or owner consent."""
import pytest
from sqlalchemy.orm import Session
from unittest.mock import MagicMock
from test_qa_stability_security import qa, auth, profile, event
from app.models.usuario import PerfilUsuario


@pytest.mark.parametrize('paused', [False, True])
def test_consent_only_update_preserves_confirmed_facts_and_pause(qa, monkeypatch, paused):
    client,engine=qa
    profile_vector=MagicMock(return_value=[1.0]*768)
    monkeypatch.setattr('app.services.ai.integration.generate_reviewed_profile_vector',profile_vector)
    monkeypatch.setattr('app.services.ai.integration.generate_reviewed_event_vector',lambda _: [1.0]*768)
    for uid in (1,2):
        body=profile();body['consentimiento_recomendaciones']=False
        body['pausado']=paused if uid==2 else False
        assert client.post('/perfil/confirmar',headers=auth(uid),json=body).status_code==200
    response=client.post('/eventos/',headers=auth(1),json=event())
    assert response.status_code==201
    path=f'/recomendaciones/eventos/{response.json()["id_evento"]}/candidatos'
    assert client.get(path,headers=auth(1)).json()==[]
    with Session(engine) as db:
        p=db.get(PerfilUsuario,2)
        source=(p.perfil_fuente_revision,p.perfil_embedding_fuente_revision,p.embedding_perfil,p.perfil_estructurado_ia,p.perfil_confirmado_at)
    payload={'datos_crudos':{'consentimiento_recomendaciones':True}}
    assert client.put('/perfil/2',headers=auth(1),json=payload).status_code==403
    profile_vector.reset_mock()
    enabled=client.put('/perfil/2',headers=auth(2),json=payload)
    assert enabled.status_code==200
    assert enabled.json()['datos_crudos']['consentimiento_recomendaciones'] is True
    assert enabled.json()['datos_crudos']['pausado'] is paused
    assert enabled.json()['perfil_estado_ia']=='listo'
    profile_vector.assert_not_called()
    # Owner consent remains false: it never grants or prevents seeing other opted-in candidates.
    recs=client.get(path,headers=auth(1))
    assert recs.status_code==200
    assert [r['candidate_id']for r in recs.json()]==([] if paused else [2])
    with Session(engine) as db:
        p=db.get(PerfilUsuario,2)
        assert (p.perfil_fuente_revision,p.perfil_embedding_fuente_revision,p.embedding_perfil,p.perfil_estructurado_ia,p.perfil_confirmado_at)==source
    disabled=client.put('/perfil/2',headers=auth(2),json={'datos_crudos':{'consentimiento_recomendaciones':False}})
    assert disabled.status_code==200
    assert client.get(path,headers=auth(1)).json()==[]
