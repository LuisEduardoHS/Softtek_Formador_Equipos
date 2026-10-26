# Candidatos vacíos con análisis listo: consentimiento y claridad de la UI

## Diagnóstico del caso reportado

Se inspeccionó en modo lectura el proyecto 2 mostrado por el usuario: «MANUAL01 Gestor de tareas», creador Alex, abierto, requisitos confirmados/listos, capacidad tres, cero integrantes, cero solicitudes pendientes y dos vacantes utilizables. SQL/Figma obligatorios y Git deseable estaban disponibles en los requisitos globales. Las habilidades vacías en los roles no explicaban por sí solas la ausencia de candidatos.

Las cuentas ficticias Beatriz SQL QA y Carla Diseño QA tenían perfil confirmado y estado listo, pero **consentimiento_recomendaciones=false**. El adaptador las marcaba ocultas y tanto el motor como el endpoint del creador devolvían HTTP 200 con lista vacía. Activar el consentimiento de Alex no publica perfiles de otras cuentas.

No se cambiaron automáticamente permisos de las cuentas de la base principal. La solución para esas cuentas requiere una acción de su propio titular.

## Cómo resolverlo en la web habitual

1. Recargar la web para tomar el frontend actualizado.
2. Iniciar sesión como **Beatriz**, entrar en **Perfil** y pulsar **Activar y guardar recomendaciones**, visible arriba del análisis.
3. Repetir desde la cuenta de **Carla**. Si hay cambios pendientes, guardarlos o descartarlos antes de usar el atajo.
4. Como **Alex**, abrir el proyecto y pulsar **Actualizar candidatos** o recargar.

El control anterior sigue disponible en **Perfil → Editar → Privacidad → Activar recomendaciones → Guardar cambios**. Los perfiles deben permanecer sin pausa y con las fortalezas relevantes permitidas. «Análisis listo» describe la confirmación/vector; no equivale a consentimiento activado ni garantiza un candidato para cualquier vacante.

## Corrección de interfaz

- Aviso persistente en Inicio/Mi perfil si el consentimiento guardado está desactivado, aunque la IA esté lista. La pausa se distingue del consentimiento.
- Acción explícita «Activar y guardar recomendaciones» para la propia cuenta. Reutiliza `PUT /perfil/{id}` y envía **solo** `datos_crudos.consentimiento_recomendaciones=true`: no cambia fortalezas, biografía, pausa ni embeddings y no vuelve a ejecutar Llama/Nomic.
- Con cambios sin guardar, el atajo se deshabilita para no descartarlos ni confirmar hechos semánticos silenciosamente.
- Al terminar onboarding con el interruptor apagado, se pide elegir entre «Guardar sin recomendaciones» y «Activar recomendaciones y guardar perfil». Abrir el diálogo no confirma ni activa nada. Guardar sin consentimiento conserva false y muestra claramente ese estado en la pantalla final.
- El listado vacío explica la ruta exacta en **cada cuenta**, y Coincidencias ofrece enlace a Mi perfil. No revela cantidades ni identidades de perfiles excluidos.

No se modificaron reglas de privacidad, valores por defecto del backend, ranking, prompts, contratos de equipo, esquema ni infraestructura.

## Reproducción real y resultados

Base nueva **softtek_formador_equipos_qa_consent_20261026_cc5be6**, vacía salvo DDL/revisión, sin copiar personas de la principal. FastAPI 8011 y React 5174 separados; MySQL 8 real, llama3.1:8b y Nomic reales. Las tres primeras cuentas fueron fixtures confirmados por HTTP con consentimiento false; las dos siguientes completaron registro, análisis y revisión desde React.

| Caso ejecutado | Resultado |
| --- | --- |
| Proyecto con vacantes y perfiles listos sin consentimiento | HTTP 200, cero candidatos; UI vacía correctamente explicada |
| Activar solo la cuenta SQL desde Mi perfil | Aparece un candidato SQL/Git; Figma queda desconocido |
| Activar después la cuenta de diseño desde su sesión | Aparecen dos candidatos; Figma acreditado al segundo, sin atribuirle SQL |
| Creador mantiene consentimiento false | Puede consultar candidatos autorizados; no necesita activarlo para hacer visibles a otras personas |
| Nombre modificado sin guardar | Atajo deshabilitado; descartar restaura datos; sin guardado implícito |
| Confirmación, fecha/revisión y vector de los fixtures | Iguales antes/después de activar; no se regeneró Nomic |
| Nuevo perfil: abrir diálogo sin elegir | Sigue pendiente_revision, sin confirmación ni opt-in automático |
| Nuevo perfil: Guardar sin recomendaciones | Confirmado/listo, consentimiento false, fuera del directorio y candidatos |
| Otro nuevo perfil: Activar recomendaciones y guardar perfil | Consentimiento true, listo y proyecto real sugerido; aparece como tercer candidato |
| Cambiar consentimiento de otra cuenta | HTTP 403 |
| Activar consentimiento en perfil pausado | Conserva pausa y exclusión; despausar explícitamente recupera resultados |

