# QA real de escenarios y matching — 2026-10-26

## Resultado y alcance

Los recorridos completos de **web, videojuegos y fútbol** funcionan en React, FastAPI, MySQL y Ollama reales: registro de dos personas, interpretación, revisión humana, confirmación, publicación, recomendaciones para ambas partes, invitación, aceptación, equipo después de recargar y edición/reconfirmación del proyecto. Se corrigieron defectos reproducibles de concurrencia del análisis, identidad entre pestañas, extracción y explicaciones. Se conserva el diseño de Isaac, la autenticación, la idempotencia, los bloqueos de equipos y la política de ranking.

El proyecto principal «Gestor de tareas inteligente» devuelve cero candidatos correctamente: los tres perfiles de otras cuentas carecen de consentimiento para recomendaciones. **No se activó consentimiento ni se completó ningún perfil real.** Se mejoró el mensaje vacío para explicar cómo participar sin revelar personas excluidas.

Resultado automático final: **365 backend y 21 frontend aprobados**, pip check correcto, build correcto y lint con cero errores y una advertencia previa. Además: **14 escenarios HTTP/MySQL**, tres recorridos visuales completos y repetición de tres escenarios críticos en otra base vacía. Los pasos de una misma operación se contabilizan como comprobaciones dirigidas, no como escenarios o defectos independientes.

La revisión humana sigue siendo necesaria. Se documentan límites de ranking, horarios y generación; este informe no certifica toda combinación posible ni una IA sin errores.

## Entorno y protección

Inicio: rama `feat/ai-matching`, HEAD `9fb42cd`, árbol limpio. Conservados los commits `2157a43`, `033f97f` y los anteriores de integración de Isaac. Se revisaron el informe original, seguimiento, runbooks, evidencias y código implicado. No hubo push, merges, cambios de rama, reset, clean, migraciones ni instalación de dependencias.

| Componente | Versión utilizada |
| --- | --- |
| Python / Node / npm | 3.13.15 / 24.19.0 / 11.17.0 |
| FastAPI / SQLAlchemy / Pydantic | 0.143.0 / 2.1.4 / 2.14.1 |
| pytest / SDK Ollama | 9.1.1 / 0.6.3 |
| React / router / Vite instalados | 19.3.0 / 7.18.4 / 8.3.4 |
| MySQL | 8.0.46, InnoDB, REPEATABLE-READ |
| Ollama servidor | 0.40.5 |
| Llama / Nomic | llama3.1:8b / nomic-embed-text:latest, 768 dimensiones |
| QA principal de esta ronda | softtek_formador_equipos_qa_matching_20261026_fac76d |
| QA vacía de repetición final | softtek_formador_equipos_qa_matching_final_20261026_071ca0 |
| Servicios separados de prueba | FastAPI 8011/8012/8013 y Vite 5174/5175 |

Las dos bases se crearon vacías usando únicamente definiciones de tablas y la revisión `20261022_6a`; no se copiaron filas personales. Las cinco tablas conservan InnoDB. Las cuentas son ficticias, con direcciones example.com y un secreto JWT exclusivo de cada QA, no publicado. La configuración con Ollama inaccesible usó `127.0.0.1:9` en un backend separado; no se detuvo el Ollama compartido ni se descargaron sus modelos.

Evidencia del entorno, conteos, verificaciones finales y recorridos: [final_validation.json](../evidencias/2026-10-26-matching/final_validation.json). Modelos y digest: [ollama_tags.json](../evidencias/2026-10-26-matching/ollama_tags.json). La instrumentación temporal registra métodos/rutas/estados y salidas de IA ficticias, sin cabeceras ni JWT. Los scripts temporales quedan ignorados en `backend/.venv/qa_matching_20261026/` y `backend/.venv/qa_matching_final_20261026/`; no son infraestructura de la aplicación.

## 1. Diagnóstico del proyecto real vacío

Se inspeccionó la principal con SQL permitido exclusivamente de lectura, sesión de diagnóstico sin autoflush y barrera contra SQL de escritura. Las únicas peticiones a su backend fueron GET; no se hizo login que pudiera migrar hashes. Se verificó identidad del organizador mediante `/auth/me` y coincidencia con el creador.

