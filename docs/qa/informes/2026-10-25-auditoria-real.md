# Auditoría real del MVP — Softtek Formador de Equipos

Fecha del encargo: 2026-10-25. Repositorio: `D:\projects\Softtek_Formador_Equipos`. Rama auditada: `feat/ai-matching`. Alcance: auditoría, sin correcciones de producción.

## 1. Resumen ejecutivo

El recorrido principal funciona con React, FastAPI, MySQL y Ollama reales: registro, análisis y revisión humana del perfil, confirmación con Nomic, publicación de proyecto, recomendaciones, invitación/adhesión, aceptación y recuperación del equipo tras recargar. Las tres carreras concurrentes ensayadas respetaron las reglas de capacidad, rol único y duplicados.

El MVP todavía presenta fallos que conviene resolver antes de considerarlo cerrado: datos JSON inválidos de un perfil pueden romper el directorio completo; la autenticación permite contraseñas vacías y trunca las largas; una caída de Ollama devuelve 500 después de persistir y permite duplicar proyectos al reintentar; un proyecto con habilidades de rol malformadas llega a romper la pantalla React. La extracción y normalización tampoco conservan siempre requisitos y habilidades útiles para el matching.

La base principal no fue alterada. No se hicieron commits, push, merges ni cambios de rama. Se conservaron el frontend Isaac, matching y recomendaciones. Los únicos archivos nuevos del repositorio son este informe y sus evidencias; los scripts temporales están dentro del entorno virtual ignorado.

Resultados: **234/234 pruebas existentes aprobadas**, más **137 comprobaciones dirigidas: 112 aprobadas y 25 fallidas**. Estos casos incluyen dependencias entre pasos y varios síntomas del mismo defecto: no equivalen a 25 errores independientes. Las llamadas del lote Llama se contabilizan aparte: **26 intentos, 22 JSON válidos y 4 timeouts**. Hubo además dos análisis reales desde React; total de intentos generativos instrumentados/observados: **28**. La revisión semántica de los 26 intentos del lote encontró 10 sin observaciones, 12 con defectos de calidad/integración y 4 bloqueados. No se suman esas llamadas otra vez como recorridos completos.

## 2. Entorno utilizado

| Componente | Versión / configuración observada |
| --- | --- |
| SO y shell | Windows; PowerShell |
| Python | 3.13.15 |
| Node / npm | 24.19.0 / 11.17.0 |
| React / router / empaquetado | React 19.3.0; react-router-dom 7.18.4; Vite 8.3.4 |
| MySQL | 8.0.46; InnoDB; REPEATABLE-READ |
| FastAPI / Starlette | 0.143.0 / 1.8.0 |
| SQLAlchemy / PyMySQL | 2.1.4 / 1.2.3 |
| Pydantic / Alembic | 2.14.1 / 1.20.0 |
| httpx / ollama Python | 0.28.1 / 0.6.3 |
| PyJWT / passlib / bcrypt | 2.15.1 / 1.7.4 / 4.0.1 |
| pytest | 9.1.1 |
| Ollama servidor | 0.40.5 |
| Generación | llama3.1:8b; lote secuencial, timeout 60 s por intento |
| Embeddings | nomic-embed-text:latest; identificador persistido nomic-embed-text; 768 dimensiones |
| Base de QA | softtek_formador_equipos_qa_20261025_2120dd |
| Backend QA | 127.0.0.1:8011, proceso uvicorn separado |
| Simulación aislada | 127.0.0.1:8012; solo ese proceso apunta Ollama a 127.0.0.1:9 |
| React QA | 127.0.0.1:5174; VITE_API_URL apunta al backend QA |
| Servicios previos | Backend 8000, frontend 5173, MySQL 3306 y Ollama 11434 detectados; no se reiniciaron ni reconfiguraron |

Modelos instalados utilizados (digest obtenido del servidor local):

| Modelo | Digest | Bytes |
| --- | --- | --- |
| nomic-embed-text:latest | 0a109f422b47e3a30ba2b10eca18548e944e8a23073ee3f3e947efcf3c45e59f | 274302450 |
| llama3.1:8b | 46e0c10c039e019119339687c3c1757cc81b9da49709a3b3924863ba87ca666e | 4920753328 |

También estaba instalado llama3.2:3b; no se utilizó. No se imprimieron credenciales, URL de conexión, AUTH_SECRET ni tokens. Se generó un secreto distinto exclusivamente para QA, mantenido en memoria de los procesos. Las cuentas de prueba usan datos ficticios y correos example.com.

## 3. Estado inicial Git, esquema y protección de la base principal

HEAD inicial: `568026a` — `docs: record MVP completion, validation and MySQL limits`. Rama `feat/ai-matching`, 12 commits por delante de su referencia de seguimiento; árbol inicial limpio. Se revisaron README, documentos de estado/cierre, configuración de ejemplo, instrucciones operativas, ORM, rutas, contratos, servicios IA y consumidores React. Los README internos del núcleo IA conservan apartados históricos que describen adaptadores aún no existentes; el código y los documentos de cierre son la referencia para el estado actual.

La base QA se creó vacía con permisos del servidor. Se copiaron las definiciones `SHOW CREATE TABLE` de las cinco tablas, sin copiar registros; se registró la revisión Alembic solo en QA. No se ejecutó upgrade/downgrade ni stamp sobre la principal durante esta auditoría.

Se comprobaron las cinco tablas, motor InnoDB, claves primarias, siete relaciones foráneas, índices, correo único y unicidad `(id_evento,id_usuario)` en participantes. Todos los nombres de columnas ORM están presentes, sin columnas extra respecto al ORM inspeccionado, y los campos JSON usan JSON nativo. La revisión es `20261022_6a`. Hay diferencias de representación documentables: fechas de creación TIMESTAMP frente a DateTime ORM y nombres/índices redundantes de claves primarias; no se detectó una columna o unicidad indispensable ausente. Esta inspección no demuestra que ejecutar desde cero todas las migraciones produzca exactamente ese esquema: eso no se ensayó.

SQL mode observado: `ONLY_FULL_GROUP_BY, STRICT_TRANS_TABLES, NO_ZERO_IN_DATE, NO_ZERO_DATE, ERROR_FOR_DIVISION_BY_ZERO, NO_ENGINE_SUBSTITUTION`.

| Tabla principal | Filas antes | Filas después | Checksum antes/después |
| --- | --- | --- | --- |
| usuarios | 1 | 1 | 101962764 / 101962764 |
| perfiles_usuarios | 1 | 1 | 2746401420 / 2746401420 |
| eventos | 0 | 0 | 0 / 0 |
| solicitudes_equipo | 0 | 0 | 0 / 0 |
| participantes_evento | 0 | 0 | 0 / 0 |

Huella SHA-256 del DDL antes/después: `000c70b44ca454ac24551c35ee36780ad1d729221e175bdbb51f581cd9fa8dbe`. Coinciden conteos, checksums, DDL y Alembic. Solo se efectuaron SELECT, SHOW e inspección/checksum sobre la principal. **No se modificaron sus registros ni su esquema.**

## 4. Resultados por área y comandos de referencia

PASS significa que se cumplió la expectativa concreta descrita; no certifica toda el área. FAIL significa expectativa incumplida, incluyendo limitaciones de contrato identificadas. BLOCKED significa falta de resultado evaluable por timeout. Las filas D/F y E/F combinan persistencia con generación de embedding y se cuentan una sola vez.

