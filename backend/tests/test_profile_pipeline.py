import json
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from ollama import RequestError, ResponseError

from app.services.ai.embeddings import build_profile_embedding_text, generate_profile_embedding
from app.services.ai.ollama_client import OllamaClient, OllamaServiceError
from app.services.ai.profile_parser import ProfileParser
from app.services.ai.schemas import StructuredProfile


def profile_json():
    return json.dumps({
        "habilidades": ["Python", "C++"],
        "intereses": ["robótica"],
        "areas_mejora": ["electrónica"],
        "experiencia": ["dos hackatones"],
        "resumen_publico": "Programa en Python y C++ y participó en dos hackatones.",
    })


@pytest.fixture
def ai():
    client = OllamaClient()
    client.client = MagicMock()
    return client


def test_structured_call_and_profile(ai):
    ai.client.chat.return_value.message.content = profile_json()
    profile = ProfileParser(ai).parse_profile("Sé Python; debo aprender electrónica.")
    assert profile.habilidades == ["Python", "C++"]
    kwargs = ai.client.chat.call_args.kwargs
    assert kwargs["format"] == StructuredProfile.model_json_schema()
    assert kwargs["options"] == {"temperature": 0}
    assert [m["role"] for m in kwargs["messages"]] == ["system", "user"]
    assert "electrónica" not in build_profile_embedding_text(profile)


@pytest.mark.parametrize("prompt,schema", [("", {"type": "object"}), ("x", {}), (1, {"type": "object"})])
def test_structured_rejects_bad_inputs(ai, prompt, schema):
    with pytest.raises(ValueError):
        ai.generate_structured(prompt, schema)
    ai.client.chat.assert_not_called()


@pytest.mark.parametrize("content", ["", "no json", "[]"])
def test_structured_rejects_bad_response(ai, content):
    ai.client.chat.return_value.message.content = content
    with pytest.raises(OllamaServiceError):
        ai.generate_structured("x", {"type": "object"})


@pytest.mark.parametrize("error", [RequestError("offline"), ResponseError("missing", status_code=404)])
def test_structured_translates_transport_errors(ai, error):
    ai.client.chat.side_effect = error
    with pytest.raises(OllamaServiceError) as caught:
        ai.generate_structured("x", {"type": "object"})
    assert caught.value.__cause__ is error


@pytest.mark.parametrize("description", ["", " ", 5, "x" * 20001])
def test_profile_rejects_bad_input(ai, description):
    with pytest.raises(ValueError):
        ProfileParser(ai).parse_profile(description)


def test_profile_rejects_invalid_schema(ai):
    ai.generate_structured = MagicMock(return_value='{"habilidades": "Python"}')
    with pytest.raises(OllamaServiceError):
        ProfileParser(ai).parse_profile("Sé Python")


def test_profile_embedding_one_call(ai):
    profile = StructuredProfile.model_validate_json(profile_json())
    ai.generate_embedding = MagicMock(return_value=[0.1] * 768)
    result = generate_profile_embedding(profile, ai)
    assert len(result) == 768
    ai.generate_embedding.assert_called_once()
    assert "electrónica" not in ai.generate_embedding.call_args.args[0]


def test_profile_summary_fallback_uses_only_extracted_facts(ai):
    ai.generate_structured = MagicMock(return_value=json.dumps({
        "habilidades": ["Python"], "areas_mejora": ["electrónica"],
        "resumen_publico": "",
    }))
    profile = ProfileParser(ai).parse_profile("Sé Python; debo aprender electrónica")
    assert profile.resumen_publico == "Habilidades declaradas: Python"


@pytest.mark.parametrize("vector", [[], [float("nan")] * 768, [0.1] * 3])
def test_profile_embedding_rejects_bad_vectors(ai, vector):
    ai.generate_embedding = MagicMock(return_value=vector)
    profile = StructuredProfile(habilidades=["Python"], resumen_publico="")
    with pytest.raises(OllamaServiceError):
        generate_profile_embedding(profile, ai)


def test_profile_embedding_rejects_no_useful_facts(ai):
    profile = StructuredProfile(areas_mejora=["Python"], resumen_publico="")
    with pytest.raises(ValueError):
        generate_profile_embedding(profile, ai)


def test_raw_embedding_validation(ai):
    ai.client.embed.return_value = SimpleNamespace(embeddings=[[float("inf")] * 768])
    with pytest.raises(OllamaServiceError):
        ai.generate_embedding("x")