| Comprobación | Observado |
| --- | --- |
| Proyecto y creador | Creador activo y autenticado correcto; proyecto abierto |
| IA | Requisitos confirmados y estado listo |
| Cupo | Capacidad total 3, sin participantes; dos roles con una vacante cada uno |
| Roles | Especialista en bases de datos y diseñador UX/UI |
| Perfiles | Cuatro en total, incluido creador; confirmados, listos y no pausados |
| Consentimiento | Desactivado en los cuatro; tres candidatos ajenos excluidos correctamente |
| Acciones pendientes | Cero; no son la causa de la exclusión |
| Adaptador ORM | Cero recomendaciones |
| Endpoint | HTTP 200, `[]`; no hay resultados perdidos en el mapper React |

No es una base sin perfiles ni un fallo de cupo: son perfiles excluidos por privacidad. El nuevo estado vacío explica consentimiento, confirmación, pausa, campos permitidos, membresía y acciones pendientes; permite actualizar. No muestra cantidades ni identidades privadas. Reproducción anonimizada: [principal_diagnosis.json](../evidencias/2026-10-26-matching/principal_diagnosis.json). El ejemplo visual de la nueva explicación pertenece exclusivamente a QA: [captura](../evidencias/2026-10-26-matching/web_sin_candidatos_explicado.png).

## 2. Escenarios MySQL y expectativas

Las expectativas se guardaron antes de ejecutar el lote: [scenario_expectations.json](../evidencias/2026-10-26-matching/scenario_expectations.json). Los 14 escenarios usan registro, confirmación revisada y publicación por HTTP real; generan embeddings Nomic reales. **Las confirmaciones del lote son fixtures declarados, no 14 extracciones Llama ni 14 recorridos visuales.** El corpus y los tres recorridos siguientes prueban la generación por separado.

| Escenario | Evidencia requerida y contraste | Resultado observado |
| --- | --- | --- |
| Web | Creador Python/FastAPI; SQL/Figma obligatorios, Git deseable; especialistas distintos | SQL/Git y UX/UI/Figma acreditan solo sus hechos; invitación y equipo persistidos |
| Videojuegos | UE5, Blender, diseño de niveles | Herramientas confirmadas conservadas; aportes complementarios, sin deducir otras capacidades |
| Datos | SQL y visualización frente a Python solamente | El primero acredita requisitos; Python solo no acredita SQL ni visualización |
| Interfaz | Figma obligatorio, UX/UI y prototipado | Figma permanece obligatorio; perfil SQL no lo acredita |
| Fútbol | Creador delantero, portero requerido y defensa deseable | Rol portero aceptado y fila real de integrante; defensa no se convierte en portero |
| Game jam | Programación UE5 y artista Blender/diseño | Complementariedad y explicaciones respaldadas por declaraciones |
| Escolar | Organización frente a presentaciones, intereses compartidos | El interés común no acredita organización |
| Obligatorias | SQL frente a Git solamente | Git se reconoce como deseable; SQL desconocido no figura cumplido |
| Interés | Interés Python sin habilidad frente a Python confirmado | No se acredita Python al primer perfil; confirmación adicional del interés en MySQL conserva fortalezas vacías |
| Negación | «No sé SQL» frente a SQL confirmado | Corpus elimina habilidad negada; confirmación humana en QA mantiene SQL sin acreditar, no inventa aprendizaje |
| Incompleto | Declaración sin confirmar y candidato confirmado sin vector | Ninguna declaración pendiente acredita habilidad; SQL confirmado funciona sin embedding y el reintento recupera Nomic |
| Vacantes | Dos plazas de un rol, invitación y adhesión | Dos aceptaciones válidas; luego proyecto lleno y sin acción disponible |
| Privacidad | Figma confirmado con y sin consentimiento | Perfil sin consentimiento excluido, sin revelar su evidencia |
| Horarios | Restricción lunes 16–18 y bloques de disponibilidad | Condición conservada como pendiente de verificar; no se inventa coincidencia de horas |