| Área | Ejecutados | Aprobados | Fallidos | Bloqueados |
| --- | --- | --- | --- | --- |
| C | 30 | 25 | 5 | 0 |
| D/F | 12 | 12 | 0 | 0 |
| E | 6 | 4 | 2 | 0 |
| E/F | 10 | 10 | 0 | 0 |
| F | 8 | 3 | 5 | 0 |
| G | 30 | 24 | 6 | 0 |
| H | 22 | 22 | 0 | 0 |
| I | 18 | 12 | 6 | 0 |
| I-HTTP | 1 | 0 | 1 | 0 |
| Total dirigido | 137 | 112 | 25 | 0 |
| Llama: revisión semántica separada | 26 | 10 | 12 | 4 |

| Comando | Resultado | Duración del proceso | Advertencia |
| --- | --- | --- | --- |
| python -m pytest -q | 234 passed | 15.54 s; pytest informa 14.26 s | 1 deprecación Starlette TestClient/httpx |
| python -m pip check | Sin dependencias rotas | 0.63 s | Ninguna |
| npm run build | Correcto; 1989 módulos | 1.15 s; Vite informa 335 ms | JS principal 483.37 kB, gzip 139.55 kB |
| npm run lint | 0 errores, 1 warning | 3.99 s | RequireSession.jsx:29: dependencia state de useEffect |

El número de pytest coincide exactamente con la referencia de 234. Se ejecutó con configuración de prueba SQLite/secreto QA para impedir conexión accidental a la principal. Esas pruebas siguen siendo unitarias/con mocks según sus fixtures; su resultado no sustituye las pruebas MySQL descritas aquí. No se editaron tests para forzar resultados. Las observaciones adicionales se escribieron como scripts temporales fuera del código de aplicación.

No ejecutados / límites de cobertura (sin afirmar aprobación): migración completa desde cero; recuperación tras reinicio del servidor MySQL o backend; carga sostenida/fuzzing/penetración exhaustiva; navegadores móviles y accesibilidad completa; matrices exhaustivas de longitud Unicode en contraseñas; error real de JSON generado por Llama (los 22 resultados obtenidos validaron); carrera de cálculo Nomic de larga duración contra una edición simultánea (se verificó descarte por revisión, no esa carrera real); generación opcional LLM de explicaciones; todos los posibles endpoints ajenos al MVP. La negación estructurada negativa se comprobó en el motor puro, no mediante un contrato HTTP que permita declarar polaridad negativa. La búsqueda por habilidad se comprobó por HTTP y lectura del contrato del buscador, sin atribuirle un recorrido visual de búsqueda ejecutado.

## 5. Hallazgos priorizados y reproducción

No se identificó un hallazgo CRÍTICO demostrado. Las severidades indican impacto observado, no una puntuación CVSS ni una prueba de explotación fuera de QA. Todas las reproducciones siguientes corresponden a cuentas/base ficticias.

### QA-01 — ALTO: un perfil propio malformado rompe el directorio global

Casos C27/C28. Autenticarse como una cuenta de QA y enviar `PUT /perfil/{id_propio}` con `{"datos_crudos":{"visibilidad":["not-an-object"]}}`. Devuelve **200**. Otro usuario consulta `GET /perfil/estudiantes/?limit=200`: **500**; el perfil público también devuelve 500. Se esperaba validación 422 y continuidad del directorio. `PerfilUpdate.datos_crudos` admite estructuras arbitrarias y `_perfil_publico` expande visibilidad como diccionario sin validar su tipo. Referencias: `backend/app/schemas/perfil.py`, `backend/app/api/routes/perfiles.py:123–130`. Se restauró únicamente ese perfil ficticio y el directorio volvió a **200**. Impacto: denegación de disponibilidad del listado mediante una cuenta autenticada ordinaria.

### QA-02 — ALTO: contraseñas vacías y equivalencia por truncamiento bcrypt

Casos C15/C17. Registrar una cuenta con contraseña vacía devuelve **200**, en vez de rechazarla. Para otra cuenta, registrar una cadena ASCII con prefijo de 72 bytes y sufijo A; iniciar sesión con el mismo prefijo y otro sufijo B devuelve **200**. Se esperaba rechazo explícito de contraseñas fuera del contrato o verificación de todos los bytes. `UsuarioRegistro.password` es `str` sin límites y el contexto bcrypt utiliza el comportamiento de truncamiento de passlib/bcrypt instalados. Referencias: `backend/app/schemas/usuario.py`, `backend/app/api/routes/auth.py`. No se probaron contraseñas reales ni se demuestra acceso arbitrario a otras cuentas: la colisión requiere conocer el prefijo correspondiente. La ausencia de política mínima también permite cuentas triviales.

### QA-03 — ALTO: caída de Ollama produce 500 tras guardar y duplica proyectos al reintentar

Casos F01/F03/F05/F06/F08 y G-INTERPRET-STATE. Usar el backend QA secundario con host Ollama inaccesible, sin apagar el servidor compartido. Confirmar perfil/proyecto o crear proyecto con requisitos revisados devuelve **500**. Las confirmaciones ya quedaron guardadas como `pendiente_embedding`; dos POST de creación idénticos devolvieron `[500,500]` y dejaron **dos proyectos**. Interpretar un perfil también devuelve 500 y deja `interpretando`; el adaptador deja de usar su estructura anterior confirmada.

Se esperaba confirmación persistida con estado recuperable y respuesta útil, o error 503 de interpretación con estado que permita reintento. Traza real: rutas → integration.py → embeddings.py → ollama_client.py → SDK `ollama/_client.py:149` → **ConnectionError incorporado**, no capturado por las excepciones actuales. El wrapper sí traduce el ConnectTimeout de un ensayo corto (F07); ese éxito no cubre el ConnectionError observado en rutas normales. Los reintentos F02/F04 e I11, con Ollama disponible, sí recuperaron Nomic y `listo`. Evidencia adicional: precondición del evento 28 quedó pendiente, sin vector, y React lo recuperó mediante su botón existente. Hace falta arreglar la clasificación de errores/estado y el resultado HTTP antes de fiarse del reintento de publicación.

### QA-04 — ALTO: roles con habilidades no textuales se guardan y rompen React

Casos E16/I15. Crear un proyecto revisado con un rol cuya propiedad sea `"habilidades":[{"unexpected":"object"}]`. La API devuelve **201** y guarda el evento QA 27. Abrir el proyecto en React produce ErrorBoundary y consola: `Objects are not valid as a React child (found: object with keys {unexpected})`. Se esperaba 422, sin persistir un contrato incompatible. El validador de roles no valida cada habilidad como texto; el frontend recibe y renderiza esos datos. No se ha demostrado que rompa toda la plataforma, sí la pantalla del proyecto abierto. Captura: [rol_malformado_error_react.png](../evidencias/2026-10-25-auditoria/rol_malformado_error_react.png).

### QA-05 — ALTO: IA omite un requisito obligatorio y etiquetas confirmadas pierden valor para matching

