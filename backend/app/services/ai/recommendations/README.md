# Recomendaciones de candidatos y proyectos (Fase 5)

Este paquete implementa servicios **puros** sobre instantáneas ya autorizadas. No consulta MySQL, no valida credenciales, no escribe solicitudes, no ejecuta tareas periódicas y no expone rutas. Usa el motor de `matching/` para elegibilidad, cobertura de requisitos y ranking. Los contextos de autorización deben construirse en un futuro adaptador confiable, nunca desde datos enviados por el cliente.

## Contratos y flujo

| Función | Entrada principal | Resultado |
| --- | --- | --- |
| `recommend_candidates` | `EventInput`, secuencia de `CandidateInput`, `OrganizerRecommendationContext` | `list[CandidateRecommendation]` para el organizador autorizado |
| `recommend_projects` | `CandidateInput`, secuencia de `EventInput`, `UserRecommendationContext` | `list[ProjectRecommendation]` para el usuario autorizado |
| `personalize_recommendation` | Un DTO público y solicitud explícita `use_llm=True` | Mismo tipo de DTO con formulación aprobada o explicación determinista |
| `build_snapshot_fingerprint` | DTO, entradas, contexto, `SourceVersions`, `RankingPolicy` | `SnapshotFingerprint` interno para comparar vigencia |
| `assess_freshness` | Huella anterior y huella actual del mismo par y audiencia | `current`, `stale` o `unknown`, con componentes afectados |
| `is_repeated_recommendation` | Dos huellas | `True`, `False` o `None` si faltan datos |
| `same_action_pair` | Dos DTO; ID de usuario para un resultado de proyectos | Coincidencia del par evento/persona, independiente de la audiencia |
| `classify_pair_records` / `context_action_state` | Solicitudes, participantes o contexto verificados | Estado de acción; **no** autorización para actuar |

`CandidateInput` y `EventInput` provienen de `matching.schemas`. El adaptador debe distinguir `None` (no se conoce o no se consultó) de `[]` (consulta completa y vacía). Las evidencias llevan `kind`, `polarity`, `source` y `confirmed`. Una extracción `ai_unreviewed`, un interés o un área de mejora no prueban una habilidad. Solo se aplican las equivalencias explícitas y versionadas de `matching.normalization`.

La política por defecto es `RankingPolicy()`. Sus pesos y reglas de elegibilidad se configuran allí; este paquete no calcula otro score. `top_n` debe ser positivo. La recomendación de proyectos ordena grupos conservadores de elegibilidad y evidencia entre eventos, y luego usa ajuste de requisitos confirmados e ID de evento para desempatar. Los scores calculados por evento no se comparan como si fueran porcentajes de compatibilidad. Las listas son reproducibles para entradas y política idénticas.

`eligible` no significa que una invitación o solicitud esté autorizada. `needs_review` exige revisar hechos faltantes o contradictorios. `evidence_group="insufficient_evidence"` no equivale a incompatibilidad: puede acompañar a cualquiera de esos estados públicos. Los candidatos `ineligible` no aparecen. Se omiten creador, miembros e invitaciones o solicitudes pendientes según el sentido de la recomendación; también se excluyen eventos cerrados y recursos fuera del alcance verificado. Un perfil oculto nunca aparece en la salida para organizadores.

## Ejemplo mínimo de uso puro

```python
from app.services.ai.matching.schemas import CandidateInput, EventInput, Evidence
from app.services.ai.recommendations import (
    OrganizerRecommendationContext, UserRecommendationContext,
    recommend_candidates, recommend_projects,
)

python_confirmado = Evidence(
    source="user_declared", kind="skill", value="Python",
    polarity="affirms", confirmed=True,
)
requisito_confirmado = Evidence(
    source="organizer_confirmed", kind="skill", value="Python",
    polarity="affirms", confirmed=True,
)
persona = CandidateInput(
    user_id=2, visibility="visible", account_state="active",
    declared_skills=[python_confirmado],
)
proyecto = EventInput(
    event_id=10, creator_id=1, state="open", participants=[],
    requirements={"categoria": "Académico", "habilidades_obligatorias": ["Python"]},
    confirmed_requirements=[requisito_confirmado], outstanding_roles=[],
    explicit_constraints=[],
)

# Estos contextos son ejemplos de hechos ya comprobados por un adaptador de servidor.
organizador = OrganizerRecommendationContext(
    authenticated_organizer_id=1, authorized_event_id=10,
    discoverable_candidate_ids=frozenset({2}), confirmed_member_ids=frozenset(),
    pending_candidate_ids=frozenset(),
)
usuario = UserRecommendationContext(
    authenticated_user_id=2, discovery_consent=True,
    discoverable_event_ids=frozenset({10}),
    confirmed_member_event_ids=frozenset(),
    pending_invitation_event_ids=frozenset(),
    pending_application_event_ids=frozenset(),
)

para_organizador = recommend_candidates(proyecto, [persona], organizador, top_n=5)
para_usuario = recommend_projects(persona, [proyecto], usuario, top_n=5)
```