**14/14 escenarios; 271 comprobaciones dirigidas aprobadas.** Incluyen top_n, ambos públicos, idempotencia, requisitos, pending/member exclusion y filas reales del equipo. Las comparaciones revisan elegibilidad y sustento de las explicaciones, no una posición exacta por ID. [Resultados y explicaciones](../evidencias/2026-10-26-matching/scenario_results.json), [comprobaciones](../evidencias/2026-10-26-matching/scenario_checks.json).

Un lote adicional aprobó **17 comprobaciones**: pausa, campo de habilidad oculto, cuenta inactiva y token 403, vector incompatible, edición de perfil, fallos reales de conexión del SDK, confirmación recuperable, conservación de fuente confirmada, reintento Nomic, publicación idempotente y concurrencia del último cupo. Dos aceptaciones simultáneas produjeron **[200,409]**, con exactamente un participante; el equipo lleno dejó de ofrecer candidatos. [extended_results.json](../evidencias/2026-10-26-matching/extended_results.json).

La base nueva de repetición final aprobó **3/3 escenarios, 57 comprobaciones**: web, videojuegos y fútbol, nueve usuarios nuevos y tres equipos. No reutilizó tokens, perfiles ni filas del primer lote. [Resultados](../evidencias/2026-10-26-matching/fresh_scenario_results.json), [comprobaciones](../evidencias/2026-10-26-matching/fresh_scenario_checks.json).

## 3. Recorridos visuales reales

Se utilizó el navegador integrado mediante automatización visual/DOM. Se operaron formularios y botones React; no se sustituyó este recorrido por inserciones ORM. Cada dominio registró organizador y candidato ficticios en sesiones independientes, revisó la salida Llama, confirmó permisos y habilidades, publicó, consultó candidatos y proyectos recomendados, invitó, aceptó y recargó el equipo. También se editaron y reconfirmaron los tres proyectos.

| Recorrido | Filas QA | Resultado y evidencia |
| --- | --- | --- |
| Web | Usuarios 5/6; evento 2 | SQL/Git del candidato, Figma aún por acreditar en el equipo; invitación aceptada y dos integrantes tras recargar. [Equipo](../evidencias/2026-10-26-matching/web_equipo_persistido.png), [recomendación al candidato](../evidencias/2026-10-26-matching/web_candidato_proyecto.png) |
| Videojuegos | Usuarios 49/50; evento 17 | Organizador UE5/diseño de niveles, artista Blender; aceptación del rol Artista 3D y cobertura de ambas herramientas. [Candidatos](../evidencias/2026-10-26-matching/videojuego_recomendaciones.png), [equipo recargado](../evidencias/2026-10-26-matching/videojuego_equipo_recargado.png) |
| Fútbol | Usuarios 51/52; evento 21 | Organizador delantero, candidato portero/defensa sin experiencia profesional positiva inventada; aceptación como portero. Dos habilidades cubiertas y todavía una vacante de defensa: habilidad cubierta y rol ocupado son conceptos distintos. [Perfil](../evidencias/2026-10-26-matching/futbol_perfil_sin_experiencia_inventada.png), [equipo recargado](../evidencias/2026-10-26-matching/futbol_equipo_recargado.png) |

Actualizaciones verificadas después de editar:

- Web: se retiró SQL obligatorio y se mantuvo Figma obligatorio/Git deseable. Se corrigió humanamente la composición ya existente que Llama había clasificado como restricción. El integrante SQL aceptado ya no aparece como candidato. [Invalidación](../evidencias/2026-10-26-matching/web_editado_invalida.png), [reconfirmación](../evidencias/2026-10-26-matching/web_reconfirmado_actualizado.png).
- Videojuegos: se agregó participación remota. Tras revisar/reconfirmar y recargar se ve la nueva condición pendiente de verificar, vector vigente y estado listo. [Captura](../evidencias/2026-10-26-matching/videojuego_reconfirmado.png).
- Fútbol: sábado cambió a lunes por la tarde. Mientras se revisaba, la cobertura quedó desconocida; después de reconfirmar recuperó datos actuales y eliminó la condición anterior. [Durante revisión](../evidencias/2026-10-26-matching/futbol_equipo_durante_revision.png), [reconfirmación](../evidencias/2026-10-26-matching/futbol_reconfirmado.png).