Casos E05, G-RAW-D06, G-RAW-D09 y G-SQL-CON. Con «Figma es obligatorio», Llama devolvió lista obligatoria vacía y trasladó Figma a restricciones. Con experiencia explícita en Blender/UE5 y UX/UI/Figma devolvió frases completas; al confirmarlas sin cambios y pasarlas por el adaptador ORM, Blender/Figma se evaluaron como **unknown**. `programar con SQL` tampoco tiene equivalencia SQL; D03 se salva porque trae además una etiqueta SQL independiente. Se esperaba conservar el requisito obligatorio y herramientas atómicas/equivalencias justificadas. La pantalla de revisión permite corregirlo, pero un usuario que confirma una salida aparentemente razonable pierde evidencia útil. No se recomienda ampliar arquitectura: ajustar extracción y normalización verificable manteniendo revisión humana.

### QA-06 — MEDIO: recomendaciones/pantalla anuncian disponibilidad sin vacante utilizable

Casos G16/I03. Proyecto QA G_occupied: único rol Backend ya ocupado, aún hay capacidad global. Candidatos devuelve recomendaciones y la tarjeta de Inicio muestra **Disponible**; solicitar/invitar para ese rol da **409** correctamente. `eligible` del núcleo es elegibilidad de evidencias y no autorización de acción, pero el producto lo traduce como disponibilidad. Se esperaba filtrar la vacante imposible o explicar que no hay acción disponible. No hay sobrecupo ni elusión de autorización. Captura: [recomendacion_sin_vacante.png](../evidencias/2026-10-25-auditoria/recomendacion_sin_vacante.png).

### QA-07 — MEDIO: cobertura del equipo da tranquilidad falsa con 0/0

Caso I08. Crear por el asistente React un proyecto con requisitos globales Python/SQL. Los roles generados tienen `habilidades:[]` (`CreateProjectPage.jsx:193`); `TeamCoverageChart` calcula únicamente desde habilidades de roles y muestra **0/0**, «¡Ninguna! Tu equipo cubre todo lo necesario». La ausencia de mapeo no demuestra cobertura total; se esperaba cobertura según requisitos confirmados o estado desconocido. Captura: [equipo_cobertura_cero.png](../evidencias/2026-10-25-auditoria/equipo_cobertura_cero.png).

### QA-08 — MEDIO: horarios/intereses en común comparados con usuario mock

Caso I17. El organizador QA tiene disponibilidad confirmada vacía. Abrir perfil ajeno con lun-tarde/sab-manana muestra ambos **en común**. `components/profile/PublicProfile.jsx` importa `currentUser` de mockData; `RecommendationCard.jsx` conserva el mismo patrón por lectura estática. Solo PublicProfile se verificó visualmente. Se esperaba comparar con el usuario autenticado real o no declarar coincidencias. Captura: [comparacion_horarios_mock.png](../evidencias/2026-10-25-auditoria/comparacion_horarios_mock.png).

### QA-09 — MEDIO: revisión obsoleta aceptada si se omite la huella de fuente

Casos E14/E15. Obtener fuente/requisitos antiguos, editar de SQL a Figma y confirmar la revisión antigua. Con `fuente_revision` antigua explícita devuelve **409**; sin esa propiedad devuelve **200** y confirma SQL contra la descripción nueva. La huella opcional mantiene compatibilidad heredada documentada, pero deja una ventana de datos obsoletos para esos clientes. Se esperaba vincular toda confirmación al texto revisado o declarar de forma explícita ese riesgo de contrato. El recorrido React normal envía revisión y reconfirmó correctamente. No es una omisión de permisos.

### QA-10 — MEDIO: privacidad por campo no cubre lo repetido en biografía pública

Caso C20. Confirmar fortalezas/intereses ocultos pero resumen público «Domino Python y SQL»; el perfil público conserva ese texto. Las listas se ocultan, la biografía queda pública por diseño. No se debe presentar como acceso indebido inequívoco: el campo se llama resumen público y pudo haber sido confirmado conscientemente. Sí existe una expectativa ambigua si la UI promete ocultar esas capacidades con los interruptores. Se esperaba una explicación clara o revisión de duplicados sensibles antes de publicar.

### QA-11 — MEDIO: no hay traducción suficiente entre bloques de disponibilidad y restricciones exactas

Caso G18. Perfil `lun-tarde` frente a condiciones lunes/16:00/18:00: todas **unknown**. La prueba de compatibilidad falló, pero es una decisión conservadora correcta frente a la falta de hora exacta: no se probó una falsa elegibilidad. Limitación de datos/UX: el usuario ve horario declarado que el motor no puede certificar. No se recomienda inferir que toda la tarde garantiza esa franja.

### QA-12 — MEDIO: búsqueda por habilidad prometida pero no implementada en q

Caso I-SEARCH-API. En QA existen ocho perfiles con Python; `GET /perfil/estudiantes/?q=Python&limit=200` devuelve **200 y cero resultados**. La búsqueda textual solo aplica a nombre/carrera (`perfiles.py:171`), mientras el buscador ofrece nombre o habilidad. Se esperaba búsqueda coherente con ese texto o una etiqueta de alcance correcta. Prueba HTTP y revisión estática, sin afirmar un clic visual en ese buscador.

### QA-13 — MEDIO: validación de longitudes no coincide con MySQL estricto

Caso C16. Registrar `nombre` de 151 caracteres devuelve **500**, frente a `VARCHAR(150)`. Se esperaba 422 y ninguna cuenta parcial. Las longitudes del contrato de registro no están acotadas. Se comprobó nombre; no se ejecutó una matriz de todos los campos.

### QA-14 — MEDIO: negaciones y estados sin evidencia mezclados con aprendizaje/fallo recuperable

Casos D04/D08/D10 y D-PERSIST-10/11. «No sé Python» se transforma en objetivo de mejora sin pedir aprenderlo; «No tengo experiencia profesional» aparece en experiencia. Perfiles vacíos/ambiguos confirmados quedan `pendiente_embedding` por falta de contenido útil, el mismo estado usado para fallo temporal de servicio. No hubo promoción de Docker/UE5 negados a fortaleza en D12; el defecto observado es de significado/estado y revisión humana. Se esperaba separar ausencia de contenido de error reintentable y respetar intención de aprendizaje.

### QA-15 — MEDIO: cuatro intentos Llama sin resultado dentro de 60 segundos

E06, E07, E10 y repetición E10-R terminaron por timeout de aproximadamente 60 s cada uno. Ninguno se marca aprobado. No prueba un fallo permanente del modelo ni una causa concreta; sí que análisis de datos, habilidades opcionales y Python no obligatorio quedaron bloqueados en esta ejecución. Se pudo completar la publicación con revisión manual y embeddings Nomic reales. Los otros 22 intentos del lote tardaron aproximadamente 0.87–4.30 s.

### QA-16 — BAJO: adhesión aceptada muestra mensaje dirigido a la persona equivocada

Caso I14. El creador acepta desde React al solicitante, el equipo persiste correctamente, pero el toast dice «¡Te uniste a QA E03!». Se esperaba «Solicitud aceptada»/«Se incorporó el solicitante». `InvitationsPage.jsx:30` reutiliza el mensaje de invitación.

### QA-17 — MEDIO: pantalla de reuniones aparenta envío sin persistencia

