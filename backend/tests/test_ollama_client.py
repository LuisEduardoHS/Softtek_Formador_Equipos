
from unittest.mock import MagicMock

import pytest

from app.services.ai.ollama_client import OllamaClient, OllamaServiceError
from ollama import ResponseError, RequestError


@pytest.fixture
def ai_client():
    ai = OllamaClient()
    ai.client = MagicMock()
    return ai


def test_generate_text(ai_client):
    ai_client.client.chat.return_value.message.content = (
        "Python, electrónica y mecánica"
    )

    result = ai_client.generate_text(
        "Menciona tres habilidades para robótica"
    )

    assert result == "Python, electrónica y mecánica"
    ai_client.client.chat.assert_called_once()


def test_generate_embedding(ai_client):
    vector = [0.1] * 768
    ai_client.client.embed.return_value.embeddings = [vector]

    result = ai_client.generate_embedding(
        "Programador Python"
    )

    assert len(result) == 768
    assert result == vector
    ai_client.client.embed.assert_called_once()


def test_generate_text_empty(ai_client):
    with pytest.raises(ValueError):
        ai_client.generate_text("")


def test_generate_embedding_empty(ai_client):
    with pytest.raises(ValueError):
        ai_client.generate_embedding("")



def test_generate_text_empty_response(ai_client):
    ai_client.client.chat.return_value.message.content = ""

    with pytest.raises(
        OllamaServiceError,
        match="La respuesta del modelo está vacía"
    ):
        ai_client.generate_text("Hola")


def test_ollama_connection_error(ai_client):
    ai_client.client.chat.side_effect = RequestError("No se pudo conectar con Ollama")

    with pytest.raises(
        OllamaServiceError,
        match="Error comunicarse con llama"
    ):
        ai_client.generate_text("Hola")


def test_ollama_model_not_found(ai_client):
    ai_client.client.embed.side_effect = ResponseError("model not found", status_code=404)

    with pytest.raises(
        OllamaServiceError,
        match="Error al generar embedding"
    ):
        ai_client.generate_embedding("Programador Python")