La comprobación final SQL/HTTP añade **26 verificaciones**, incluidas seis confirmaciones de perfiles, tres revisiones actuales de proyecto, membresías aceptadas, exclusión del integrante y conservación de la principal. Los detalles están en `final_validation.json`; no se suman a los 14 dominios como escenarios nuevos.

Se capturaron errores reales previos a la corrección: 409 de análisis duplicados y 403 por identidad mezclada entre pestañas. El backend rechazó el acceso ajeno; no se observó fuga de perfil privado. Además hubo un fallo de preparación del laboratorio: CORS rechazó el origen QA 5175 con OPTIONS 400 antes del registro. Se autorizó ese origen únicamente en el servidor temporal QA y se repitió; no se modificó el CORS de producción. La consola guardada conserva ese `Failed to fetch`; **no se afirma que toda la sesión tuvo cero errores**. [Consola organizador](../evidencias/2026-10-26-matching/consola_organizador.json), [consola candidato](../evidencias/2026-10-26-matching/consola_candidato.json). Las trazas también incluyen un 403 deliberado de cuenta inactiva, un 409 esperado del último cupo y un 422 del script por omitir campos obligatorios de visibilidad, corregido en el arnés. Ninguno se presenta como error de producción resuelto por cambiar la aplicación.

## 4. Primer análisis, calentamiento y recuperación

Al comenzar, `/api/ps` mostraba cero modelos cargados. No se forzó descarga ni recarga del Ollama compartido. El primer efecto de React/StrictMode envió dos POST idénticos: ambos SDK terminaron correctamente, en **4.333 y 5.491 s**, con carga del modelo de aproximadamente **2.80/2.81 s**. El backend entregó un resultado y rechazó el competidor con 409 por estado cambiado. El intento con modelo ya cargado volvió a duplicar solicitudes: **1.386 y 2.662 s** de SDK y otro 409.

La captura [primer_intento_409.png](../evidencias/2026-10-26-matching/primer_intento_409.png) muestra la UI lista pese al 409 competidor; el nombre identifica la traza, **no demuestra un error visible del primer intento**. No se reprodujo de forma natural el fallo visible que relató el usuario, ni un timeout de carga fría. Sí se reprodujo la carrera capaz de producir resultados/conflictos dependientes del orden. No se aumentaron timeouts para ocultarla.

Corrección: compartir solo la petición de interpretación en vuelo para la misma sesión, ruta y entrada exacta. Al terminar o fallar se elimina; un reintento envía una petición nueva. No hay caché de resultados ni StrictMode desactivado. Otra entrada o sesión no comparte trabajo. El backend compara además la huella del texto pendiente para impedir que un análisis antiguo sobrescriba otro más nuevo.

Se probó un error **visible** de conexión con el SDK real en un backend QA apuntando a puerto inaccesible: HTTP 503, formulario conservado y botón de reintento. Se recuperó únicamente ese backend, se pulsó reintentar sin volver a escribir y se confirmó con Llama/Nomic reales. [Fallo](../evidencias/2026-10-26-matching/juego_ollama_caido_formulario_conservado.png), [recuperación](../evidencias/2026-10-26-matching/juego_reintento_recuperado.png). Otro ensayo de conexión fallida conservó una confirmación previa en MySQL. Dos fallos ConnectionError controlados, cero timeouts observados.

Trazas: [antes/durante corrección](../evidencias/2026-10-26-matching/service_trace.json), [recuperación](../evidencias/2026-10-26-matching/service_trace_recovery.json), [servicio inaccesible](../evidencias/2026-10-26-matching/service_trace_offline.json). Los OPTIONS no cuentan como análisis. Los metadatos SDK están en nanosegundos; `seconds` mide tiempo de pared.

## 5. Calidad de extracción: salida cruda, filtros y revisión

Se ejecutaron secuencialmente **14 llamadas de corpus** (10 perfiles, cuatro proyectos) y **cuatro repeticiones focalizadas reales**. Las 18 llamadas generaron JSON válido. Sumando 18 intentos instrumentados de recorridos y recuperación: **36 intentos de chat, 34 respuestas obtenidas y dos ConnectionError deliberados; cero timeouts**. Duración por intento: mínimo 0.806 s, mediana 1.5565 s y máximo 5.491 s. Esto no invalida los timeouts históricos del informe original.