Caso I18. Abrir `/meeting`, proponer horario y enviar: toast «Propuesta enviada al equipo», seguido de navegación a `/equipos/t1` y error al cargar ese equipo ficticio. `MeetingPage.jsx:24–25` solo muestra toast/navega; no hay operación de guardado ni endpoint/modelo correspondiente. Se esperaba marcar la pantalla como demostración o no presentar un envío exitoso. Está fuera del cierre IA solicitado; se documenta el engaño observado, sin proponer desarrollar reuniones ni ampliar el alcance. Captura: [reunion_exito_aparente.png](../evidencias/2026-10-25-auditoria/reunion_exito_aparente.png).

## 6. Seguridad y controles que sí respondieron

Registro válido, correo duplicado y obligatorios ausentes respondieron conforme al contrato; contraseña incorrecta y tokens ausente/inválido/caducado recibieron 401. Token válido funcionó. Perfil privado ajeno y modificación ajena dieron 403, creador falsificado 403, edición ajena 403 y candidatos por no organizador 403. Cuenta inactiva rechazó tanto login como token emitido anteriormente. Perfil pausado no se descubre, sin consentimiento no recibe recomendaciones, y equipos/invitaciones/notificaciones ajenos dieron 403.

Las respuestas públicas ensayadas no incluyen contraseñas, hashes, tokens ni embeddings; las explicaciones de recomendación no exponen score interno. Confirmar objetivos Docker no dio crédito como habilidad Docker. Dos payloads HTML de nombre/biografía se mostraron escapados en React y no abrieron diálogos JavaScript (I16); esto no certifica inmunidad XSS de toda la aplicación. La aceptación de almacenamiento por sí sola (C29) tampoco se contó como prueba de escape visual.

## 7. Evaluación de perfiles y Llama real

Se ejecutaron los doce escenarios solicitados. Los textos y salidas JSON completas, ficticios, están en `qa_evidencia_20261025/datos_auditoria.json` → `llama_raw`; la revisión de calidad es `llama_quality_review`. La comprobación inicial por subcadenas solo detectaba dos defectos; la revisión manual agregó frases no normalizadas, negaciones en campos impropios y restricciones mal clasificadas. No se presenta validez Pydantic como calidad semántica.

| Caso | Entrada ficticia | Tiempo | Evaluación | Observación |
| --- | --- | --- | --- | --- |
| D01 | Sé Python y SQL. Tengo experiencia creando consultas y APIs. | 4.30 s | PASS | Python y SQL explícitos, sin invenciones relevantes. |
| D02 | Sé programar en Python. | 0.97 s | PASS | «Sé programar en Python» normalizado a Python. |
| D03 | Sé programar con SQL y crear consultas. | 1.16 s | FAIL | SQL aparece junto con «programar con SQL» y «crear consultas»; duplicación semántica y etiqueta sin equivalencia canónica. |
| D04 | No sé Python. Domino SQL. | 1.03 s | FAIL | Python no se acredita como fortaleza, pero se inventa como área de mejora sin expresar intención de aprenderlo. |
| D05 | Quiero aprender Docker. Mi habilidad actual es SQL. | 0.93 s | PASS | SQL como habilidad; Docker solo como aprendizaje. |
| D06 | Tengo experiencia en Blender y Unreal Engine 5. He modelado escenarios 3D. | 1.86 s | FAIL | Blender/UE5 quedan dentro de frases «Experiencia en…»; confirmarlas sin corregir no acredita Blender en el motor real. |
| D07 | Me gustan los videojuegos y los juegos de estrategia; no afirmo tener habilidades de programación. | 1.02 s | PASS | Videojuegos como interés, sin habilidades técnicas inventadas. |
| D08 | Juego fútbol como portero y defensa en torneos amateurs. No tengo experiencia profesional. | 1.45 s | FAIL | Portero/defensa quedan agrupados en una frase y «No tengo experiencia profesional» se guarda dentro de experiencia. |
| D09 | Diseño interfaces UX/UI en Figma y he realizado prototipos para una app. | 1.72 s | FAIL | Figma aparece dentro de una frase de UX/UI; confirmarla sin corregir deja Figma como requisito desconocido. |
| D10 | No tengo experiencia laboral ni profesional. Quiero aprender diseño. | 1.49 s | FAIL | Omite el objetivo diseño y añade experiencia laboral/profesional como áreas de mejora; experiencia incluye una negación. |
| D11 | Me gustaría hacer algo interesante con otras personas, todavía no sé qué aportar. | 1.07 s | PASS | Texto ambiguo: no inventa capacidades concretas. |
| D12 | Sé Python y SQL. He creado un panel de datos y limpiado encuestas. Me interesa la visualización y el diseño accesible. No sé Docker ni Unreal Engine 5. Quiero mejorar estadística y aprender Docker. Puedo trabajar los sábados. Prefiero colaborar con personas de otras carreras. | 1.74 s | PASS | Conserva Python/SQL, intereses y aprendizaje; no convierte Docker/UE5 negados en habilidades. |

Se confirmaron por HTTP doce perfiles corregidos humanamente y se comprobó su persistencia en MySQL y revisión de fuente. Diez recibieron vectores reales finitos de 768 dimensiones; D10/D11 carecían de texto útil para vector y quedaron pendientes. Esa confirmación se hizo con expectativas humanas, no convirtiendo automáticamente en verdad todo lo extraído. Por separado, G-RAW-D03/06/09 sí confirmaron las etiquetas reales sin corregir para medir la incompatibilidad con matching. El recorrido visual I02 agregó otro perfil analizado, revisado y confirmado de principio a fin.

## 8. Proyectos: extracción, confirmación y edición

| Caso | Descripción ficticia | Tiempo | Evaluación | Observación |
| --- | --- | --- | --- | --- |
| E01 | Buscamos un desarrollador backend con Python obligatorio y SQL deseable para una aplicación web. | 1.45 s | FAIL | Python obligatorio y SQL deseable correctos; clasifica «aplicación web» como restricción explícita. |
| E02 | Buscamos programador de Unreal Engine 5 para crear un videojuego cooperativo. Git deseable. | 1.26 s | PASS | UE5 obligatorio, Git deseable y rol programador. |
| E03 | Necesitamos artista 3D con Blender para modelar un escenario. | 1.19 s | PASS | Blender y artista 3D correctamente identificados. |
| E04 | Equipo amateur busca portero. Entrenamos sábados en Monterrey. No exigimos experiencia profesional. | 0.87 s | PASS | Portero, sábados y Monterrey; sin exigir experiencia profesional. |
| E05 | Buscamos diseñador UX/UI. Figma es obligatorio para prototipar una app accesible. | 2.94 s | FAIL | Omite Figma de habilidades obligatorias y lo coloca como restricción. |
| E06 | Necesitamos analista de datos con SQL obligatorio y Python deseable para estudiar encuestas. | 60.01 s | BLOCKED | Timeout de Llama, sin JSON evaluable. |
| E07 | Buscamos desarrollador web. Python y SQL son opcionales, no son obligatorios. | 60.02 s | BLOCKED | Timeout de Llama, sin JSON evaluable. |
| E08 | Queremos hacer algo creativo juntos; todavía no hemos decidido herramientas ni roles. | 0.95 s | FAIL | Sin habilidades/roles inventados, pero restricciones contienen «herramientas» y «roles» sin condición real. |
| E09 | Necesitamos tutor con Python obligatorio. Reuniones los lunes de 16:00 a 18:00 en línea. | 1.18 s | PASS | Python, tutor y horario lunes 16:00–18:00 identificados. |
| E10 | Buscamos analista con SQL obligatorio. Python no es obligatorio. No exigimos Docker. | 60.01 s | BLOCKED | Timeout de Llama; no se puede aprobar el tratamiento de Python no obligatorio. |

