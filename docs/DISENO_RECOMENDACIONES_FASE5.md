# Diseño de recomendaciones — Fase 5.0

**Fecha:** 22 de octubre de 2026. **Estado:** diseño, sin implementación. **Rama examinada:** `feat/ai-matching` en `f883c4f`; `origin/isaac` en `d90b7e5` tras `git fetch origin`. El árbol local contiene trabajo de 4.5 sin confirmar, por lo que **no se integró** `origin/isaac`. Las observaciones sobre esa rama describen su commit remoto, no código disponible aún en esta rama.

## 1. Base verificada y objetivo

El núcleo de Fase 4 ya ofrece `CandidateInput`, `EventInput`, `Evidence`, `MatchRequest`, `MatchResult`, `RankingPolicy`, `assess_eligibility`, `assess_requirements`, `assess_team_gaps`, `cosine_similarity`, `rank_candidates` y explicaciones deterministas. Evalúa **un evento frente a varios candidatos** sin consultar base de datos ni Ollama. Los resultados distinguen `eligible`, `needs_review`, requisitos `met`/`unmet_confirmed`/`unknown`, señales `None` y cobertura de evidencia. `ranking_score` es un índice interno, no una probabilidad. El ajuste local de 4.5 exige evidencia de todas las partes de una restricción afirmada, como «domingos en Monterrey»; todavía no está confirmado en Git.

Fase 5.0 debe diseñar dos superficies:

1. **Para organizadores:** personas que pueden cubrir una vacante de un evento propio y son visibles para ese organizador.
2. **Para usuarios:** eventos abiertos donde pueden participar, con explicación y datos faltantes. El sentido inverso requiere una capa de selección y orden **entre eventos**; `rank_candidates` por sí solo no lo resuelve.

El resultado de esta fase de diseño no crea rutas, tablas, jobs, recomendaciones persistidas ni invitaciones. El frontend actual todavía devuelve arreglos simulados en `obtenerRecomendaciones()` y `obtenerCandidatos()`; la pantalla `/match` usa `mockData`. El commit nuevo de Isaac añade un directorio `/estudiantes`, perfiles públicos e invitaciones ligadas a rutas, pero no conecta el motor de matching.

### Interfaces y dependencias concretas

| Pieza | Situación observada | Consecuencia para 5.0 |
| --- | --- | --- |
| `PerfilUsuario` / `Evento` actuales | JSON genéricos; el ORM de perfil carece de vector/metadatos. `EventoOut.embedding_requisitos` está tipado como diccionario, mientras los generadores producen listas. | Adaptadores explícitos y validación antes de construir contratos del motor; no interpretar JSON arbitrario como evidencia confirmada. |
| `origin/isaac`: perfiles públicos | `datos_crudos.visibilidad` controla campos; `pausado` excluye del listado. Hay valores de visibilidad por defecto y no aparece un consentimiento global verificable para recomendaciones. | Decidir permiso de exposición por audiencia. `pausado`, cuenta inactiva o visibilidad incierta no pueden convertirse en candidato público. |
| `origin/isaac`: `ParticipanteEvento` y `SolicitudEquipo` | Hay ORM y rutas nuevas, con estados textuales. El SQL tiene `UNIQUE(id_evento,id_usuario)` para participantes, pero el modelo ORM mostrado no declara esa unicidad. | Confirmar esquema efectivo, roles, estados y duplicados. Un participante aceptado se excluye antes de recomendar. |
| `origin/isaac`: invitaciones | El POST recibe `de_id` por query y el PATCH acepta un estado sin comprobar identidad del destinatario en la ruta inspeccionada. `rol_esperado` no se guarda en `ParticipanteEvento`. | La integración requiere identidad/autorización del servidor y transición atómica; una sugerencia nunca autoriza por sí misma a invitar o aceptar. |
| Frontend actual y remoto | La identidad se lee de `localStorage`; el nuevo directorio busca perfiles y puede invitar. Las funciones de recomendaciones y solicitudes para unirse siguen simuladas. El mapeo remoto de habilidades asigna nivel «intermedio» por defecto. | El frontend debe consumir un DTO público nuevo y estados reales; no usar ID local ni nivel inferido como prueba de habilidad. |

