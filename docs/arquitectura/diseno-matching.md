> Diseño de referencia histórico. Los contratos operativos actuales están en [operación](../operacion/recomendaciones-equipos.md); la validación está en [QA](../qa/seguimiento-mvp.md).

# Diseño del motor de matching — Fase 4

**Estado:** propuesta de arquitectura; no hay motor implementado. **Fecha:** 21 de octubre de 2026. **Alcance:** ordenar candidatos para cubrir vacantes de un evento o proyecto, en categorías académicas, deportivas, competencias, videojuegos y otras. El sentido inverso (proyectos para una persona), recomendaciones periódicas e invitaciones pertenecen a fases posteriores.

## 1. Evidencia del repositorio y límites actuales

- `backend/app/services/ai/schemas.py`: `StructuredProfile` contiene `habilidades`, `intereses`, `areas_mejora`, `experiencia`, `resumen_publico`. `StructuredEventRequirements` contiene `habilidades_obligatorias`, `habilidades_deseables`, `roles_buscados`, `intereses_relacionados`, `restricciones_explicitas`, categoría, título y resumen. Son textos estructurados, no hechos verificados sobre disponibilidad, ubicación o elegibilidad. **`areas_mejora` jamás acredita competencia.**
- `backend/app/services/ai/embeddings.py`: el texto de perfil usa habilidades, intereses y experiencia, y excluye áreas de mejora; el texto de evento incluye capacidades obligatorias/deseables, roles, intereses, restricciones, categoría y resumen. `generate_*_embedding` devuelve `list[float]`; con `nomic-embed-text` exige 768 elementos finitos. Un vector por sí solo no prueba que se cumpla un requisito.
- `database/db_actividad.sql`: `usuarios` tiene estado de cuenta y ubicación; `perfiles_usuarios` declara JSON de datos, perfil IA y embedding; `eventos` declara requisitos IA, embedding y estado; `participantes_evento` contiene integrantes y roles; `solicitudes_equipo` contiene invitaciones/solicitudes. No hay campos explícitos para versión de embedding, visibilidad, disponibilidad verificable ni estado de procesamiento.
- Backend incorporado de Isaac: `models/usuario.py` no declara `perfil_estructurado_ia`, `embedding_perfil` ni `resumen_publico_ia`, aunque sí están en el SQL. `models/evento.py` declara `requisitos_ia` y `embedding_requisitos` como JSON; las rutas `api/routes/perfiles.py` y `eventos.py` no invocan la IA. No hay ORM para `participantes_evento`/`solicitudes_equipo` ni endpoints de matching. `schemas/evento.py` expone `embedding_requisitos` como diccionario, incompatible con el vector `list[float]` generado actualmente. `main.py` ejecuta `create_all`, que no migra columnas existentes.
- Análisis de integración del 21 de octubre, consultable en el [archivo histórico](../archivo/README.md): en ese momento la UI usaba `api.js` y aún simulaba interpretación/recomendaciones. El frontend enviaba `requisitos_ia: {roles}` con otro contrato; no debía tomarse como salida validada del parser. La identidad basada en `localStorage` tampoco acreditaba autorización. Esta descripción es anterior al JWT y la integración actuales.

La auditoría del plan maestro y estas observaciones definen dependencias, no permiso para editar rutas, ORM, SQL o frontend durante esta fase de diseño. El estado de calidad de los parsers debe medirse en casos reales antes de usar resultados no revisados para descartar personas.

## 2. Principios y fronteras de responsabilidad