Los diez proyectos pudieron publicarse con requisitos corregidos por una persona y Nomic/MySQL reales, incluidos los tres cuyo análisis inicial agotó el tiempo. No se marca por eso su extracción como aprobada. En las respuestas generadas, `titulo_normalizado` quedó vacío aunque se aportó título; la UI mantiene el original y no se observó pérdida del título guardado.

Edición de proyecto por HTTP y React: invalida requisitos confirmados, oculta la evidencia vieja, elimina vector y requiere revisión visible. Reconfirmación genera vector nuevo por endpoints existentes. La versión explícitamente obsoleta devuelve 409; la limitación del campo opcional figura en QA-09. No se observaron escrituras de miembros perdidas al editar el proyecto del recorrido visual.

Repeticiones limitadas para no saturar Llama:

| Repetición | Tiempo | Resultado observado |
| --- | --- | --- |
| D03-R | 1.32 s | SQL aparece junto con «programar con SQL» y «crear consultas»; duplicación semántica y etiqueta sin equivalencia canónica. |
| D04-R | 1.01 s | Python no se acredita como fortaleza, pero se inventa como área de mejora sin expresar intención de aprenderlo. |
| E01-R | 1.48 s | Python obligatorio y SQL deseable correctos; clasifica «aplicación web» como restricción explícita. |
| E10-R | 60.01 s | Timeout de Llama; no se puede aprobar el tratamiento de Python no obligatorio. |

D03, D04 y E01 repitieron los defectos semánticos indicados; E10 volvió a timeout. Cuatro repeticiones no constituyen una evaluación estadística de variabilidad.

## 9. Nomic, revisiones y estados

Las pruebas D/F y E/F verificaron 768 dimensiones, valores finitos, almacenamiento JSON nativo, estado listo, modelo y coincidencia de revisión del vector con la confirmación. Cambiar una revisión de fuente, dimensión, modelo o pipeline en fixtures QA hizo que el adaptador/motor descartara la señal semántica; el ranking siguió funcionando sin embeddings. El único vector de tres dimensiones presente al cierre fue introducido deliberadamente como fixture incompatible; no procede de Nomic. La evidencia distingue esos vectores artificiales de los reales.

Al cierre, el perfil del recorrido visual (usuario QA 24) y su proyecto (evento QA 28) están `listo`, con 768 dimensiones y revisión coincidente, modelo `nomic-embed-text`. El proyecto se editó, reconfirmó y recuperó mediante reintento real. No se detuvo Ollama para simular fallos: se utilizó solo el backend secundario con host inválido. La traza adicional del error se capturó con TestClient y MySQL reales; las respuestas HTTP 500 se reprodujeron también por TCP.

## 10. Matching: lógica frente a resultados

Política inspeccionada `2026-10-21.v1`: obligatorias 0.40, complementariedad 0.25, deseables 0.15, semántica 0.10 e intereses 0.10. Las señales ausentes no equivalen a cero ni se convierten en certeza. El orden prioriza elegibilidad y suficiencia de evidencia; el score interno no es probabilidad de éxito. `top_n` se aplica después del orden y el endpoint restringe 1–20.

Se comprobó por HTTP/ORM la explicación basada en Python confirmado, ausencia de crédito por interés o deseo de aprender, equivalencias Python/programar en Python y UE5/Unreal Engine 5, estabilidad de la misma instantánea y exclusiones de perfiles pausados/sin consentimiento, integrantes, pendientes, proyectos llenos y cerrados. La polaridad negativa explícita produjo `unmet_confirmed` en el motor puro; no se atribuye esa prueba a persistencia HTTP. La extracción de «No sé Python» no lo convirtió en fortaleza, pero tampoco representa por sí sola una negación estructurada persistida.

Complementariedad G19: con creador sin perfil confirmado dio desconocida, correctamente. Tras confirmar creador y miembros, G23 destacó SQL aportado para una necesidad vacante. El candidato siguió `needs_review` por falta de Python: la explicación no afirmó cubrir todos los requisitos. La omisión de una habilidad es desconocida, no incumplimiento confirmado. La limitación de normalización Blender/Figma y la etiqueta Disponible sin rol vacante se describen en QA-05/06; los horarios desconocidos en QA-11 se consideran conservadores, no falsos positivos de seguridad.

## 11. Invitaciones, adhesiones y transacciones MySQL

Se probaron invitación y adhesión válidas, aceptación/rechazo, segunda aceptación, envío duplicado, invitación/adhesión opuestas, intento de invitar a integrante, capacidad llena, rol único ocupado, dos vacantes para el mismo rol, respuesta como otra cuenta, edición del rol entre petición y aceptación, perfil pausado y cuenta inactiva antes de aceptar. Se consultaron filas reales de `solicitudes_equipo` y `participantes_evento`. Rechazos por reglas no añadieron miembros. Las membresías persisten tras login nuevo y recarga React; no se reinició el proceso del servidor para probarlo.

| Carrera real | Respuestas HTTP | Filas observadas | Resultado |
| --- | --- | --- | --- |
| H-RACE-last_slot | [200, 409] | {'http_statuses': [200, 409], 'members': [{'user': 3, 'role': 'Backend'}], 'pending': 1} | PASS |
| H-RACE-same_role | [409, 200] | {'http_statuses': [409, 200], 'members': [{'user': 5, 'role': 'Backend'}], 'pending': 1} | PASS |
| H-RACE-inverse_pair | [409, 200] | {'http_statuses': [409, 200], 'members': [], 'pending': 1} | PASS |

No se detectaron pares de membresía duplicados al cierre: **0**. La adhesión visual quedó en evento 3 para usuario QA 24 con rol **artista**, comprobando que se agregó al solicitante y no al creador. Esta muestra valida los intercalados ejecutados, no todas las carreras posibles ni una carga sostenida.

## 12. Frontend real y evidencias

Se usó navegador automatizado IAB con lectura del DOM/árbol accesible, interacción real y capturas, contra Vite QA. No se infieren clics a partir de código. Los recorridos ejercitaron registro→perfil→Llama→revisión→confirmación; crear→revisar→publicar; recomendaciones de proyecto/candidatos; invitar→cambiar de cuenta→aceptar→equipo; solicitar adhesión→recargar→aceptación por creador; editar→reconfirmar; reintentar embedding; protección sin token y fallos de renderizado.