## 2. Reglas de producto y privacidad

**Elegibilidad precede al orden.** No mostrar perfiles ocultos, pausados, de cuentas inactivas, creadores del mismo evento ni integrantes confirmados. Un requisito obligatorio sin dato del candidato produce revisión, no rechazo. Una contradicción confirmada solo excluye si la política versionada la declara estricta. Las habilidades deseables, intereses y coseno nunca excluyen. Áreas de mejora y preferencias no acreditan capacidad.

**Audiencias separadas.** El organizador solo consulta recomendaciones de un evento que puede administrar; ve únicamente campos públicos autorizados del candidato. El usuario consulta eventos que puede ver y sus propias razones; no recibe datos privados de integrantes ni de otros aspirantes. El caso de perfil pausado/oculto para recomendaciones privadas al propio usuario requiere decisión de producto y un contrato de autorización separado: no se debe alterar artificialmente `visibility` para reutilizar `rank_candidates`.

**Explicación verificable.** Mostrar hechos como «declara Blender y cubre la vacante confirmada de artista 3D» solo con evidencia positiva confirmada. Mostrar «Python por verificar» si solo hay extracción IA o no hay dato. Una negación confirmada debe distinguirse de una omisión. No mostrar nombres de integrantes, correo, teléfono, prompts, `source_ref`, porcentajes de compatibilidad ni el índice interno como promesa. La proyección pública debe revisar también texto libre de requisitos antes de enviarlo: el saneamiento actual de `MatchResult` cubre patrones obvios de correo/teléfono, no toda información sensible.

**Estado actual en el momento de actuar.** Una recomendación es una fotografía, no un derecho a invitar o solicitar ingreso. Antes de cada acción, volver a comprobar propiedad del evento, cuenta, visibilidad, estado del evento, cupo/rol, pertenencia e invitación o solicitud existente. La consulta y la escritura deben ser atómicas o protegidas por restricciones únicas; la UI debe poder mostrar «ya no disponible».

## 3. Contratos propuestos, internos y públicos

Estos son contratos de diseño para una fase posterior; no existen todavía en código.

| Contrato | Campos mínimos | Regla |
| --- | --- | --- |
| `RecommendationQuery` | `audience: organizer\|user`, `event_id` para organizador o sujeto del usuario autenticado, `top_n`, `policy_version` | `actor_id` procede de autenticación servidor, nunca de un parámetro confiado al cliente. Máximo y paginación deben fijarse en backend. |
| `RecommendationSnapshot` | `event: EventInput`, candidatos `CandidateInput`, `team_members`, estados de invitación/solicitud, `source_revisions`, `as_of` | `None` y lista vacía tienen significados diferentes; cada hecho conserva procedencia, confirmación y polaridad. |
| `RecommendationItemPublic` | identificador opaco de resultado, `event_id` o `candidate_id` visible, `eligibility_group`, razones públicas, `evidence_coverage`, `explanation`, `action_state`, `freshness` | No exponer `CandidateInput`, vector, evidencia interna ni `ranking_score` bruto. Resolver nombre/foto públicos aparte y bajo autorización. |
| `RecommendationPage` | `items`, `audience`, `policy_version`, `equivalence_version`, `generated_at`, `snapshot_revision`, `next_cursor` | Cursor estable ligado a filtros/versión; no duplicar el mismo par al paginar. |
| `ActionCheck` | `allowed`, `reason_code`, `current_revision` | Se recalcula en servidor justo antes de invitar o solicitar, independientemente del resultado mostrado. |

`eligibility_group` debe distinguir `eligible`, `needs_review` y `insufficient_evidence` de forma visible. `ineligible` no sale en recomendaciones públicas. `action_state` contempla al menos `available`, `pending_invitation`, `pending_application`, `already_member`, `closed` y `stale`; no debe construirse a partir de mocks. Una recomendación del mismo par evento-persona se identifica por `(event_id, candidate_id, audience, policy_version, snapshot_revision)` para trazabilidad, mientras la deduplicación de **acciones** usa el par evento-persona y su estado real, sin permitir duplicados por cambiar el rol mostrado.