El detector inicial marcó 12 PASS/2 FAIL: faltaban portero y Git. Esa cifra **no es una aprobación semántica completa**: al revisar manualmente también faltaban prototipado, FastAPI y parte de los roles deportivos, no incluidos suficientemente en las primeras expectativas. Se conservaron las expectativas y salidas iniciales sin reescribirlas; se ampliaron los controles posteriores.

| Entrada / salida cruda observada | Problema o defensa | Resultado final delimitado |
| --- | --- | --- |
| «Sé programar con SQL y trabajo con Python» | Variantes de etiqueta | SQL y Python, catálogo literal compartido |
| «Trabajo con Git. Uso FastAPI»; crudo `trabajar con Git`, `usar FastAPI` | Filtro anterior descartaba habilidades explícitas | Git y FastAPI preservados |
| «Diseño interfaces UX/UI en Figma. Hago prototipado» | Prototipado desaparecía durante filtrado | UX/UI, Figma y prototipado preservados |
| «Juego de portero y defensa»; crudo sin habilidades | Omisión del modelo | Recuperación acotada de ambas declaraciones literales |
| «Buscamos portero, defensa y delantero»; crudo solo restricción de portero | Roles omitidos/requisito mal clasificado | Roles coordinados recuperados; portero obligatorio |
| Figma obligatorio; crudo lo puso en restricciones | Clasificación incorrecta del modelo | Figma se conserva obligatorio; no es una condición logística |
| «Me interesa Python. No sé programar en Python»; crudo añadió aprendizaje | Objetivo inventado por Llama | Sin fortaleza ni aprendizaje inferido; solo interés Python |
| «No tengo experiencia profesional»; crudo lo puso en experiencia | Experiencia negativa clasificada como positiva | Experiencia positiva vacía |
| Interés educación y `Me interesa la educación` | Duplicados por prefijos | Una etiqueta dentro de intereses, sin moverla a fortalezas |
| «Tal vez pueda ayudar en algo» | Riesgo de capacidades inventadas | Sin herramientas acreditadas |

Catálogo **2026-10-26.v4**, 14 conceptos y alias finitos; no similitud difusa ni competencia inferida por embedding. Se conservan negaciones, metas e intereses separados de habilidades. También se elimina una misma habilidad de deseables cuando ya es obligatoria, tanto en el mapper de publicación como en el contrato backend, incluidas equivalencias SQL/programar con SQL.

Se volvió a procesar el JSON capturado de los 14 casos con el parser final: **14/14 PASS con expectativas corregidas**. Es **replay con salida capturada y cliente simulado**, no otras 14 llamadas Llama. Luego se repitieron cuatro entradas con Llama real: deporte, texto largo, requisitos por rol y fútbol, **4/4 PASS**. JSON crudo, salida procesada, omisiones y duraciones: [corpus inicial](../evidencias/2026-10-26-matching/corpus_initial.json), [replay](../evidencias/2026-10-26-matching/corpus_replay.json), [repeticiones reales](../evidencias/2026-10-26-matching/corpus_focused.json).

La confirmación humana no se eliminó: en fútbol se corrigió una frase redundante de experiencia y en web una restricción mal clasificada. Las capturas y los perfiles/requisitos finales en `final_validation.json` muestran la revisión persistida; no deben confundirse con la respuesta cruda del modelo. Las reglas nuevas solo cubren construcciones literales comprobadas, no todo el idioma español.

## 6. Matching, persistencia y límites

Se verifican hechos confirmados y permitidos, no solo cercanía de vectores ni posición del ranking. Consentimiento desactivado, pausa, inactividad, integrante y acción pendiente excluyen correctamente. Ocultar una habilidad impide que acredite el requisito; un vector incompatible o ausente no elimina las habilidades explícitas. Un interés, objetivo de aprendizaje o texto negado no acredita SQL/Python. La negación libre impide promover una fortaleza; no se introduce un nuevo contrato HTTP de evidencia negativa estructurada.

Los 20 proyectos finales de la primera QA están listos. Hay **46 perfiles listos, uno sin_contenido y uno obsoleto deliberadamente sin confirmar**. Los **46 vectores de perfil y 20 de evento** almacenados son finitos, de 768 dimensiones y con revisión vigente; cero incompatibles al cierre. Los seis perfiles y tres proyectos visuales tienen modelo y revisión actuales. [vectors_final.json](../evidencias/2026-10-26-matching/vectors_final.json).