| Caso visual | Resultado | Comprobación |
| --- | --- | --- |
| I01 | PASS | Registro visual redirige al alta de perfil en MySQL QA |
| I02 | PASS | Perfil: análisis Llama, revisión y confirmación con Nomic/MySQL reales |
| I03 | FAIL | Inicio marca Disponible un proyecto cuyo único rol ya está ocupado |
| I04 | PASS | Crear proyecto, interpretar con Llama, revisar y publicar con MySQL/Nomic |
| I05 | PASS | Organizador consulta candidatos y explicaciones reales |
| I06 | PASS | Invitación enviada desde React y candidato pendiente excluido |
| I07 | PASS | Aceptar invitación, ver equipo y recargar conserva dos integrantes |
| I08 | FAIL | Cobertura muestra 0/0 y ninguna habilidad faltante pese a requisitos Python/SQL |
| I09 | PASS | Acceso privado sin token redirige a login |
| I10 | PASS | Editar proyecto, ocultar IA anterior, corregir requisitos y reconfirmar con Nomic real |
| I11 | PASS | Reintento visual recupera embedding real tras precondición de conexión fallida |
| I12 | PASS | Solicitar adhesión y recargar mantiene estado pendiente |
| I13 | PASS | El creador acepta una adhesión desde React; se incorpora al solicitante |
| I14 | FAIL | Mensaje de aceptación de adhesión dice al creador que él se unió |
| I15 | FAIL | Un proyecto con habilidades de rol como objetos provoca error de renderizado |
| I16 | PASS | HTML almacenado en nombre y biografía se muestra escapado, sin diálogo de JavaScript |
| I17 | FAIL | Comparación de horarios usa usuario de demostración |
| I18 | FAIL | Reuniones anuncia Propuesta enviada sin persistencia y navega a equipo ficticio t1 |

Se inspeccionó consola: sin errores registrados durante los recorridos normales observados; el payload de rol produjo el error React citado. Se verificaron estados vacío/sin requisitos, revisión, pendiente y reintento, mensajes tras acciones y error de equipo inexistente. No se ensayó cada spinner ni cada error de red de todas las pantallas.

Capturas: [perfil confirmado](../evidencias/2026-10-25-auditoria/perfil_confirmado.png), [recomendación sin vacante](../evidencias/2026-10-25-auditoria/recomendacion_sin_vacante.png), [cobertura 0/0](../evidencias/2026-10-25-auditoria/equipo_cobertura_cero.png), [ErrorBoundary](../evidencias/2026-10-25-auditoria/rol_malformado_error_react.png), [horarios mock](../evidencias/2026-10-25-auditoria/comparacion_horarios_mock.png), [reunión aparente](../evidencias/2026-10-25-auditoria/reunion_exito_aparente.png).

mockData conserva constantes útiles (días/franjas) y datos de presentación de Landing/DesignSystem; eso no es por sí mismo un defecto de persistencia. Sí se verificó un uso incorrecto de currentUser en PublicProfile y un flujo ficticio de MeetingPage. RecommendationCard conserva comparación con currentUser por inspección estática, sin atribuirle una reproducción visual independiente.

## 13. Evidencia, persistencia y reproducción segura

[datos_auditoria.json](../evidencias/2026-10-25-auditoria/datos_auditoria.json) contiene resultados por identificador, respuestas HTTP filtradas, entradas/salidas Llama ficticias, tiempos, metadatos del esquema y trazas sin credenciales. No contiene tokens ni valores de la fila real del usuario. Los payloads visibles en capturas pertenecen a QA. Los scripts y resultados temporales permanecen en `backend/.venv/qa_audit_20261025/` (ignorados por Git). No se entregan como código de producción ni se configuran para ejecutarse en la principal.

Ejemplos de consultas de comprobación, **solo dentro de la base QA identificada**:

```sql
SELECT id_evento, id_usuario, rol
FROM participantes_evento WHERE id_evento IN (3, 19, 20, 28);
SELECT id_evento, COUNT(*) AS miembros
FROM participantes_evento GROUP BY id_evento;
SELECT id_evento, estado_ia, JSON_LENGTH(embedding_requisitos) AS dimensiones,
       requisitos_fuente_revision = embedding_fuente_revision AS revision_coincide
FROM eventos WHERE id_evento = 28;
SELECT usuario_id, perfil_estado_ia, JSON_LENGTH(embedding_perfil) AS dimensiones,
       perfil_fuente_revision = perfil_embedding_fuente_revision AS revision_coincide
FROM perfiles_usuarios WHERE usuario_id = 24;
```

Se dejó la base QA para reproducir hallazgos; no se borró. Algunas filas contienen deliberadamente estados/vectores incompatibles o datos malformados. No utilizar sus registros como datos reales. El perfil cuyo JSON rompía el directorio se restauró tras demostrar el problema. Los resultados iniciales de G19 se reevaluaron con la precondición de creador sin confirmar y se separaron de G23; F07 quedó aprobado solo para la traducción del ConnectTimeout efectivamente observada. No se ocultaron las limitaciones de esos ensayos.

| Tabla QA | Filas finales |
| --- | --- |
| usuarios | 23 |
| perfiles_usuarios | 23 |
| eventos | 33 |
| solicitudes_equipo | 18 |
| participantes_evento | 12 |

## 14. Qué fue real, qué fue controlado y siguiente encargo

MySQL real: creación QA/esquema, registro/login, confirmaciones, JSON, membresías, invitaciones, transacciones y carreras; todas las escrituras en QA. Ollama real: 26 intentos del lote Llama, dos análisis desde React y embeddings de perfiles/proyectos confirmados. React real: 18 comprobaciones visuales del cuadro anterior. Fallo de servicio: configuración aislada en un backend separado, no apagado del servidor compartido.

Controlado/sin modelo: fixtures G/H abren algunos proyectos por ORM después de crearlos por API para aislar reglas; vectores/revisiones incompatibles se introdujeron deliberadamente solo en QA; la negación estructurada y parte de las equivalencias se comprobaron en motor puro; pytest utiliza sus mocks/fixtures. No confundir esos ensayos con calidad generativa ni con una confirmación humana visual independiente para cada fixture.

Orden recomendado de correcciones (sin implementarlas en esta auditoría):

| Prioridad | Corrección acotada | Impacto | Dificultad |
| --- | --- | --- | --- |
| 1 | Validar JSON de perfil y listas de habilidades de roles; proteger serialización pública | ALTO: disponibilidad y contratos | Baja/media |
| 2 | Contrato de contraseñas/longitudes y tratamiento seguro de bcrypt | ALTO: autenticación y errores 500 | Media; considerar cuentas existentes |
| 3 | Capturar errores reales del SDK, estados recuperables y respuesta tras persistencia | ALTO: publicación/reintentos y duplicados | Media |
| 4 | Extracción atómica y normalización limitada Python/SQL/Blender/UE5/Figma; negaciones | ALTO: evidencia y requisitos | Media; repetir corpus real limitado |
| 5 | Revisión de fuente obligatoria o compatibilidad explícita segura | MEDIO: datos obsoletos | Baja/media |
| 6 | Disponibilidad accionable, cobertura desconocida y usuario real en comparación | MEDIO: confianza en la UI | Media |
| 7 | Alinear búsqueda, privacidad por campo y mensaje de adhesión | MEDIO/BAJO: contratos y mensajes | Baja/media |
| 8 | Marcar/ocultar envío ficticio de reuniones, sin construir la funcionalidad | MEDIO: éxito aparente | Baja |

Siguiente encargo sugerido, pequeño/mediano: **corregir exclusivamente validación de datos de perfil/roles y degradación ante ConnectionError de Ollama**, con regresiones que reproduzcan QA-01/03/04, sin cambiar arquitectura. Criterios: payload inválido→422; directorio y proyecto siguen renderizando; caída de Ollama conserva confirmación con estado recuperable y respuesta coherente; reintentar recupera Nomic sin crear una segunda publicación por un 500 engañoso. Ejecutar pytest/pip check/build/lint y repetir en una base QA nueva los recorridos afectados. Después abordar autenticación en un encargo separado que contemple los hashes existentes. No añadir reuniones, feedback ni microservicios.