1. **Entrada confiable y procedencia.** Un adaptador backend obtiene registros autorizados y distingue datos declarados por usuario, requisitos confirmados por organizador y extracción IA pendiente de revisión. Cada hecho usado para filtrar o explicar debe conservar `origen`, texto/valor original y estado de confirmación. El motor no consulta directamente MySQL ni Ollama durante el ranking.
2. **Separar elegibilidad de preferencia.** Una condición realmente obligatoria y confirmada puede impedir la candidatura solo ante contradicción comprobada. Preferencias y similitud ordenan, nunca excluyen. Un dato ausente produce `desconocido` o `requiere_verificacion`, no `no cumple`.
3. **Complementar huecos reales del equipo.** Se evalúan vacantes y capacidades aún no cubiertas por participantes. Si falta la lista de participantes o sus roles, no se inventan huecos: se usan únicamente `roles_buscados` confirmados, con la limitación indicada.
4. **Explicabilidad.** Cada señal de ranking debe vincularse a evidencias de entrada. No presentar un número como “porcentaje de compatibilidad” ni afirmar disponibilidad, experiencia o habilidad que no conste.
5. **Neutralidad de categoría.** El algoritmo base es el mismo para programación, deportes, competencias u otras actividades. Un vocabulario de equivalencias por dominio puede ayudar a normalizar términos, pero debe estar versionado y revisado; no asumir que “portero” equivale a otra función ni que interés en una disciplina implica práctica.

## 3. Contratos propuestos (internos, sin endpoints todavía)

Los siguientes tipos representan una frontera de dominio. El adaptador posterior decidirá cómo obtenerlos y persistirlos. Campos opcionales son `None` cuando se desconoce el dato; una lista vacía significa que la fuente confirmó que no hay elementos, no simplemente que aún no se cargaron.

```python
Evidence = {
    "source": "user_declared|organizer_confirmed|ai_unreviewed|team_record",
    "value": str,
    "confirmed": bool,
    "source_ref": str | None,  # referencia interna, no PII ni prompt completo en la respuesta
}

CandidateInput = {
    "user_id": int,
    "profile": StructuredProfile | None,
    "declared_skills": list[Evidence] | None,
    "role_preferences": list[Evidence] | None,
    "availability": list[Evidence] | None,
    "location": dict | None,
    "visibility": "visible|hidden|unknown",
    "account_state": "active|inactive|unknown",
    "profile_embedding": list[float] | None,
    "embedding_model": str | None,
    "embedding_source_version": str | None,
}

EventInput = {
    "event_id": int,
    "creator_id": int,
    "state": "open|closed|unknown",
    "requirements": StructuredEventRequirements | None,
    "confirmed_requirements": list[Evidence] | None,
    "participants": list[dict] | None,  # {user_id, role, confirmed}
    "outstanding_roles": list[Evidence] | None,
    "explicit_constraints": list[Evidence] | None,
    "event_embedding": list[float] | None,
    "embedding_model": str | None,
    "embedding_source_version": str | None,
}

MatchRequest = {
    "event": EventInput,
    "candidates": list[CandidateInput],
    "policy_version": str,
    "top_n": int | None,
}
```

`StructuredProfile.habilidades` es evidencia de habilidad **declarada**. `experiencia` puede respaldar una habilidad solo si contiene una capacidad explícita y una regla de normalización revisada; no se convierte automáticamente en nivel de dominio. `intereses` puede alimentar afinidad temática. `areas_mejora` se conserva para explicación de oportunidades de aprendizaje, pero se excluye de cobertura obligatoria, deseable, complementariedad de fortalezas y texto del embedding de perfil. Si una persona dice que quiere aprender Python y no declara saberlo, Python figura como `sin_evidencia_de_habilidad`.

```python
RequirementAssessment = {
    "requirement": str,
    "kind": "required_skill|preferred_skill|open_role|explicit_constraint",
    "status": "met|unmet_confirmed|unknown|not_applicable",
    "evidence": list[Evidence],
    "reason": str,
}

MatchResult = {
    "event_id": int,
    "candidate_id": int,
    "eligibility": "eligible|needs_review|ineligible",
    "eligibility_reasons": list[str],
    "requirements": list[RequirementAssessment],
    "ranking_score": float | None,  # índice interno [0,1], no porcentaje de compatibilidad
    "score_components": dict[str, float | None],
    "evidence_coverage": dict[str, int],  # conocidas, desconocidas y no aplicables
    "explanation": {"strengths": list[str], "gaps": list[str], "unknowns": list[str]},
    "policy_version": str,
}
```

