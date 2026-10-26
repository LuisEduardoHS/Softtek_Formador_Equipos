"""Regressions from recorded real Llama outputs and concurrent UI analysis."""
import json
from unittest.mock import MagicMock
import pytest
from app.services.ai.profile_parser import ProfileParser
from app.services.ai.event_parser import EventParser
from app.services.ai.matching.normalization import apply_equivalence
from test_qa_stability_security import qa, auth
from app.services.ai.schemas import StructuredProfile, StructuredEventRequirements
from app.models.usuario import PerfilUsuario
from sqlalchemy.orm import Session
from threading import Event
from concurrent.futures import ThreadPoolExecutor

def parse(source,**raw):
    ai=MagicMock();ai.generate_structured.return_value=json.dumps({'resumen_publico':'',**raw})
    return ProfileParser(ai).parse_profile(source)

def test_actual_long_output_keeps_working_with_git_and_fastapi():
    p=parse('Sé programar en Python y con SQL. Trabajo con Git. Uso FastAPI.',
            habilidades=['programar en Python','con SQL','trabajar con Git','usar FastAPI'])
    assert set(p.habilidades)=={'Python','SQL','Git','FastAPI'}

def test_actual_model_omitted_sport_skills_are_recovered_only_from_explicit_source():
    p=parse('Juego de portero y defensa. No tengo experiencia profesional.',habilidades=[],experiencia=['Juego de portero y defensa'])
    assert set(p.habilidades)=={'portero','defensa'}
    p=parse('Quiero aprender a jugar de portero. No sé jugar de defensa.',habilidades=['portero','defensa'])
    assert p.habilidades==[]

def test_actual_model_interest_wrapper_does_not_duplicate_a_label():
    p=parse('Habilidades declaradas: Sé Python.\nIntereses: Me interesa la educación.',
            habilidades=['Python'],intereses=['educación','Me interesa la educación'])
    assert p.intereses==['educación']

def test_explicit_prototyping_survives_a_separate_affirmative_clause():
    p=parse('Diseño interfaces UX/UI en Figma. Hago prototipado.',habilidades=['Diseño interfaces UX/UI','Figma','Prototipado'])
    assert set(p.habilidades)=={'UX/UI','Figma','prototipado'}

@pytest.mark.parametrize('alias,canonical',[('uso de FastAPI','FastAPI'),('trabajar con Git','Git'),('Juego de portero','portero')])
def test_reviewed_usage_labels_match_exact_catalog_without_stripping_intent(alias,canonical):
    assert apply_equivalence(alias)==apply_equivalence(canonical)
    assert apply_equivalence('No sé '+alias)!=apply_equivalence(canonical)
    assert apply_equivalence('Quiero aprender '+alias)!=apply_equivalence(canonical)

def test_actual_football_model_omission_keeps_the_full_requested_role_list():
    ai=MagicMock();ai.generate_structured.return_value=json.dumps({'restricciones_explicitas':['Se requiere saber jugar de portero.']})
    p=EventParser(ai).parse_event('Equipo de fútbol. Buscamos portero, defensa y delantero. Se requiere saber jugar de portero.','Deportivo')
    assert set(p.roles_buscados)=={'portero','defensa','delantero'}
    assert 'portero' in p.habilidades_obligatorias

def test_same_confirmed_skill_is_not_both_required_and_preferred():
    p=StructuredEventRequirements(habilidades_obligatorias=['SQL','Figma'],
        habilidades_deseables=['programar con SQL','figma','Git'])
    assert p.habilidades_obligatorias==['SQL','Figma']
    assert p.habilidades_deseables==['Git']

def test_existing_team_member_is_not_a_participation_constraint():
    ai=MagicMock();ai.generate_structured.return_value=json.dumps({'habilidades_obligatorias':['Figma'],
        'restricciones_explicitas':['Ya incorporamos especialista en bases de datos']})
    p=EventParser(ai).parse_event('Ya incorporamos especialista en bases de datos. Figma obligatorio.','Academico')
    assert p.habilidades_obligatorias==['Figma']
    assert p.restricciones_explicitas==[]


def test_old_analysis_cannot_overwrite_a_newer_input_while_both_are_running(qa,monkeypatch):
    client,engine=qa
    old_started,new_started,old_release,new_release=(Event() for _ in range(4))
    def parser(self,description):
        older='SQL' in description
        (old_started if older else new_started).set()
        assert (old_release if older else new_release).wait(10)
        return StructuredProfile(habilidades=['SQL' if older else 'Figma'],resumen_publico='')
    monkeypatch.setattr('app.api.routes.perfiles.ProfileParser.parse_profile',parser)
    with ThreadPoolExecutor(max_workers=2) as pool:
        old=pool.submit(client.post,'/perfil/interpretar',headers=auth(),json={'fortalezas':'Sé SQL.'})
        assert old_started.wait(5)
        new=pool.submit(client.post,'/perfil/interpretar',headers=auth(),json={'fortalezas':'Sé Figma.'})
        assert new_started.wait(5)
        try:
            old_release.set()
            old_response=old.result(5)
        finally:new_release.set()
        new_response=new.result(5)
    assert old_response.status_code==409
    assert new_response.status_code==200
    with Session(engine) as db:
        p=db.get(PerfilUsuario,1)
        assert p.datos_crudos['borrador_texto_ia']['fortalezas']=='Sé Figma.'
        assert p.perfil_borrador_ia['habilidades']==['Figma']
