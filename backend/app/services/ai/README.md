> Este documento describe el módulo y su entrega original. La aplicación ya integra IA, JWT, MySQL y React; consulta la [operación actual](../../../../docs/operacion/ia-perfiles-proyectos.md) para el flujo completo y sus permisos.

# Análisis de perfiles y eventos

Este módulo transforma descripciones en objetos Pydantic y vectores semánticos. No escribe en la base de datos ni decide compatibilidad entre personas y eventos.

## Configuración

`OLLAMA_HOST` (por defecto `http://127.0.0.1:11434`), `OLLAMA_LLM_MODEL` (`llama3.1:8b`) y `OLLAMA_EMBEDDING_MODEL` (`nomic-embed-text`) se leen en `config.py`. El modelo Nomic original produce 768 dimensiones; el módulo exige ese tamaño cuando se usa ese nombre de modelo. Otro modelo puede usar otra dimensión, pero la integración debe almacenar el nombre y evitar mezclar vectores incompatibles.

## API

```python
from app.services.ai.profile_parser import ProfileParser
from app.services.ai.event_parser import EventParser
from app.services.ai.embeddings import generate_profile_embedding, generate_event_embedding

profile = ProfileParser().parse_profile(
    "Sé Python. Me interesa robótica, pero debo aprender electrónica."
)
profile_vector = generate_profile_embedding(profile)

event = EventParser().parse_event(
    "Buscamos portero para fútbol amateur. Entrenamos sábados.",
    categoria_principal="deportivo",
    detalles_especificos={"modalidad": "amateur"},
)
event_vector = generate_event_embedding(event)
```

`StructuredProfile` conserva `habilidades`, `intereses`, `areas_mejora`, `experiencia` y `resumen_publico`. Por ejemplo, aprender electrónica queda en `areas_mejora`, nunca en `habilidades`. Si Llama devuelve un resumen vacío pero sí extrajo hechos útiles, el parser genera uno breve usando solo esos campos. Si no hay hechos útiles, puede quedar vacío.

`StructuredEventRequirements` separa `habilidades_obligatorias`, `habilidades_deseables`, `roles_buscados`, `intereses_relacionados` y `restricciones_explicitas`, además de categoría, título y resumen. `categoria_principal`, si se proporciona, prevalece sobre la categoría inferida. Los detalles son un objeto JSON opcional. Si el resumen viene vacío y hay requisitos explícitos, se construye solo con las listas extraídas. Ausencia de datos se representa con cadenas/listas vacías; no se infieren fechas, cupos ni ubicación.

`build_profile_embedding_text()` incluye habilidades, intereses y experiencia declarados. Excluye áreas por mejorar. `build_event_embedding_text()` etiqueta expresamente las capacidades obligatorias, deseables, roles buscados, intereses y condiciones. Ambas funciones son puras, deduplican valores, normalizan espacios y acotan el texto a 4000 caracteres. Un texto sin hechos útiles produce `ValueError` antes de invocar Nomic. El vector devuelto es una lista de floats finitos y no vacía. Los parsers aceptan un `OllamaClient` inyectado y los generadores aceptan `ai=` para pruebas.

Entradas vacías, tipos incorrectos y descripciones mayores a 20000 caracteres producen `ValueError`. Fallos de conexión, JSON inválido, esquema Pydantic inválido y vectores inválidos producen `OllamaServiceError`. Pydantic `model_validate_json()` valida los tipos y campos del JSON; JSON Schema guía la salida de Ollama, pero la extracción semántica todavía puede equivocarse. Debe revisarse la calidad antes de publicar resúmenes o usar vectores para decisiones.

## Integración futura

La capa de rutas puede guardar `profile.model_dump(mode="json")` en `perfiles_usuarios.perfil_estructurado_ia`, `profile.resumen_publico` en `resumen_publico_ia` y `profile_vector` en `embedding_perfil`. Puede guardar `event.model_dump(mode="json")` en `eventos.requisitos_ia` y `event_vector` en `embedding_requisitos`. Las descripciones originales quedan bajo control de las rutas. No sobrescribir `atributos_dinamicos`. La persistencia, los endpoints y el matching pertenecen a otras fases.

## Pruebas

Desde `backend`: `\.venv\Scripts\python.exe -m pytest tests -v`. La suite usa mocks y no requiere Ollama. Las pruebas reales con modelos instalados son manuales y deben usar descripciones sintéticas. Un resultado estructuralmente válido no garantiza interpretación correcta: comprobar especialmente negaciones, roles ya cubiertos y separación entre obligatorias y deseables.