`unmet_confirmed` exige evidencia positiva de incompatibilidad: por ejemplo, la persona declara que no puede acudir el domingo y el organizador confirma asistencia dominical obligatoria. La simple ausencia de “domingo” o “Laravel” en el perfil es `unknown`. `needs_review` indica que la información necesaria falta o procede solo de IA no confirmada. Si no hay señales puntuables, `ranking_score=None` y el candidato queda visible en un grupo “información insuficiente”, sin inventar un cero.

## 4. Política de elegibilidad

| Tipo | Tratamiento propuesto | Ejemplo |
| --- | --- | --- |
| Seguridad/estado confirmado | Exclusión estricta antes de puntuar, con motivo auditable. | Cuenta inactiva, perfil oculto, evento cerrado, creador o participante ya incorporado. La política de visibilidad debe definir quién puede ver la recomendación. |
| Condición explícita confirmada | Exclusión solo si hay contradicción confirmada; si falta información, `needs_review`. | Asistencia presencial obligatoria los domingos frente a indisponibilidad declarada los domingos. |
| Habilidad obligatoria | `met` con habilidad declarada/equivalencia aprobada; `unmet_confirmed` solo ante carencia explícita y actual; si no aparece, `unknown`. La política de producto debe decidir si `unmet_confirmed` impide enviar solicitud o solo solicita revisión humana. | “Python obligatorio”; “quiero aprender Python” no cumple. |
| Habilidad deseable | Aumenta ranking si existe evidencia; ausencia o desconocimiento no excluye. | Git deseable. |
| Rol vacante | Señal de complementariedad cuando la vacante está confirmada y el candidato aporta capacidad relevante; preferencia de rol declarada puede ayudar, sin sustituir habilidad. | Portero solicitado; no recomendar otro portero si el puesto ya quedó cubierto. |
| Modalidad/ubicación/horario | Filtrar solo si ambos lados tienen datos comparables y la condición es realmente obligatoria; de otro modo, desconocido. | No inferir que una ciudad en el perfil implica disposición a viajar. |

`visibility=unknown` requiere decisión de privacidad antes de mostrar un perfil a terceros. Puede mantenerse en el cálculo interno como `needs_review`, pero no exponerse en una respuesta pública hasta confirmar el permiso. No usar `rol_sistema="Estudiante"` ni `carrera` como filtros generales: el producto abarca personas fuera de la universidad. En competencias con requisitos reglamentarios, una regla específica solo se aplica si está declarada, confirmada y dispone de datos verificables.

## 5. Comparación y ranking explicable

### 5.1 Normalización de términos

Normalizar espacios, mayúsculas, acentos y formas explícitamente equivalentes sin cambiar el significado. Las equivalencias (`UE5` ↔ `Unreal Engine 5`, por ejemplo) deben quedar en un catálogo revisado y versionado por dominio. No convertir “me interesa fútbol” en “juega fútbol”, “básico” en dominio avanzado ni “proyecto de IA” en restricción. Mantener el texto original para explicaciones y auditoría. Un requisito ambiguo o producido solo por IA queda pendiente de confirmación.

### 5.2 Cobertura de requisitos y complementariedad

- Para cada habilidad obligatoria y deseable: registrar `met`, `unmet_confirmed` o `unknown`, con evidencia. La cobertura obligatoria es la fracción de requisitos confirmados que el candidato acredita; reportar también el número desconocido para no convertir omisiones en fallos.
- Obtener capacidades existentes del equipo únicamente de participantes confirmados y de perfiles visibles para el proceso. Una fortaleza complementa si cubre un requisito o rol confirmado aún no cubierto; repetir una capacidad abundante no recibe la misma bonificación. Si falta composición del equipo, el componente de complementariedad queda `None` y se indica “equipo no disponible”.
- Para deportes, un puesto explícito y disponibilidad para entrenar pueden ser más relevantes que un texto similar; para competencias, herramientas/roles y condiciones de participación; para proyectos académicos, habilidades y tareas. Las reglas por categoría cambian **evidencias disponibles y pesos configurados**, no fabrican datos.

