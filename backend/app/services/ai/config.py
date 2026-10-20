import os

OLLAMA_HOST = os.getenv(
    "OLLAMA_HOST",
    "http://127.0.0.1:11434"
)

LLM_MODEL = os.getenv(
    "OLLAMA_LLM_MODEL",
    "llama3.1:8b"
)

EMBEDDING_MODEL = os.getenv(
    "OLLAMA_EMBEDDING_MODEL",
    "nomic-embed-text"
)