## 15. Estado final Git y confirmación de alcance

No hubo cambios de código de producción, tests existentes, dependencias, configuración persistida ni rama. No se hicieron commits ni push. La revisión sigue en `568026a`, rama `feat/ai-matching`. `git diff --name-only` y `git diff --cached --name-only` vacíos. Archivos nuevos: informe y carpeta de evidencias. Los artefactos de build/entorno temporal permanecen ignorados.

Estado Git final verificado:

```text
?? docs/REPORTE_QA_REAL_2026-10-25.md
?? docs/qa_evidencia_20261025/
```

La base principal `softtek_formador_equipos` mantiene filas, checksums, esquema y revisión iniciales. **No se realizaron escrituras ni limpieza sobre ella.** Se conservaron los procesos preexistentes, comprobando al cierre los mismos PID en 8000/5173/3306/11434. Se cerró la pestaña temporal y se detuvieron únicamente los tres procesos creados para QA en 8011/8012/5174, después de verificar sus identificadores y comandos. La base QA y las evidencias permanecen disponibles. Las herramientas auxiliares QA no forman parte de una instalación o despliegue del producto.

## Anexo: catálogo de endpoints y permisos

Las rutas de negocio requieren Bearer y cuenta activa salvo registro/login; `/` es público. Swagger/OpenAPI son documentación, no operaciones de negocio.

| Método | Ruta | Permiso inspeccionado |
| --- | --- | --- |
| POST | /auth/registro | Público; crea su cuenta |
| POST | /auth/login | Público; credenciales y cuenta activa |
| GET | /auth/me | Sesión propia |
| POST | /perfil/interpretar | Propietario autenticado; analiza su perfil |
| POST | /perfil/confirmar | Propietario autenticado; revisión humana explícita |
| POST | /perfil/embedding/reintentar | Propietario; perfil confirmado |
| GET | /perfil/estudiantes/ | Cuenta activa; proyección pública/visible |
| GET | /perfil/publico/{usuario_id} | Cuenta activa; proyección pública y no pausada |
| GET | /perfil/{usuario_id} | Solo el propio usuario |
| PUT | /perfil/{usuario_id} | Solo el propio usuario |
| POST | /eventos/interpretar | Cuenta activa; análisis sin publicar |
| POST | /eventos/ | POST: creador autenticado; GET: abiertos/no borrador ajeno |
| GET | /eventos/ | POST: creador autenticado; GET: abiertos/no borrador ajeno |
| POST | /eventos/{id_evento}/confirmar | Solo creador, revisión humana |
| POST | /eventos/{id_evento}/embedding/reintentar | Solo creador; requisitos confirmados |
| GET | /eventos/{id_evento} | GET: visible/no borrador ajeno; PUT: solo creador |
| PUT | /eventos/{id_evento} | GET: visible/no borrador ajeno; PUT: solo creador |
| GET | /invitaciones/{id_usuario} | Solo el propio usuario |
| POST | /eventos/{id_evento}/solicitudes | Solicitante propio; capacidad/rol/estado/duplicados |
| POST | /invitaciones/ | Solo creador del evento; remitente propio y destino elegible |
| PATCH | /invitaciones/{id_solicitud} | Solo destinatario; revalida evento y persona al aceptar |
| GET | /equipos/{id_usuario} | Solo el propio usuario |
| GET | /notificaciones/{id_usuario} | Solo el propio usuario |
| GET | /recomendaciones/eventos/{id_evento}/candidatos | Solo creador/organizador |
| GET | /recomendaciones/usuarios/{id_usuario}/proyectos | Solo el propio usuario con consentimiento |
| GET | / | Público |

## Anexo: catálogo de comprobaciones dirigidas

Los detalles HTTP/SQL están en datos_auditoria.json bajo el mismo identificador. Los casos agrupados incluyen pasos y comprobaciones, no un inventario artificial de cada aserción.