### 5.3 Similitud coseno

Usar el producto punto de vectores normalizados: `cos(a,b) = dot(a,b) / (||a||·||b||)`. Validar longitudes iguales, todos los valores finitos, norma mayor que cero, versión/modelo compatibles y estado no obsoleto. Si falla cualquier condición, `semantic_similarity=None`; nunca usar cero como sustituto ni mezclar modelos aunque compartan 768 dimensiones. Para ranking se puede mapear una similitud válida a `[0,1]` mediante una transformación fija documentada, sin interpretarla como probabilidad o porcentaje de éxito. Nomic aporta proximidad temática y debe pesar menos que cobertura explícita y restricciones confirmadas.

### 5.4 Pesos iniciales configurables

Propuesta para **experimento**, no calibración de producto:

| Componente | Peso inicial | Fuente |
| --- | ---: | --- |
| Cobertura de habilidades obligatorias acreditadas | 0.40 | Requisitos confirmados y habilidades declaradas. |
| Complementariedad de vacantes/capacidades faltantes | 0.25 | Roles buscados y participantes confirmados. |
| Habilidades deseables | 0.15 | Preferencias confirmadas y habilidades declaradas. |
| Similitud semántica | 0.10 | Vectores compatibles de Nomic. |
| Interés o preferencia explícita por el tema/rol | 0.10 | Intereses y preferencias declarados. |

Los pesos suman 1.0 y viven en una configuración versionada, no en constantes dispersas. Ajustar por categoría solo después de evaluar ejemplos reales. Una señal sin datos queda `None`; recalcular el promedio ponderado sobre componentes disponibles y **mostrar `evidence_coverage` y componentes ausentes**. No dar bonificación por desconocimiento. Para evitar que una puntuación con una sola señal parezca tan sólida como otra con cinco, ordenar primero por nivel de elegibilidad (`eligible`, luego `needs_review`) y dentro de cada nivel por cobertura de evidencia mínima configurable y puntuación; ofrecer un grupo separado de candidatos con datos insuficientes. No ocultarlos ni asignarles incompatibilidad ficticia. Desempates deterministas: más requisitos confirmados cubiertos, mayor complementariedad comprobada y, por último, `user_id` estable; nunca datos sensibles.

El ranking debe devolver frases basadas en hechos: “declara Python; cubre 1 de 2 requisitos obligatorios; disponibilidad dominical por confirmar”. No afirmar “90 % compatible”. `gaps` distingue requisitos sin evidencia de contradicciones confirmadas. No mostrar detalles privados de otros participantes para explicar complementariedad.

## 6. Subfases de implementación propuestas

Nombres y firmas **propuestos**, no existentes. Mantener los parsers y generadores públicos actuales sin cambios de firma. La capa de matching trabaja con objetos ya adaptados y probados; la integración HTTP/BD será otra tarea.