**29 comprobaciones HTTP/MySQL aprobadas**, no 29 escenarios independientes. QA final: cinco usuarios/perfiles, un proyecto, ninguna invitación o membresía nueva. Este encargo verifica descubrimiento/consentimiento; los recorridos de formación de equipo están en la [validación anterior](2026-10-26-flujo-web.md).

**Dos análisis Llama reales**, exitosos, de **1.380 y 1.498 s**. Los textos separaban SQL/Git de Figma negado/Docker deseado, y Figma/UX/UI de SQL negado/Blender deseado. **Seis vectores Nomic**: tres confirmaciones fixture, un proyecto y dos altas visuales; todos 768 dimensiones finitas y revisión vigente. Activar consentimiento no agregó llamadas de IA. No se necesitó modificar prompts para resolver este vacío.

Evidencia: [validación SQL/HTTP](../evidencias/2026-10-26-consentimiento/validation.json), [traza SDK/rutas](../evidencias/2026-10-26-consentimiento/service_trace.json), [revisiones conservadas](../evidencias/2026-10-26-consentimiento/activation_result.json).

Capturas: [aviso y atajo](../evidencias/2026-10-26-consentimiento/perfil_aviso_y_atajo.png), [cero candidatos](../evidencias/2026-10-26-consentimiento/candidatos_antes.png), [SQL/Figma tras activar](../evidencias/2026-10-26-consentimiento/dos_candidatos_consentimiento_activado.png), [elección al confirmar](../evidencias/2026-10-26-consentimiento/eleccion_explicita_al_confirmar.png), [guardado sin recomendaciones](../evidencias/2026-10-26-consentimiento/perfil_guardado_sin_recomendaciones.png).

Las tres consolas de navegador no capturaron errores: [organizador](../evidencias/2026-10-26-consentimiento/consola_organizador.json), [perfil](../evidencias/2026-10-26-consentimiento/consola_perfil.json), [alta](../evidencias/2026-10-26-consentimiento/consola_alta.json). Los 403 del ensayo de permisos son peticiones HTTP deliberadas, no un error visual no resuelto.

## Pruebas automáticas

| Control | Resultado | Duración del proceso |
| --- | --- | --- |
| python -m pytest -q | **367 passed**, dos regresiones nuevas | 36.99 s; pytest 35.62 s |
| python -m pip check | Sin dependencias rotas | 0.60 s |
| npm test | **27 passed**, seis casos nuevos y uno existente fortalecido | 1.35 s |
| npm run build | Correcto | 1.24 s |
| npm run lint | 0 errores; 1 advertencia previa | 4.20 s |

[Logs completos](../evidencias/2026-10-26-consentimiento/checks.json). Backend usa SQLite y vectores simulados para aislar consentimiento, autorización y conservación de confirmación/pausa; los lotes anteriores son MySQL/Nomic reales. Persisten deprecación Starlette/httpx y advertencia useEffect en RequireSession. El aviso WebSocket 24678 de algún ensayo SSR corresponde al arnés, no al motor.

## Archivos y límites

Cambios: `RecommendationConsentStatus.jsx`, `ProfileConsentConfirmation.jsx`, integración en ProfileSetupPage/ProfilePage/HomePage/MatchPage, mensaje de CandidatesEmptyState y cliente `activarRecomendaciones` en api.js. Regresiones en `frontend/tests/contracts.test.js` y `backend/tests/test_recommendation_consent.py`. El backend de producción no cambió; sigue verificando identidad y privacidad.

En el proyecto real se observaron metadatos de título/materia/integrantes clasificados como restricciones. Se reprodujeron en QA y no impidieron recomendar al activar el permiso, aunque agregan razones pendientes de verificar. Deben revisarse mediante el editor humano; no se reescribió ese proyecto real. Siguen los límites de requisitos globales por persona, horarios exactos y variabilidad del [informe de escenarios](2026-10-26-escenarios-matching.md).

Solo se usaron consultas de lectura en la principal y GET del endpoint del organizador, con credencial efímera no registrada y sin login/migración de hash. Al principio hubo actividad externa: la principal pasó de ocho a nueve cuentas antes de preparar QA. Desde el snapshot de preparación al final conservó **9 usuarios, 9 perfiles, 2 eventos, 1 solicitud y 0 participantes**, mismos checksums/DDL/revisión. No se copiaron registros personales a QA ni se guardaron tokens, secretos o URL privadas.

Las pestañas y procesos QA se cierran al terminar; se conservan datos ficticios. Corrección sobre `9fcc16a`, rama `feat/ai-matching`, para commit y push solicitados, sin merges ni force.