Una edición invalida las confirmaciones/vectores anteriores; la UI no los presenta como cobertura actual durante revisión. La confirmación con Nomic inaccesible guarda datos y devuelve estado recuperable, no 500 engañoso. La creación repetida con la misma clave conserva la misma fila, y las rutas existentes de reintento recuperan el vector. Estas funciones previas se volvieron a ensayar, sin sustituirlas por colas o servicios nuevos.

| Base | Usuarios | Perfiles | Proyectos | Solicitudes/invitaciones | Participantes incorporados |
| --- | --- | --- | --- | --- | --- |
| Primera QA | 48 | 48 | 20 | 20 | 19 |
| QA nueva final | 9 | 9 | 3 | 3 | 3 |
| Total ficticio | 57 | 57 | 23 | 23 | 22 |

Los creadores aparecen en la proyección del equipo y no necesitan una fila adicional en participantes_evento. Las cantidades de solicitudes son filas persistidas; los reintentos de una publicación no se cuentan como proyectos nuevos. No se borró ni reinició ninguna base.

Consultas reproducibles, conectándose **solo a una de las QA identificadas**:

```sql
SELECT DATABASE();
SELECT id_evento, id_usuario, rol FROM participantes_evento WHERE id_evento IN (2,17,21);
SELECT id_evento, estado FROM solicitudes_equipo WHERE id_evento IN (2,17,21);
SELECT id_evento, estado_ia, JSON_LENGTH(embedding_requisitos) AS dimensiones,
       embedding_fuente_revision = requisitos_fuente_revision AS revision_actual
FROM eventos WHERE id_evento IN (2,17,21);
SELECT perfil_estado_ia, COUNT(*) FROM perfiles_usuarios GROUP BY perfil_estado_ia;
```

## 7. Errores reproducidos y correcciones

| Hallazgo | Gravedad observada | Reproducción anterior / causa | Corrección y regresión |
| --- | --- | --- | --- |
| Identidad mezclada entre pestañas | ALTO funcional; backend mantuvo autorización | Registrar candidato en segunda pestaña, volver al organizador: identidad de localStorage cambiaba, JWT de sessionStorage no; peticiones ajenas 403 | Identidad y token por sessionStorage; `/auth/me` repuebla la sesión propia. Test de almacenes con identidades distintas; repetición visual de ambas cuentas. [Antes](../evidencias/2026-10-26-matching/sesiones_mezcladas_antes.png) |
| Análisis duplicado | MEDIO | StrictMode ejecutaba dos suscripciones; dos POST y 409 competidor | Petición en vuelo compartida por sesión/entrada; cuatro pruebas de separación, limpieza, fallo/reintento y proyectos |
| Análisis antiguo sobrescribe texto nuevo | ALTO integridad | Barreras controladas: dos entradas distintas, resultado antiguo aceptado 200 | Huella de texto pendiente comprobada al éxito y error; antiguo 409, nuevo 200; no se sobrescribe borrador vigente |
| Omisiones/equivalencias literales | MEDIO | Git, FastAPI, prototipado y roles deportivos perdidos; interés duplicado | Catálogo v4, reconocimiento afirmativo acotado y limpieza de prefijos dentro de su categoría; regresiones de negación/metas |
| Requisito obligatorio también deseable | MEDIO | Publicar roles no indispensables agregaba SQL/Figma otra vez a deseables | Mapper filtra duplicados; backend canoniza y da precedencia a obligatorio; pruebas frontend/backend |
| Composición de equipo como restricción | MEDIO | Crudo «Ya incorporamos especialista…» como condición de participación | Filtro de prefijos literales observados, sin inferir nuevas restricciones; regresión conservando Figma |
| Vacío de candidatos sin orientación | BAJO | No explicaba cómo habilitar recomendaciones | Mensaje y actualización sin divulgar excluidos; dos regresiones de vacío/vacantes |
| Interés compartido anunciado como proyecto | BAJO accesibilidad | Texto sr-only «Coincide con el proyecto» en perfil de otra persona | Variante «Interés en común»; aserción existente fortalecida |