| Subfase | Archivos propuestos | API y responsabilidad | Pruebas mínimas |
| --- | --- | --- | --- |
| **4.1 Contratos y normalización** | `backend/app/services/ai/matching/schemas.py`, `normalization.py`, `tests/test_matching_contracts.py` | `MatchRequest`, `MatchResult`, `RequirementAssessment`; `normalize_term`, `validate_evidence`. Diferenciar ausente, vacío y no confirmado; catálogo de equivalencias versionado. | JSON inválido, duplicados, acentos, UE5, categorías académica/deportiva/competencia/otra; área de mejora nunca acredita habilidad. |
| **4.2 Elegibilidad y cobertura** | `matching/eligibility.py`, `matching/requirements.py`, `tests/test_matching_eligibility.py` | `assess_eligibility(event, candidate, policy)`, `assess_requirements(...)`. Aplicar exclusiones confirmadas y estados trivalentes por requisito. | Cuenta inactiva, perfil oculto, creador/participante, evento cerrado; Python obligatorio acreditado/negado/desconocido; Docker deseable; domingo disponible/indisponible/desconocido. |
| **4.3 Similitud y complementariedad** | `matching/similarity.py`, `matching/complementarity.py`, `tests/test_matching_signals.py` | `cosine_similarity(a,b,model_metadata) -> float|None`; `assess_team_gaps(event, participants)`, `complementarity_score(...)`. No llamar Ollama aquí. | Vector idéntico/ortogonal, cero/NaN/infinito, dimensión/modelo/versión incompatibles; portero ya cubierto; equipo desconocido; interés sin habilidad. |
| **4.4 Puntuación y explicación** | `matching/policy.py`, `matching/ranking.py`, `matching/explanations.py`, `tests/test_matching_ranking.py` | `score_candidate(assessments, policy)`, `rank_candidates(request, policy)`, `explain_match(result)`. Pesos validados y reponderación de componentes disponibles. | Orden estable, pesos inválidos, preferencia nunca elimina, contradicción prevalece sobre coseno alto, datos incompletos en grupo visible, explicación sin hechos inventados ni porcentaje. |
| **4.5 Evaluación y preparación de integración** | `tests/test_matching_scenarios.py`, `backend/app/services/ai/matching/README.md`; adaptador futuro bajo acuerdo con backend | `evaluate_scenarios(fixtures, policy)` para revisar ejemplos sintéticos y resultados esperados; definir contrato del adaptador, sin modificar aún rutas/ORM. | Casos académicos, deportivos, game jam y otros; candidatos hábiles pero indisponibles; roles ocupados; embeddings faltantes; cambio de modelo; privacidad; regresión de parsers IA-01 a IA-05. |

`ranking.py` debe ser puro y determinista para que las pruebas no dependan de MySQL u Ollama. El adaptador futuro realizará consultas por lotes para evitar N+1, verificará autorización y versiones de datos, y pasará entradas ya filtradas por visibilidad. Los pesos, umbrales mínimos de evidencia y equivalencias deberán tener `policy_version` para reproducir un orden histórico.

## 7. Decisiones pendientes y dependencias del equipo

1. **Backend/BD:** alinear ORM con SQL de perfil, representar vector como lista más metadatos de modelo y actualización, y modelar participantes y solicitudes. Definir migraciones reales; `create_all` no basta. Decidir si se persiste un vector completo en JSON o se usa otra infraestructura cuando aumente el volumen.
2. **Producto y organizadores:** confirmar qué requisitos son excluyentes, qué roles están abiertos, si un candidato puede cubrir varios roles y si se admite revisión humana cuando falta evidencia. No convertir cada palabra de `restricciones_explicitas` en filtro estricto automáticamente.
3. **Autenticación y privacidad:** identidad servidor, visibilidad de perfil y permiso para recomendar; el ID de `localStorage` no sirve como control de acceso. Definir si candidatos ocultos se omiten completamente o se consideran solo para métricas internas anónimas.
4. **Frontend:** diseñar estados `eligible`, `needs_review` e `ineligible`, motivos verificables, campos faltantes y controles para corregir datos. Su modelo actual de `{roles}` no coincide con `StructuredEventRequirements`.
5. **Calidad IA:** confirmar con casos reales que habilidades obligatorias/deseables y roles extraídos son fieles. Las correcciones puntuales IA-01 a IA-05 no prueban una extracción universal. Los requisitos no confirmados por organizador no deberían excluir candidatos.
6. **Evaluación:** acordar un conjunto de pares evento-candidato revisado por humanos, métricas de cobertura de requisitos, errores de exclusión, utilidad del orden y distribución por categoría. Ajustar pesos con esos datos; los valores 0.40/0.25/0.15/0.10/0.10 son punto de partida.

## 8. Criterio para iniciar código de Fase 4

Se puede desarrollar el núcleo puro de 4.1–4.4 con fixtures sintéticos y contratos provisionales. Para integrar recomendaciones reales se necesitan, al menos: esquema ORM/SQL consistente, requisitos confirmados, fuente de participantes/roles, política de visibilidad y autorización, metadatos de embeddings, y acuerdo de cómo manejar datos incompletos. Hasta entonces, cualquier salida será una evaluación técnica local, no una recomendación de producto.
