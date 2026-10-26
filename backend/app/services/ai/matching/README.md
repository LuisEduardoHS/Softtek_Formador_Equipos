> Este documento describe el módulo y su entrega original. La aplicación ya integra IA, JWT, MySQL y React; consulta la [operación actual](../../../../../docs/operacion/recomendaciones-equipos.md) para el flujo completo y sus permisos.

# Motor puro de matching — subfase 4.5

Este paquete ordena candidatos para **un evento** a partir de contratos ya validados. No consulta MySQL, no llama a Ollama y no expone un endpoint. Los escenarios de `backend/tests/test_matching_scenarios.py` evalúan la cadena completa de contratos, elegibilidad, requisitos, complementariedad, coseno, ranking y explicación con datos controlados.

## Entrada y uso

- `CandidateInput` identifica al candidato y separa `declared_skills`, `role_preferences`, `availability`, visibilidad, estado de cuenta, perfil estructurado y embedding. `profile.habilidades` no se promociona por sí solo a evidencia confirmada: las capacidades puntuables requieren `Evidence(kind="skill", source="user_declared", polarity="affirms", confirmed=True)` en `declared_skills`.
- `EventInput` contiene requisitos estructurados, `confirmed_requirements`, `outstanding_roles`, `explicit_constraints`, `participants` y embedding. Un texto extraído por IA sigue pendiente hasta que el organizador confirme el hecho pertinente. `participants=None` significa equipo desconocido; `[]` significa lista confirmada vacía.
- `MatchRequest` contiene un evento, candidatos únicos, `policy_version` y `top_n` opcional. La versión debe coincidir exactamente con `RankingPolicy.version`.
- `team_members` es un mapa opcional de ID a `CandidateInput` de integrantes confirmados cuyos perfiles son visibles para este proceso. `Participant.role` no demuestra habilidades. Si la composición necesaria está incompleta, el componente de complementariedad del ranking es `None`.

```python
from app.services.ai.matching.policy import RankingPolicy
from app.services.ai.matching.ranking import rank_candidates
from app.services.ai.matching.schemas import CandidateInput, EventInput, Evidence, MatchRequest

policy = RankingPolicy()
event = EventInput(
    event_id=10, creator_id=1, state="open",
    requirements={"categoria": "Académico", "habilidades_obligatorias": ["Python"]},
    confirmed_requirements=[Evidence(
        source="organizer_confirmed", kind="skill", value="Python",
        polarity="affirms", confirmed=True,
    )],
    participants=[], outstanding_roles=[],
)
candidate = CandidateInput(
    user_id=2, visibility="visible", account_state="active",
    declared_skills=[Evidence(
        source="user_declared", kind="skill", value="Python",
        polarity="affirms", confirmed=True,
    )],
)
request = MatchRequest(event=event, candidates=[candidate],
                       policy_version=policy.version, top_n=10)
results = rank_candidates(request, policy)
```

`rank_candidates` devuelve `list[MatchResult]` en orden determinista. Excluye candidatos `ineligible`, perfiles ocultos y visibilidad sin confirmar; mantiene los visibles `needs_review` después de los `eligible`. `top_n` se aplica tras ordenar. El adaptador futuro debe verificar autorización **antes** de construir estas entradas y nunca devolver directamente un `CandidateInput`.

## Evidencia, señales y política

`assess_requirements` clasifica cada requisito como `met`, `unmet_confirmed`, `unknown` o `not_applicable`. Una omisión y una extracción `ai_unreviewed` no son incumplimientos confirmados. Las áreas de mejora e intereses no acreditan habilidades. Las equivalencias son explícitas y versionadas (`UE5` ↔ `Unreal Engine 5` en el catálogo actual); no se infieren sinónimos ni nivel de dominio.

`RankingPolicy` trae pesos experimentales configurables que deben sumar 1: obligatorias **0.40**, complementariedad **0.25**, deseables **0.15**, coseno **0.10** e intereses/preferencias **0.10**. Por defecto exige al menos dos señales disponibles y un requisito conocido para colocar un resultado en el grupo con evidencia suficiente. Primero se ordena por elegibilidad; después por suficiencia de evidencia, puntuación, obligatorias cubiertas, complementariedad y `user_id`. Un `None` representa señal ausente y se excluye del promedio ponderado; un cero representa una señal evaluada sin crédito. `ranking_score` es un índice interno, **no** probabilidad ni porcentaje de éxito.