Se guardaron fallos antes de corregir: [ocho regresiones semánticas](../evidencias/2026-10-26-matching/semantic_before.txt), [carrera](../evidencias/2026-10-26-matching/race_before.txt), [duplicación frontend](../evidencias/2026-10-26-matching/frontend_before.txt), [requisitos duplicados](../evidencias/2026-10-26-matching/requirements_before.txt), [texto accesible](../evidencias/2026-10-26-matching/accessibility_before.txt). Solo se normalizaron a UTF-8 y se retiraron espacios al final de las líneas de estos logs. La advertencia WebSocket 24678 de los primeros tests era del arnés SSR paralelo; se deshabilitó HMR solo en esos servidores de prueba.

## 8. Archivos modificados y pruebas

| Archivos | Motivo |
| --- | --- |
| `backend/app/api/routes/perfiles.py` | Rechazar resultados de análisis para texto pendiente diferente |
| `backend/app/services/ai/skill_catalog.py`, `skill_terms.py` | Catálogo v4 y expresiones afirmativas literales |
| `backend/app/services/ai/profile_parser.py`, `event_parser.py` | Intereses sin duplicación, roles deportivos y restricciones de composición |
| `backend/app/services/ai/schemas.py` | Obligatorio/deseable sin doble acreditación de la misma habilidad |
| `frontend/src/services/api.js` | Compartir interpretación en vuelo, identidad por sesión y requisitos sin duplicados |
| `frontend/src/lib/session.js`, `components/auth/RequireSession.jsx`, `components/layout/AppLayout.jsx` | Lectura, verificación y cierre de identidad de la pestaña |
| `frontend/src/pages/AuthPage.jsx`, `ProfileSetupPage.jsx`, `ProfilePage.jsx`, `StudentsPage.jsx` | Consumidores coherentes de la misma identidad autenticada |
| `frontend/src/components/project/CandidatesEmptyState.jsx`, `pages/ProjectDetailPage.jsx` | Estado vacío informativo y actualización |
| `frontend/src/components/profile/PublicProfile.jsx`, `components/ui/SkillChip.jsx` | Texto accesible veraz para intereses compartidos |
| `backend/tests/test_matching_real_regressions.py`, `real_matching_scenarios.py` | Once regresiones nuevas y corpus/expectativas ficticias reutilizables |
| `backend/tests/test_matching_contracts.py`, `test_event_pipeline.py` | Versión del catálogo y defensa explícita conservando exclusión de portero negado |
| `frontend/tests/interpretation.test.js`, `session.test.js`, `contracts.test.js` | Ocho casos nuevos, aserción accesible fortalecida y SSR sin HMR |
| Este informe, seguimiento, runbooks y `docs/qa/evidencias/2026-10-26-matching/` | Resultados, límites, contratos vigentes y evidencia filtrada |

No se tocaron pesos/umbrales de ranking, JWT/hashes, bloqueos transaccionales de equipo, framework, esquema ni dependencias. El ajuste de un test previo de deporte ahora exige defensa explícita donde antes esperaba lista vacía, y sigue excluyendo portero negado; no rebaja la validación.

| Comando final | Resultado | Tiempo de proceso |
| --- | --- | --- |
| python -m pytest -q | 365 passed, frente a 354 anteriores | 33.75 s; pytest 32.54 s |
| python -m pip check | No broken requirements found | 0.47 s |
| npm test | 21 passed, frente a 13 anteriores | 2.00 s |
| npm run build | Correcto, 1991 módulos | 0.98 s |
| npm run lint | 0 errores, 1 advertencia previa | 3.44 s |

Logs completos: [checks.json](../evidencias/2026-10-26-matching/checks.json). Pytest usa SQLite/configuración ficticia y sus mocks; no se presenta como MySQL real. Los lotes HTTP y visuales usan MySQL real; las confirmaciones generan Nomic real. Persisten deprecación de Starlette TestClient/httpx y advertencia de dependencia `state` en RequireSession.jsx:29. No se debilitaron tests ni se instalaron paquetes para ocultarlas.

## 9. Pendientes y límites, por impacto