Los DTO contienen ID, estado de elegibilidad, grupo y cobertura de evidencia, explicación pública y versión de política. No contienen perfil completo, referencias de evidencia, vectores ni score interno. Si el llamador conserva entradas privadas para construir la instantánea, debe mantenerlas fuera de la respuesta HTTP y de los logs públicos.

## Explicaciones

El texto determinista de `matching` es la fuente de hechos y el **fallback obligatorio**. `personalize_recommendation(item)` lo conserva. Bajo una solicitud explícita, `personalize_recommendation(item, use_llm=True, ai=generador)` permite elegir variantes españolas ya aprobadas. El generador recibe solo categorías e identificadores anónimos de hechos, no nombres, requisitos textuales, PII, referencias, vectores o scores. La salida debe seleccionar exactamente los hechos, grupos, orden y variantes permitidos; cualquier error, vacío o hecho inventado devuelve el DTO original. La personalización no vuelve a calcular elegibilidad ni ranking. Llama 3.1:8b es opcional y se inyecta mediante `generate_structured(prompt, schema)`; la ruta normal no invoca Ollama.

## Duplicados y vigencia

`SourceVersions` admite revisiones opacas aportadas por el adaptador para perfil, evento, equipo, acceso, acciones y ambos embeddings, además de la revisión del contenido fuente que representa cada embedding. Todas son necesarias para declarar una instantánea completa. La versión de fuente del embedding no es la versión de compatibilidad del pipeline (`embedding_source_version` de `matching`). Un embedding ausente **confirmado** puede llevar una revisión de ausencia; metadatos omitidos significan vigencia desconocida.

```python
from app.services.ai.matching.policy import RankingPolicy
from app.services.ai.recommendations import (
    SourceVersions, assess_freshness, build_snapshot_fingerprint,
)

revisiones = SourceVersions(
    profile="profile-v1", event="event-v1", team="team-v1",
    access="access-v1", actions="actions-v1",
    profile_embedding="profile-vector-v1", event_embedding="event-vector-v1",
    profile_embedding_source="profile-v1", event_embedding_source="event-v1",
)
politica = RankingPolicy()
anterior = build_snapshot_fingerprint(
    para_organizador[0], persona, proyecto, organizador, revisiones,
    politica, action_records=[],
)
# Tras consultar otra vez todas las fuentes autorizadas, construir `actual`
# con los datos, contextos y revisiones recién obtenidos.
actual = build_snapshot_fingerprint(
    para_organizador[0], persona, proyecto, organizador, revisiones,
    politica, action_records=[],
)
estado = assess_freshness(anterior, actual)
assert estado.status == "current"
```

Las huellas son tokens internos SHA-256 para igualdad; no incluyen valores crudos en su representación y no deben exponerse como identificadores públicos. `current` solo compara las dos instantáneas completas dadas; no prueba que el estado siga igual después. Cambios conocidos producen `stale`; ausencia de revisiones o datos necesarios produce `unknown`, nunca `current` por defecto. No hay plazo de caducidad arbitrario. Un modelo de embedding, vector, origen, política, perfil, evento, equipo, permiso o acción distintos pueden invalidar la recomendación. `same_action_pair` permite reconocer el mismo par en ambas direcciones; `is_repeated_recommendation` exige la misma audiencia y una instantánea completa sin cambios. Una solicitud aceptada sin participante confirmado queda en `unknown`.

## Integración futura FastAPI/MySQL

Un adaptador autorizado debe:

1. Identificar al actor con la autenticación vigente y verificar propiedad del evento o consentimiento del usuario. Obtener solo eventos visibles y perfiles descubribles según permisos reales.
2. Preparar `CandidateInput`, `EventInput`, contextos, integrantes, `ActionRecord` y revisiones desde una lectura coherente de `Usuario`, `PerfilUsuario`, `Evento`, `ParticipanteEvento` y `SolicitudEquipo`. Distinguir estados pendientes, aceptados, rechazados y desconocidos. No inferir revisiones que el esquema aún no ofrezca.
3. Aplicar las recomendaciones y devolver únicamente los DTO públicos de la audiencia correcta. Mantener huellas y datos privados solo del lado del servidor. Si se presenta una recomendación guardada, comparar una instantánea fresca antes de mostrarla como vigente.
4. **Antes de invitar o solicitar ingreso, revalidar dentro de la operación de escritura** identidad y permisos actuales, consentimiento/visibilidad, evento abierto, creador, membresía, estado de invitaciones y solicitudes, cupo o roles si aplican y cualquier restricción estricta vigente. Volver a leer el estado de ambos lados y evitar la carrera entre comprobación y escritura mediante transacción y restricciones de unicidad o bloqueo apropiados. Una huella `current` no sustituye esta comprobación; `stale` o `unknown` impide usar la recomendación como autorización.

El esquema actual no garantiza todas las revisiones de fuente, versión del modelo/vector, ni una captura atómica de permisos, equipo y acciones. El adaptador deberá definirlas con el equipo de backend antes de publicar vigencia `current` en producción. Este paquete no implementa endpoints, persistencia, invitaciones, periodicidad ni política de notificaciones.