La similitud usa únicamente vectores existentes con dimensión, modelo y `embedding_source_version` compatibles. El coseno válido se transforma mediante `(coseno + 1) / 2` para la política; ausencia o incompatibilidad deja `semantic_similarity=None`. La complementariedad solo da crédito a requisitos o roles confirmados que el equipo aún necesita. Un interés temático es una señal débil de afinidad textual, no prueba de competencia. Las restricciones son estrictas solo si `EligibilityPolicy.strict_constraint_terms` las nombra; una contradicción confirmada prevalece sobre un coseno alto. Una afirmación de disponibilidad debe cubrir todas las partes explícitas de una condición conjunta; la negación confirmada de una parte puede contradecirla.

`MatchResult` incluye estado de elegibilidad, evaluaciones por requisito, cinco componentes (incluidos los ausentes), `evidence_coverage` y explicación determinista. Las frases sobre habilidades y restricciones requieren evidencia confirmada; los desconocidos se muestran como asuntos por verificar. No se incluyen datos de otros participantes ni se llama a un LLM para explicar. Las evidencias internas y `source_ref` están excluidas de la serialización pública; el adaptador todavía debe aplicar su propia política de privacidad.

## Evaluación de 4.5

Desde `backend/`:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Los fixtures cubren proyectos académicos, deportes, game jam/videojuegos y categoría general: habilidades obligatorias y deseables, rol vacante u ocupado, disponibilidad dominical, coseno alto frente a una contradicción estricta, perfil oculto, participante existente, intereses sin habilidad, equipo y embeddings desconocidos/incompatibles, orden estable y `top_n`. También verifican que una confirmación parcial como «domingos» no acredite «domingos en Monterrey». Son pruebas reproducibles del núcleo puro, **no** una medición de calidad con personas ni una validación de las extracciones del parser en producción.

## Límites y futura integración

### Interfaces backend inspeccionadas (22 de octubre de 2026)

| Fuente actual | Traducción necesaria para el motor |
| --- | --- |
| `models/usuario.py`: `Usuario.estado_cuenta`, `PerfilUsuario.datos_crudos`/`atributos_dinamicos` | Mapear estados como `Activa` a `active` solo con reglas explícitas; conservar procedencia y confirmación de habilidades, disponibilidad y preferencias. El ORM no declara vector ni perfil IA del usuario. |
| `models/evento.py`: `Evento.estado`, `requisitos_ia`, `embedding_requisitos` | Mapear `Abierto` a `open` y validar requisitos revisados por organizador. `requisitos_ia` y `embedding_requisitos` son JSON genéricos; no aportan por sí solos `Evidence`, modelo ni versión del vector. |
| `schemas/evento.py`: `EventoOut.embedding_requisitos` es `Dict[str, Any]` | Alinear en una tarea posterior con `event_embedding: list[float]` y metadatos antes de invocar coseno; no convertir un diccionario arbitrario en vector. |
| `api/routes/perfiles.py` y `eventos.py` | Hoy no construyen `MatchRequest` ni llaman al motor. La ruta de perfil devuelve nombre/correo; la respuesta de matching debe usar solo `MatchResult` autorizado. |
| Participantes y visibilidad | No hay ORM de participantes ni campo de visibilidad en los modelos inspeccionados; sin fuente fiable, `participants=None` y la complementariedad queda ausente. No asumir visibilidad pública. |

1. El adaptador backend debe mapear ORM/SQL reales a `CandidateInput` y `EventInput`, consultar por lotes candidatos y participantes, verificar identidad y permiso de visibilidad en servidor, y distinguir dato ausente, lista vacía confirmada y extracción IA pendiente. No existe adaptador en este paquete.
2. Debe persistir junto al vector el modelo, versión de origen y marca de actualización; el contrato actual solo compara cadenas de versión y no puede detectar por sí solo un embedding obsoleto respecto del texto. Los modelos distintos jamás se comparan aunque tengan igual dimensión.
3. El equipo debe acordar qué condiciones son realmente excluyentes, cómo representar varios cupos del mismo rol y qué hacer con evidencia contradictoria. La disponibilidad, ubicación o experiencia no se infieren a partir de un perfil incompleto.
4. Antes de exponer recomendaciones reales se necesitan contratos ORM/SQL consistentes, autorización y visibilidad verificadas, confirmación de requisitos por organizador, fuente fiable de participantes y evaluación humana por categoría. Medir errores de exclusión, cobertura, utilidad del orden, estabilidad y latencia; revisar pesos y equivalencias con esos datos.
5. Este trabajo no integra rutas, persistencia, frontend, generación de embeddings, parsers ni autenticación. El diseño de referencia está en `docs/arquitectura/diseno-matching.md`; ese documento describe una propuesta anterior al código y puede contener estados históricos.