1. **MEDIO — Orden entre evidencia parcial:** en el proyecto visual de videojuegos un candidato con Git, sin Blender acreditado, precedió al artista Blender. La política actual agrupa evidencia y renormaliza dimensiones disponibles; varios candidatos permanecen `needs_review` por requisitos obligatorios desconocidos. Las explicaciones no les atribuyen Blender. No se cambió el ranking para conseguir un orden deseado. Conviene una revisión acotada de política sobre este contraejemplo antes de prometer que «el mejor especialista siempre sale primero».
2. **MEDIO — Requisitos globales y roles:** SQL y Figma globales se evalúan para cada persona; el especialista SQL puede quedar needs_review por Figma aunque otro rol la cubra. La elección del rol sigue siendo manual. No existe una matriz nueva de requisitos por rol ni se añadió en este encargo.
3. **MEDIO — Horarios (QA-11):** bloques `lun-tarde` no demuestran compatibilidad exacta con lunes 16–18. Se conserva la restricción como pendiente de verificar. La edición real de fútbol actualizó la condición; no se declara una comprobación horaria que el motor no implementa.
4. **MEDIO — Variabilidad Llama:** corpus delimitado, no prueba universal. Persisten posibles omisiones fuera del catálogo, resúmenes redundantes y construcciones complejas. La revisión humana corrige la versión que se confirma. No hubo timeout natural en esta ronda, por lo que no se da por reproducido ni resuelto todo fallo de primer intento relatado.
5. **Pendiente heredado — Contraseñas bcrypt antiguas >72 bytes:** conserva rechazo explícito seguro y limitación de recuperación descrita en el seguimiento; esta ronda no agrega restablecimiento.
6. **No ejecutado:** carga sostenida, caída/reinicio de MySQL, reinicio completo de backend durante una aceptación, matriz de móviles/navegadores, auditoría exhaustiva de accesibilidad/seguridad y todas las carreras posibles. Las recargas de navegador y nuevas sesiones sí se probaron. No se desarrollaron reuniones, feedback ni funcionalidades sociales.

No se identificó un nuevo defecto CRÍTICO demostrado. Los fallos funcionales altos reproducidos de esta ronda tienen corrección y regresión; los límites anteriores impiden presentar el orden generativo/semántico como garantía automática de selección. El MVP permite los recorridos de formación de equipo verificados con revisión humana.

## 10. Principal intacta y cierre Git

**La base principal `softtek_formador_equipos` no fue alterada por esta tarea.** Conteos/checksums iguales al principio y al final de esta ronda; los datos reales añadidos por el usuario desde la auditoría anterior no se confundieron con escrituras de QA.

| Tabla principal | Filas antes/después | Checksum antes/después |
| --- | --- | --- |
| usuarios | 4 / 4 | 3844398997 / 3844398997 |
| perfiles_usuarios | 4 / 4 | 4192465674 / 4192465674 |
| eventos | 1 / 1 | 897947035 / 897947035 |
| solicitudes_equipo | 0 / 0 | 0 / 0 |
| participantes_evento | 0 / 0 | 0 / 0 |

DDL SHA-256 igual: `fb8d8647973fdda177c17a2e4deabc571886f26ba2160e6055f8a12a52dd9128`; revisión igual: `20261022_6a`. No se ejecutó DDL, stamp, limpieza, reparación ni cambio de consentimiento sobre la principal. No se guardaron URL privadas, contraseñas, secretos o JWT en este informe/evidencias.

Al cierre se cerraron las dos pestañas temporales y se detuvieron únicamente los procesos QA creados. Los listeners previos 8000/5173/3306/11434 conservaron PID 43532/2108/9036/10056, respectivamente; no se reconfiguraron ni se forzó su reinicio. Se dejaron las bases ficticias y evidencias para inspección.

Se validó `git diff --check`, se revisó el contenido preparado para evitar secretos y se conservaron los commits previos. Esta ronda se registra en un commit **local**, identificado por el mensaje `fix(mvp): stabilize analysis sessions and validate real matching`, con padre `9fb42cd`; el hash se entrega en la respuesta final y puede consultarse con `git log -1 --oneline`. Rama final `feat/ai-matching`, árbol limpio después del commit. No se realizó push ni merge.