La compatibilidad semántica necesita **dos versiones distintas**: una versión común del modelo/pipeline de embedding y la revisión del texto fuente de cada perfil/evento. El `embedding_source_version` actual se compara por igualdad entre los dos vectores; si representa revisiones individuales, esa igualdad sería inadecuada. El adaptador futuro debe definir y validar ambas dimensiones antes de activar coseno. Hasta entonces, vectores ausentes, incompatibles u obsoletos producen señal `None`.

## 4. Flujo para organizadores

1. Autenticar al actor y verificar que administra el evento solicitado; comprobar evento abierto y requisitos revisados por organizador.
2. Obtener en lote candidatos potenciales, visibilidad/consentimiento, cuentas, perfiles y embeddings; obtener equipo confirmado y estados de acciones. Nunca usar `localStorage` como autoridad.
3. Construir `EventInput`, `CandidateInput` y `team_members` validados. Aplicar exclusiones de privacidad y acciones existentes. Las extracciones IA no confirmadas permanecen `ai_unreviewed`.
4. Ejecutar `rank_candidates` con política/catálogo versionados. Conservar `eligible` y `needs_review` en grupos identificables; poner casos sin evidencia suficiente en un grupo propio. Aplicar `top_n` **después** de exclusiones y deduplicación, con desempate estable.
5. Proyectar `MatchResult` a `RecommendationItemPublic` y resolver solo campos públicos autorizados. Mostrar por qué cubre una vacante o qué falta confirmar; no inventar niveles de dominio.
6. En la invitación, ejecutar `ActionCheck` con estado actual y escribir idempotentemente. Si el equipo, visibilidad, rol o estado cambió, pedir recálculo antes de enviar.

El rol «buscado» debe distinguirse de un cupo real. `outstanding_roles` hoy es una lista de términos, sin cantidad; no se puede decidir si dos personas con el mismo rol son necesarias ni atribuir capacidad a un participante solo por su etiqueta de rol.

## 5. Flujo para usuarios

1. Autenticar al usuario; definir si su perfil puede evaluarse para descubrimiento privado según consentimiento. No revelar al organizador el interés del usuario por un evento hasta que el usuario actúe.
2. Obtener eventos visibles y abiertos, excluyendo eventos propios, membresías y acciones pendientes según política. Construir un `EventInput` por evento con requisitos confirmados; preservar desconocidos.
3. Evaluar elegibilidad/requisitos de la persona por evento y producir explicación específica. La función actual `rank_candidates` puede ayudar a evaluar **cada** par evento-persona, pero no se deben concatenar sus `ranking_score`: al reponderar señales disponibles, dos eventos con cobertura distinta no son directamente comparables.
4. Diseñar un comparador transversal explícito y versionado: primero elegibilidad, después suficiencia y cobertura de evidencia comparable, luego utilidad de vacante/preferencia confirmada y señal semántica secundaria. Hasta calibrarlo con ejemplos humanos, ofrecer grupos o filtros por categoría y orden estable por hechos conocidos; no presentar una lista global como «mejores oportunidades» basada solo en coseno.
5. Antes de solicitar ingreso, revalidar estado, visibilidad del evento, requisitos estrictos y duplicados. La solicitud de ingreso necesita dirección y autorización distintas de la invitación del organizador.

## 6. Obsolescencia, duplicados y consistencia

Un snapshot debe registrar versiones o hashes de perfil, requisitos confirmados, vacantes/participantes, visibilidad, estado del evento, solicitudes/invitaciones, catálogo de equivalencias y política, además de modelo/pipeline de embedding. Cualquier cambio relevante invalida la explicación o marca el resultado `stale`. `generated_at` y un TTL configurable pueden limitar exposición, pero **no reemplazan** la revalidación transaccional antes de actuar. No fijar un TTL arbitrario hasta medir latencia y frecuencia de cambios.