| ID | Área | Estado | Expectativa comprobada |
| --- | --- | --- | --- |
| C01 | C | PASS | Registro válido con MySQL real |
| C02 | C | PASS | Correo duplicado |
| C03 | C | PASS | Registro sin campos obligatorios |
| C04 | C | PASS | Login con contraseña incorrecta |
| C05 | C | PASS | Login correcto |
| C06 | C | PASS | Token válido |
| C07 | C | PASS | Token ausente |
| C08 | C | PASS | Token inválido |
| C09 | C | PASS | Token caducado firmado por QA |
| C10 | C | PASS | Lectura de perfil ajeno privado |
| C11 | C | PASS | Modificación de perfil ajeno |
| C12 | C | PASS | Creador falsificado |
| C13 | C | PASS | Cuenta inactiva: token previamente emitido |
| C14 | C | PASS | Cuenta inactiva: login |
| C15 | C | FAIL | Registro rechaza contraseña vacía |
| C16 | C | FAIL | Registro limita longitud a lo admitido por MySQL |
| C17 | C | FAIL | Contraseñas diferentes después del byte 72 no autentican |
| D-PERSIST-01 | D/F | PASS | Corrección humana y persistencia D01 |
| D-PERSIST-02 | D/F | PASS | Corrección humana y persistencia D02 |
| D-PERSIST-03 | D/F | PASS | Corrección humana y persistencia D03 |
| D-PERSIST-04 | D/F | PASS | Corrección humana y persistencia D04 |
| D-PERSIST-05 | D/F | PASS | Corrección humana y persistencia D05 |
| D-PERSIST-06 | D/F | PASS | Corrección humana y persistencia D06 |
| D-PERSIST-07 | D/F | PASS | Corrección humana y persistencia D07 |
| D-PERSIST-08 | D/F | PASS | Corrección humana y persistencia D08 |
| D-PERSIST-09 | D/F | PASS | Corrección humana y persistencia D09 |
| D-PERSIST-10 | D/F | PASS | Corrección humana y persistencia D10 |
| D-PERSIST-11 | D/F | PASS | Corrección humana y persistencia D11 |
| D-PERSIST-12 | D/F | PASS | Corrección humana y persistencia D12 |
| C18 | C | PASS | Perfil público omite contraseñas, tokens, vectores y áreas privadas |
| C19 | C | PASS | Perfil pausado no se descubre públicamente |
| C20 | C | FAIL | Ocultar fortalezas también evita publicarlas en la biografía |
| C21 | C | PASS | Sin consentimiento no consulta recomendaciones propias |
| E-PERSIST-01 | E/F | PASS | Publicación humana E01 |
| E-PERSIST-02 | E/F | PASS | Publicación humana E02 |
| E-PERSIST-03 | E/F | PASS | Publicación humana E03 |
| E-PERSIST-04 | E/F | PASS | Publicación humana E04 |
| E-PERSIST-05 | E/F | PASS | Publicación humana E05 |
| E-PERSIST-06 | E/F | PASS | Publicación humana E06 |
| E-PERSIST-07 | E/F | PASS | Publicación humana E07 |
| E-PERSIST-08 | E/F | PASS | Publicación humana E08 |
| E-PERSIST-09 | E/F | PASS | Publicación humana E09 |
| E-PERSIST-10 | E/F | PASS | Publicación humana E10 |
| C22 | C | PASS | Edición de proyecto ajeno |
| C23 | C | PASS | Candidatos solo para organizador |
| C24 | C | PASS | Invitaciones ajenas no se leen |
| C25 | C | PASS | Equipos ajenos no se leen |
| C26 | C | PASS | Notificaciones ajenas no se leen |
| E11 | E | PASS | Editar proyecto propio |
| E12 | E | PASS | Edición invalida IA sin publicar requisitos anteriores |
| E13 | E | PASS | Reintento antes de reconfirmar |
| E14 | E | PASS | Rechazo de revisión obsoleta |
| F01 | F | FAIL | Fallo controlado de Ollama conserva confirmación |
| F02 | F | PASS | Reintento real recupera Nomic |
| F03 | F | FAIL | Perfil conserva datos si Nomic no responde |
| F04 | F | PASS | Perfil reintenta Nomic real |
| F05 | F | FAIL | Fallo controlado del parser guarda borrador |
| G01 | G | PASS | Matching real: permiso y proyección pública |
| G02 | G | PASS | Excluye perfil pausado y sin consentimiento |
| G03 | G | PASS | Habilidad confirmada respalda explicación |
| G04 | G | PASS | Interés sin habilidad no acredita Python |
| G05 | G | PASS | top_n fuera de rango |
| G06 | G | PASS | top_n limita resultados |
| G07 | G | PASS | Ranking determinista con la misma instantánea |
| G08 | G | PASS | Campos ocultos no se exponen como habilidades explícitas |
| G09 | G | PASS | Vector obsoleto descartado en adaptación ORM real |
| G10 | G | PASS | Vector Nomic de dimensión incompatible descartado |
| G11 | G | PASS | Matching opera sin embedding |
| G12 | G | PASS | Equivalencia Python/programar en Python en evidencia real |
| G13 | G | PASS | UE5 acredita Unreal Engine 5 |
| G14 | G | PASS | Negación confirmada conserva polaridad (motor puro) |
| H01 | H | PASS | Invitación válida |
| H02 | H | PASS | Invitación duplicada |
| H03 | H | PASS | Adhesión inversa duplicada |
| H04 | H | PASS | Responder como otra persona |
| H05 | H | PASS | Aceptación válida |
| H06 | H | PASS | Doble aceptación |
| H07 | H | PASS | Invitar integrante existente |
| H08 | H | PASS | Rol ocupado |
| H09 | H | PASS | Fila de integrante y solicitud aceptada reales |
| H10 | H | PASS | Solicitud válida |
| H11 | H | PASS | Creador acepta adhesión |
| H12 | H | PASS | Se incorpora al solicitante y no al creador |
| H13 | H | PASS | Rechazo válido |
| H14 | H | PASS | Rechazo no crea miembro |
| H_edited | H | PASS | Revalidación al aceptar: role |
| H_paused | H | PASS | Revalidación al aceptar: paused |
| H_inactive | H | PASS | Revalidación al aceptar: inactive |
| H-RACE-last_slot | H | PASS | Concurrencia InnoDB last_slot |
| H-RACE-same_role | H | PASS | Concurrencia InnoDB same_role |
| H-RACE-inverse_pair | H | PASS | Concurrencia InnoDB inverse_pair |
| H15 | H | PASS | Dos vacantes permiten dos miembros y rechazan un tercero |
| H16 | H | PASS | Equipo persiste al iniciar nueva sesión |
| G15 | G | PASS | Excluye integrante, invitación y adhesión pendientes |
| G_closed | G | PASS | Sin candidatos para proyecto cerrado |
| G_full | G | PASS | Sin candidatos para proyecto lleno |
| G16 | G | FAIL | Proyecto con único rol ocupado no propone otra persona para esa vacante |
| F06 | F | FAIL | Estado persistido después de fallos de conexión |
| F07 | F | PASS | Error real de conexión debe traducirse a OllamaServiceError |
| C27 | C | FAIL | JSON de perfil inválido no inutiliza el directorio global |
| C28 | C | PASS | Restauración del único perfil QA malformado recupera directorio |
| G-RAW-D03 | G | PASS | Etiquetas reales D03 acreditan SQL |
| G-RAW-D06 | G | FAIL | Etiquetas reales D06 acreditan Blender |
| G-RAW-D09 | G | FAIL | Etiquetas reales D09 acreditan Figma |
| G-SQL-CON | G | FAIL | programar con SQL y SQL tienen equivalencia explícita |
| G-INTERPRET-STATE | G | FAIL | Un fallo de interpretación no pierde toda la evidencia confirmada previa |
| E15 | E | FAIL | Revisión obsoleta sin huella no se confirma silenciosamente |
| G17 | G | PASS | Proyectos propios y con membresía/acción pendiente quedan fuera |
| G18 | G | FAIL | Horario declarado se interpreta como evidencia conocida compatible |
| E16 | E | FAIL | Habilidades por rol rechazan objetos no textuales |
| C29 | C | PASS | HTML se conserva como texto a verificar visualmente |
| G19 | G | PASS | Equipo con creador sin confirmar conserva complementariedad desconocida |
| G20 | G | PASS | Querer aprender Docker no acredita Docker |
| G21 | G | PASS | Modelos distintos no producen semejanza semántica comparable |
| G22 | G | PASS | Pipelines distintos no comparan vectores |
| C30 | C | PASS | Áreas privadas no se publican en proyección real |
| I-SEARCH-API | I-HTTP | FAIL | Búsqueda prometida por habilidad encuentra Python |
| G23 | G | PASS | Complementariedad con todos los integrantes y creador confirmados |
| I01 | I | PASS | Registro visual redirige al alta de perfil en MySQL QA |
| I02 | I | PASS | Perfil: análisis Llama, revisión y confirmación con Nomic/MySQL reales |
| I03 | I | FAIL | Inicio marca Disponible un proyecto cuyo único rol ya está ocupado |
| I04 | I | PASS | Crear proyecto, interpretar con Llama, revisar y publicar con MySQL/Nomic |
| I05 | I | PASS | Organizador consulta candidatos y explicaciones reales |
| I06 | I | PASS | Invitación enviada desde React y candidato pendiente excluido |
| I07 | I | PASS | Aceptar invitación, ver equipo y recargar conserva dos integrantes |
| I08 | I | FAIL | Cobertura muestra 0/0 y ninguna habilidad faltante pese a requisitos Python/SQL |
| I09 | I | PASS | Acceso privado sin token redirige a login |
| I10 | I | PASS | Editar proyecto, ocultar IA anterior, corregir requisitos y reconfirmar con Nomic real |
| I11 | I | PASS | Reintento visual recupera embedding real tras precondición de conexión fallida |
| I12 | I | PASS | Solicitar adhesión y recargar mantiene estado pendiente |
| I13 | I | PASS | El creador acepta una adhesión desde React; se incorpora al solicitante |
| I14 | I | FAIL | Mensaje de aceptación de adhesión dice al creador que él se unió |
| I15 | I | FAIL | Un proyecto con habilidades de rol como objetos provoca error de renderizado |
| I16 | I | PASS | HTML almacenado en nombre y biografía se muestra escapado, sin diálogo de JavaScript |
| I17 | I | FAIL | Comparación de horarios usa usuario de demostración |
| I18 | I | FAIL | Reuniones anuncia Propuesta enviada sin persistencia y navega a equipo ficticio t1 |
| F08 | F | FAIL | Creación con Ollama inaccesible no devuelve 500 después de persistir |