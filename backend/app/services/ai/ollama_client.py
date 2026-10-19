from ollama import Client, ResponseError, RequestError

from app.services.ai.config import (
    OLLAMA_HOST,
    LLM_MODEL,
    EMBEDDING_MODEL,
)

class OllamaServiceError(Exception):
    """Error controlado del servicio de IA."""
    pass


class OllamaClient:
    def __init__(self):
        self.client = Client(
            host=OLLAMA_HOST,
            timeout=120.0,
        )

    def generate_text(self, prompt: str) -> str:
        if not isinstance(prompt, str) or not prompt.strip():
            raise ValueError("El promp no puede estar vacío.")

        try:
            response = self.client.chat(
                model=LLM_MODEL,
                messages=[
                    {
                        "role": "user",
                        "content": (
                            "Eres un asistente especializado en "
                            "analizar perfiles, habilidades y "
                            "requisitos de proyectos. "
                            "Responde en español."
                        ),
                    },
                    {
                        "role": "user",
                        "content": prompt,
                    },
                ],
            )

            content = response.message.content

            if not content:
                raise OllamaServiceError("La respuesta del modelo está vacía.")

            return content

        except (ResponseError, RequestError) as error:
            raise OllamaServiceError(
                f"Error comunicarse con llama: {error}"
            ) from error

    def generate_embedding(self, text: str) -> list[float]:
        if not isinstance(text, str) or not text.strip():
            raise ValueError("El texto no puede estar vacío.")

        try:
            response = self.client.embed(
                model=EMBEDDING_MODEL,
                input=text,
            )

            if not response.embeddings:
                raise OllamaServiceError("El modelo no generó embeddings.")

            return list(response.embeddings[0])

        except (ResponseError, RequestError) as error:
            raise OllamaServiceError(
                f"Error al generar embedding: {error}"
            ) from error