Para acciones, el backend debe normalizar estados (`Pendiente`, `Aceptada`, `Rechazada`), comprobar transiciones permitidas, idempotencia y unicidad efectiva en base de datos. Debe distinguir invitación del organizador de solicitud del usuario. El nuevo endpoint de `origin/isaac` comprueba una invitación pendiente del mismo remitente/destinatario, pero no basta para evitar carreras, solicitudes inversas, reintentos simultáneos o alta duplicada de participantes. La tabla SQL sí declara unicidad `(id_evento,id_usuario)` para participantes; verificar que la base desplegada y el ORM convergen.

## 7. Plan de implementación y pruebas 5.1–5.5

| Subfase | Entregable propuesto | Pruebas de aceptación |
| --- | --- | --- |
| **5.1 Contratos y adaptadores de lectura** | `recommendations/contracts.py`, adaptadores de snapshot en backend tras acordar ORM/SQL; autorización y procedencia explícitas. | Mapeo de estados, IDs, `None` vs `[]`, requisitos IA sin confirmar, vector/versión incompatible, actor ajeno rechazado, visibilidad/pausa respetadas; consultas por lote sin N+1. |
| **5.2 Organizador → candidatos** | Orquestador puro que usa Fase 4, deduplica acciones y proyecta DTO público. | Académico, deportivo, game jam y general; vacante real/ocupada, obligatorias/deseables, alto coseno con contradicción, participante/creador excluido, perfil oculto, orden/top N estable, invitación pendiente no repetida. |
| **5.3 Usuario → eventos** | Evaluación por par y comparador transversal versionado; contrato de consentimiento para evaluación privada. | Evento propio/cerrado/ya unido omitido; desconocidos visibles para revisión; categorías con coberturas diferentes no ordenadas por números incomparables; resultados reproducibles y sin revelar actividad privada del usuario. |
| **5.4 Explicaciones y acciones seguras** | Proyección pública de evidencias, `ActionCheck` y estados de invitación/solicitud; rutas solo tras autenticación y autorización. | Sin habilidades de `areas_mejora`, sin datos de otros integrantes ni PII, `unknown` distinto de negación; cambios de visibilidad/rol/estado invalidan acción; concurrencia e idempotencia; acceso cruzado denegado. |
| **5.5 Evaluación e integración gradual** | Fixtures revisados por humanos, métricas, observabilidad y, después de acuerdos, consumo frontend. | Precisión de exclusiones y requisitos, omisiones/alucinaciones, cobertura de evidencia, estabilidad, latencia, degradación sin embedding, perfiles pausados, duplicados, pruebas de contrato backend/frontend y regresión de 4.1–4.5 + parsers IA-01–IA-05. |

El primer hito de integración debe funcionar sin Ollama en la ruta de consulta, usando datos y vectores ya disponibles. La generación y actualización de embeddings pertenecen a otro flujo. En cada subfase, medir cambios por categoría y revisar errores con ejemplos humanos antes de ajustar pesos o habilitar acciones.

## 8. Decisiones pendientes y bloqueos

- **Git:** el árbol local conserva `matching/requirements.py`, `matching/README.md`, `test_matching_scenarios.py` y dos documentos sin seguimiento. Se necesita preservar y decidir cómo registrar ese trabajo antes de un merge. La simulación de merge de los commits rastreados no mostró archivos superpuestos ni marcadores textuales, pero eso no valida el árbol local ni la integración funcional.
- **Backend/BD:** confirmar esquema desplegado, migraciones, metadatos de embeddings, revisión de requisitos, participantes/roles/cupos, estados de solicitud y unicidad. `create_all` no migra columnas existentes.
- **Seguridad y privacidad:** autenticación de servidor, propiedad del evento, consentimiento de recomendación, pausa/visibilidad global y por campo, permiso para ver datos personales, auditoría de consultas y acciones. El ID en `localStorage` o `de_id` no constituye autorización.
- **Producto:** decidir política de requisitos estrictos, solicitud inversa, manejo de rechazo y eventual período de espera, varios cupos por rol y tratamiento de perfil oculto en descubrimiento privado.
- **Evaluación:** acordar un conjunto de pares evento-persona etiquetado por revisores de distintas categorías. Los escenarios sintéticos que hoy pasan pytest verifican reglas, no utilidad real ni equidad del orden.
