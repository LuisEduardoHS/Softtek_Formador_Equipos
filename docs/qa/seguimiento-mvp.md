# Seguimiento QA del MVP — 2026-10-25

**Actualización 2026-10-26:** **367 pytest + 27 pruebas frontend aprobadas**. El caso MANUAL01 vacío se explica por consentimiento desactivado en perfiles listos. Se añadieron avisos visibles, activación propia por un botón y elección explícita al confirmar; 29 comprobaciones reales QA aprobadas. Ver [diagnóstico de consentimiento](informes/2026-10-26-consentimiento-candidatos.md) y [escenarios amplios](informes/2026-10-26-escenarios-matching.md). Las rondas anteriores conservan sus resultados históricos.

Repositorio: `D:\projects\Softtek_Formador_Equipos`. Rama: `feat/ai-matching`. La primera ronda partió de `568026a` y después se integró en el commit local `2157a43`. La segunda ronda semántica parte de `2157a43`; sus resultados y límites se detallan al final. No se hicieron push, merges ni cambios de rama.

Se leyó el [informe integral](informes/2026-10-25-auditoria-real.md) y su [evidencia JSON](evidencias/2026-10-25-auditoria/datos_auditoria.json). Esta entrega implementa las correcciones de estabilidad, recuperación y autenticación solicitadas. No modifica arquitectura, framework, dependencias, esquema ni datos de la base principal. Conserva el diseño de Isaac y el motor de matching.

## Resultado por hallazgo

| ID | Estado | Corrección implementada |
| --- | --- | --- |
| QA-01 | Corregido | Validación de los campos JSON consumidos por React: visibilidad con claves conocidas y booleanos estrictos, fortalezas, listas de intereses/aprendizaje/experiencia/disponibilidad, semestre, biografía y opciones del perfil. Peticiones malformadas devuelven 422 antes de guardar. Proyección pública/privada defensiva para datos legados y privacidad inválida cerrada. Una estructura IA dañada se omite al leer, sin reescribirla. |
| QA-04 | Corregido | Habilidades de roles: listas de strings no vacíos, hasta 150 caracteres y 100 elementos; nombres de rol de 1–50, identificadores de 1–100, vacantes enteras 1–8 y bandera indispensable booleana. Requisitos estructurados y detalles usados por el frontend tienen límites/tipos. Datos legados se proyectan de forma segura en detalle, listados y equipos. El mapper React descarta objetos en habilidades y entradas de rol incompatibles. |
| QA-03 | Corregido | ConnectionError incorporado, TimeoutError, errores httpx y del SDK se traducen a errores controlados. Confirmar/crear conserva los datos y devuelve pendiente_embedding ante fallo del vector; interpretación fallida devuelve 503 y restaura el estado confirmado anterior. Se conservan los borradores y las rutas de reintento existentes. Publicación con Idempotency-Key recupera la misma fila y detecta un cuerpo distinto con 409. |
| QA-02 | Corregido con límite heredado explícito | Altas nuevas usan bcrypt_sha256 y verifican la contraseña completa. Se admiten Unicode y contraseñas largas sin colisión por el byte 72. Login conserva compatibilidad con bcrypt existente de hasta 72 bytes y migra el hash al verificar correctamente una cuenta activa. Un intento de más de 72 bytes contra bcrypt heredado se rechaza explícitamente; no se migra a partir de un prefijo ambiguo. |
| QA-13 | Corregido | Nombre 1–150, carrera 1–100, correo hasta 100, estado/municipio hasta 50 caracteres en registro; nombre/carrera también acotados en edición. La validación sucede antes de insertar, evitando el 500 de MySQL estricto por nombre de 151 caracteres. |
| QA-05 | Corregido en el corpus delimitado, ronda 2 | Catálogo compartido v3, etiquetas atómicas explícitas, SQL con y sin preposición, herramientas Blender/UE5/UX/UI/Figma y recuperación de requisitos obligatorios como Figma. No se cambia la política de ranking. |
| QA-14 | Corregido en los casos verificados, ronda 2 | Se separan negación, habilidad afirmada, interés y aprendizaje; ausencia de experiencia no es experiencia positiva ni meta automática. Perfil sin contenido semántico confirmado queda sin_contenido, distinto de una caída de Nomic. |
| QA-15 | Mitigado y medido, ronda 2 | Generación JSON limitada a 1024 tokens, instrucciones sin ejemplos de roles ajenos y sin repetir listas. Se registraron 22 llamadas reales, cero timeouts; no demuestra ausencia universal de timeouts ni fiabilidad del JSON crudo. |

Los fallos de validación no devuelven el contenido de entrada: evita reflejar contraseñas o texto privado y permite responder 422 ante Unicode inválido enviado como escapes JSON.

## Política de contraseñas y compatibilidad

- Registro: **8–128 caracteres Unicode**, sin NUL y sin cadenas compuestas exclusivamente por espacios. No se recorta ni normaliza la contraseña. No se exige un repertorio artificial de símbolos.
- Login: **1–128 caracteres**, para conservar contraseñas cortas preexistentes que sí eran válidas. El frontend permite ese acceso; el mínimo de ocho se aplica a altas nuevas.
- Hash nuevo: esquema passlib **bcrypt_sha256** en la columna existente de 255 caracteres. No se añadieron paquetes ni columnas.
- Hash bcrypt previo: se verifica y actualiza únicamente después de credenciales correctas y cuenta activa. Las contraseñas Unicode se evalúan según sus bytes UTF-8 para la limitación heredada.
- **Limitación inevitable de los hashes antiguos:** bcrypt no conservó la información posterior al byte 72. No se puede distinguir el sufijo original de otro sufijo a partir de ese hash. Se devuelve 422 con explicación y se requiere restablecimiento seguro para esos casos. No existe todavía un flujo real de restablecimiento en este MVP; el botón anterior no lo implementa. No se añadió uno en este encargo ni se modificó la cuenta principal. Esta restricción es explícita, no una migración silenciosa basada en una contraseña truncada.

## Recuperación y publicación repetida

La caída de Nomic ya no convierte una confirmación persistida en un error 500: perfil devuelve 200 y proyecto creado devuelve 201 con `pendiente_embedding`. Se puede seguir usando la evidencia confirmada y regenerar el vector mediante las rutas existentes. Un fallo de interpretación conserva el texto del borrador; si había una confirmación lista o pendiente de embedding, se mantiene su revisión/estructura. También se evita sobrescribir una confirmación que cambió durante el análisis.

React guarda una clave UUID junto con el borrador **antes** del POST de publicación. Repetir el mismo intento, incluso después de recargar, envía la misma clave; modificar el contenido genera otra. El backend vincula clave, creador autenticado y huella del cuerpo en el JSON existente. La clave se conserva al editar el proyecto y no se expone en los DTO públicos. No se añadieron tablas ni migraciones.

Los envíos concurrentes de un creador se serializan durante la comprobación/creación. Se descarta la instantánea inicial de autenticación para que MySQL REPEATABLE READ vea el proyecto recién confirmado por otro intento. La lectura de una repetición no bloquea el evento: conserva el orden de bloqueos usado por aceptación/invitaciones. Se comprobó una repetición mientras otra transacción mantenía bloqueado el evento; respondió 201 en 0.376 s.

Compatibilidad: clientes antiguos sin `Idempotency-Key` siguen funcionando y reciben el resultado recuperable del fallo de embedding. La garantía de recuperar la misma publicación ante pérdida de respuesta requiere enviar la clave; no se deduplican publicaciones intencionales solo porque tengan el mismo título o descripción. Las rutas existentes de reintento de embedding siguen siendo el mecanismo para completar el análisis de una publicación guardada.

## Archivos y motivos

| Archivos | Motivo |
| --- | --- |
| `backend/app/schemas/profile_data.py` (nuevo), `schemas/perfil.py` | Contratos de JSON del perfil y normalización defensiva de lectura. Preservan metadatos adicionales sin permitir formas inválidas en los campos consumidos. |
| `backend/app/schemas/ai_integration.py` | Booleanos estrictos y listas/niveles coherentes en la confirmación humana del perfil. |
| `backend/app/api/routes/perfiles.py` | Proyecciones resistentes a registros antiguos; conservación de confirmación tras fallo; protección frente a una confirmación concurrente durante análisis. |
| `backend/app/schemas/event_details.py` (nuevo), `schemas/evento.py` | Contratos de roles/detalles y proyecciones seguras de registros legados; metadatos internos de publicación reservados. |
| `backend/app/services/team_rules.py` | Validación efectiva de roles antes de guardar; mantiene las reglas de capacidad, unicidad y revalidación transaccional existentes. |
| `backend/app/api/routes/eventos.py` | Lectura segura de eventos e idempotencia por intento/creador, sin alterar las rutas de confirmación/reintento. |
| `backend/app/api/routes/solicitudes.py` | Proyección de equipo con perfil y roles legados seguros. Mantiene el destinatario/solicitante y las reglas de aceptación. |
| `backend/app/services/ai/ollama_client.py`, `services/ai/integration.py` | Traducción de fallos reales del SDK y degradación recuperable del embedding. Los detalles internos del error no se devuelven al usuario. |
| `backend/app/services/ai/schemas.py` | Límites y tipos de requisitos estructurados. No cambia prompts ni reglas de extracción. |
| `backend/app/services/ai/recommendations/orm_adapter.py` | Vacantes legadas inválidas quedan desconocidas, en lugar de provocar TypeError. No cambia pesos, ranking ni equivalencias del núcleo. |
| `backend/app/schemas/usuario.py`, `api/routes/auth.py` | Política de contraseña, compatibilidad/migración de hashes y longitudes alineadas con MySQL. |
| `backend/app/main.py` | Respuestas 422 sin eco de entradas privadas; evita 500 al serializar errores de Unicode inválido. |
| `frontend/src/components/auth/AuthCard.jsx` | Longitudes visibles, política de altas y login compatible con contraseñas cortas anteriores. |
| `frontend/src/pages/CreateProjectPage.jsx`, `frontend/src/services/api.js` | Persistencia de la clave del intento de publicación, envío del encabezado y defensas del mapper de roles. |
| `backend/tests/test_qa_stability_security.py` (nuevo) | Regresiones HTTP/ORM para los hallazgos y concurrencia de publicación. No se alteraron los tests existentes. |
| Este documento y `docs/qa/evidencias/2026-10-25-estabilidad/` | Seguimiento y evidencia filtrada de las ejecuciones reales. El informe original y sus evidencias se conservan intactos. |

## Regresiones y controles automáticos

Antes de modificar producción se ejecutó el primer lote de **57 casos nuevos contra el comportamiento anterior**: **51 fallaron y 6 pasaron**, en 19.14 s. Reprodujeron aceptación de formas inválidas, colisiones de contraseña, falta de migración, 500 de Ollama y longitudes no validadas. Después se agregaron seis casos para guardas adicionales: vacantes legadas, Unicode inválido, ámbito/conservación de clave, clave inválida, concurrencia y estructura IA legada. Son casos parametrizados, no 63 defectos distintos.

Resultado definitivo:

| Control | Resultado | Duración del proceso |
| --- | --- | --- |
| `python -m pytest -q` | **297 passed**: 234 anteriores + 63 regresiones | 37.07 s; pytest informa 34.99 s |
| `python -m pip check` | Sin dependencias rotas | 1.01 s |
| `npm run build` | Correcto, 1989 módulos | 2.03 s |
| `npm run lint` | 0 errores; 1 advertencia previa | 6.08 s |
| `git diff --check` | Sin errores de whitespace | Verificación final |

Advertencias conservadas: deprecación Starlette TestClient/httpx y dependencia `state` de useEffect en `RequireSession.jsx:29`. No se instalaron dependencias para ocultarlas ni se rebajaron aserciones. Pytest se ejecutó con URL SQLite y secreto de pruebas explícitos; las escrituras MySQL de verificación se hicieron exclusivamente en QA.

Cobertura nueva: dos usuarios HTTP y directorio tras peticiones malformadas; lectura sin reparación persistida de perfiles/estructuras dañadas; roles y requisitos incompatibles rechazados; SDK ConnectionError/TimeoutError/httpx en generación/JSON/embeddings; confirmación pendiente y recuperación; interpretación fallida con y sin confirmación; contraseñas largas ASCII/Unicode y sufijos distintos; bcrypt previo corto/Unicode/72 bytes; rechazo de bcrypt ambiguo sin cambiar hash; longitudes MySQL; clave por actor, conflicto de cuerpo, conservación tras editar y dos POST concurrentes.

## Smoke real MySQL/Ollama/React

Base nueva y vacía: **`softtek_formador_equipos_qa_fix_20261025_29e772`**, con DDL de las cinco tablas principales y revisión Alembic `20261022_6a`. No se copiaron registros de usuarios. Se mantuvo InnoDB, MySQL 8.0.46 y REPEATABLE READ. Se usaron las dependencias instaladas y los modelos locales `llama3.1:8b` y `nomic-embed-text` del informe original.

**63 comprobaciones reales aprobadas**: lote principal 51, comprobaciones de la versión final de idempotencia 5 y cierre 7. Algunas verifican distintos pasos del mismo recorrido; no representan 63 errores independientes. Se conservaron respuestas/estados SQL filtrados en [resultados.json](evidencias/2026-10-25-estabilidad/resultados.json).

- Registro, políticas de contraseña y longitudes: 422 sin insertar; ASCII/Unicode largos autentican solo con la clave completa; cuenta bcrypt previa migra al verificar; sufijo ambiguo heredado da 422 sin tocar su hash.
- Perfil propio malformado: 422; otro usuario sigue consultando el directorio con 200. Perfil y estructura IA legados dañados se leen sin 500 ni corrección persistida automática; privacidad inválida no publica correo/campos.
- Rol con objeto en habilidades: 422 y conteo de eventos **0 → 0**. Datos legados con vacantes incompatibles no rompen detalle/equipos/recomendaciones.
- Backend separado con Ollama apuntando a `127.0.0.1:9`: interpretación 503; perfil confirmado 200 pendiente; proyecto creado/confirmado recuperable. No se apagó Ollama compartido.
- Dos POST idénticos con la misma clave devolvieron **[201,201]**, mismo ID y **una fila**. Dos peticiones concurrentes hicieron lo mismo. Un cuerpo distinto con la misma clave devolvió 409. Se volvió a comprobar la concurrencia contra la versión final del código.
- Reintentos existentes recuperaron embeddings **reales, finitos y de 768 dimensiones**, con revisión de fuente coincidente y estado listo.
- Recomendaciones con Python confirmado, exclusión de invitación pendiente, permisos ajenos 403, invitación, rechazo de duplicado, aceptación, adhesión y filas de participantes correctas. Doble aceptación devuelve 409; el equipo persiste.
- Dos llamadas Llama instrumentadas: perfil **16.397 s**, proyecto **4.182 s**, ambas HTTP 200. Una tercera interpretación se ejecutó desde el asistente React; no se instrumentó su duración. No se repitió el corpus completo de calidad de IA porque este encargo corrige estabilidad/seguridad.

Cuatro recorridos visuales adicionales en navegador IAB contra Vite 5174 y FastAPI QA 8011: login; detalle legado con candidatos; directorio/perfil legado con privacidad cerrada; publicación desde React y recarga del proyecto. **Cero errores de consola capturados**. La publicación visual quedó en evento QA **5**, una fila, clave del intento y huella persistidas, vector de 768 y estado listo. La recarga conservó el resultado.

Capturas: [detalle legado protegido](evidencias/2026-10-25-estabilidad/detalle_legado_protegido.png), [directorio protegido](evidencias/2026-10-25-estabilidad/directorio_perfil_legado.png), [publicación confirmada](evidencias/2026-10-25-estabilidad/publicacion_react_confirmada.png), [proyecto listo tras recargar](evidencias/2026-10-25-estabilidad/proyecto_persistido_listo.png).

Al cierre QA conserva únicamente datos ficticios: 6 usuarios, 6 perfiles, 5 eventos, 2 solicitudes y 2 participantes. Los scripts temporales siguen en `backend/.venv/qa_fix_20261025/`, ignorados por Git. No se borró la base QA. Se cerró la pestaña y se detuvieron exclusivamente los procesos QA creados en 8011/8012/5174; los procesos anteriores de 8000/5173/3306/11434 conservaron sus PID.

## Base principal y alcance de escrituras

**La base principal no fue modificada.** Se usaron únicamente SELECT, SHOW e inspecciones/checksum sobre ella. No se ejecutó migración, stamp, downgrade, limpieza ni restablecimiento. Conteos, checksums, DDL y revisión coinciden antes y después:

| Tabla principal | Filas antes/después | Checksum antes/después |
| --- | --- | --- |
| usuarios | 1 / 1 | 101962764 / 101962764 |
| perfiles_usuarios | 1 / 1 | 2746401420 / 2746401420 |
| eventos | 0 / 0 | 0 / 0 |
| solicitudes_equipo | 0 / 0 | 0 / 0 |
| participantes_evento | 0 / 0 | 0 / 0 |

Huella DDL SHA-256: `000c70b44ca454ac24551c35ee36780ad1d729221e175bdbb51f581cd9fa8dbe`; Alembic `20261022_6a`. La migración de hashes se comprobó en cuentas ficticias QA; la cuenta real no se utilizó para login ni se modificó. No se guardaron credenciales, tokens o URL privadas en las evidencias.

## Pendientes y límites

1. Restablecimiento seguro de contraseñas bcrypt históricas ambiguas de más de 72 bytes; no es posible recuperar el sufijo original del hash. No se creó un flujo nuevo en este encargo.
2. Fuera de los casos cubiertos en ronda 2, siguen pendientes evaluación amplia de calidad/latencia, vocabulario no catalogado y construcciones complejas. Llama todavía puede producir datos crudos incorrectos; la revisión humana sigue siendo obligatoria. No se declara calidad universal por pasar un corpus limitado.
3. QA-06/07/08: disponibilidad accionable por rol, cobertura 0/0 y comparaciones con currentUser de demostración.
4. QA-09/10/11/12/16/17: huella opcional en clientes heredados, expectativas de privacidad de biografía, contrato de horarios, búsqueda por habilidad, mensaje de adhesión y reunión ficticia. No se añadieron reuniones ni otras funcionalidades.
5. No se ejecutó carga sostenida, prueba de todas las carreras posibles, migración desde cero, ni auditoría de seguridad exhaustiva. No se inyectó pérdida de respuesta en el navegador: las repeticiones y su concurrencia se verificaron mediante HTTP/MySQL, y la clave emitida por React se verificó en la fila persistida. Se verificaron los recorridos documentados; las advertencias previas de herramientas siguen visibles.

La primera ronda se entregó inicialmente sin commit y después quedó en `2157a43`. El informe integral previo y sus evidencias se conservaron. No hubo push ni merges.

Los servidores habituales no se reiniciaron; para ejecutar el código actualizado en esos procesos debe aplicarse su recarga/reinicio normal. La comprobación de esta entrega se hizo en procesos QA separados, ya detenidos.

## Segunda ronda — precisión semántica, QA-05/14/15

### Cambios acotados

- `services/ai/skill_catalog.py` define **8 conceptos y 62 alias finitos**, versión **2026-10-25.v3**: Python, SQL, Blender, Unreal Engine 5, UX/UI, Figma, Docker y Git. Incluye UE5 y prefijos afirmativos específicos como experiencia en/con y programar en/con. Extracción, confirmación y matching usan el mismo catálogo. No se añadieron equivalencias por embeddings, distancia de texto o afinidad temática.
- `skill_terms.py` clasifica menciones como afirmadas, negadas, objetivos, intereses, menciones inciertas, objetivos negados e intereses negados. Negar interés o aprendizaje no borra una habilidad afirmada en otra frase. Las contradicciones sobre competencia se tratan de forma conservadora. Las negaciones originales permanecen en el texto del borrador; **no se transforman automáticamente en una declaración negativa confirmada ni se publican como nueva evidencia**. El matching sigue reservando la polaridad negativa a evidencia explícitamente confirmada de su contrato existente.
- `profile_parser.py` exige apoyo literal de la fuente, recupera herramientas explícitas del catálogo, elimina experiencia negativa y no conserva un resumen que repita hechos descartados. Las metas se recuperan solo de intención de aprender/mejorar expresada. El prefijo aprender se elimina para deduplicar **dentro de metas**, nunca para convertir una meta en habilidad. La experiencia no combina herramientas y acciones de frases distintas si esa relación no está expresada: conserva las frases positivas originales como alternativa.
- `event_parser.py` recupera Figma/Python/SQL y otras herramientas catalogadas solo con requisitos explícitos; separa obligatorias y opcionales coordinadas. Descarta temas, herramientas sueltas, campos internos y placeholders usados como restricciones. Recupera algunos roles literalmente pedidos, sin inferir una profesión a partir de una tecnología. Conserva los contratos anteriores de programador Python/UE5, artista Blender y portero.
- `schemas/ai_integration.py` fusiona alias duplicados en la revisión humana. Si la misma habilidad aparece con dos niveles incompatibles, devuelve **422** para que la persona resuelva el conflicto. No elige un nivel por inferencia.
- `integration.py`, `routes/perfiles.py`, `recommendations/orm_adapter.py` y `AIStatus.jsx` distinguen **sin_contenido** de **pendiente_embedding**. Un perfil confirmado con solo metas o sin hechos útiles no llama a Nomic ni ofrece un reintento inútil; mantiene sus datos confirmados. Añadir contenido y reconfirmar permite generar el vector. Una caída temporal con contenido sigue siendo reintentable y una interpretación fallida conserva también el estado sin_contenido previo.
- `ollama_client.py` conserva temperatura 0 y añade **num_predict=1024** a la generación estructurada. Los analizadores mantienen timeout de 60 s. No se añaden reintentos automáticos ilimitados ni se sustituyen errores de formato por resultados supuestamente correctos.

No se tocaron pesos, elegibilidad, desempates ni scoring del motor. Los módulos de autenticación, creación idempotente y reglas transaccionales de equipos de la primera ronda permanecen preservados. No hubo cambios de esquema, modelos generativos, dependencias, framework o infraestructura.

### Reproducción y regresiones

El primer lote semántico, antes de estas correcciones, produjo **19 fallos y 1 aprobado**. Se añadieron regresiones con las salidas reales observadas durante esta ronda: meta aprender diseño duplicada, restricciones Figma mal clasificadas, tecnología opcional como restricción, placeholder de ausencia de condiciones, relación inventada entre experiencias y omisión de rol literal. También se verificaron duplicados/niveles humanos y negación de interés separada de negación de competencia.

Archivos permanentes: `backend/tests/test_semantic_quality.py` (**34 casos nuevos**) y `backend/tests/semantic_corpus.py` (datos ficticios del corpus, sin llamadas automáticas a modelos durante pytest). Se ajustaron tres pruebas existentes sin reducir sus comprobaciones funcionales: versión esperada del catálogo; presupuesto de generación; y redacción del prompt sin portero ajeno al texto. El fixture antiguo de C++ ahora lo declara explícitamente en la fuente; una regresión adicional comprueba que C++ desaparece cuando no está declarado. El test de portero mantiene sus tres salidas inconsistentes y la misma exigencia funcional.

Resultado final automático:

| Control | Resultado | Duración del proceso |
| --- | --- | --- |
| python -m pytest -q | **331 aprobadas**: 297 anteriores + 34 nuevas | 26.14 s; pytest 25.07 s |
| python -m pip check | Sin dependencias rotas | 0.50 s |
| npm run build | Correcto | 1.00 s |
| npm run lint | 0 errores; advertencia previa de RequireSession.jsx | 3.42 s |

Se mantiene la advertencia de deprecación de Starlette/httpx. No se debilitaron tests para forzar aprobación; la comprobación completa detectó una regresión de recuperación del programador Python/UE5 y se corrigió conservando las aserciones originales.

### Corpus real y errores observados

Se usó exclusivamente **llama3.1:8b** instalado, sin cambiar el modelo. Hubo **22 llamadas secuenciales**: 10 perfiles + 6 proyectos + 2 repeticiones, 3 comprobaciones focalizadas y una última comprobación de opcionales. Se conservaron todas las salidas crudas y duraciones en [resultados semánticos](evidencias/2026-10-25-semantica/resultados.json).

**Las 22 devolvieron JSON válido y ninguna agotó 60 s**, pero no todas fueron semánticamente correctas en la versión ejecutada en ese momento:

- Primera fase: detector inicial **14 PASS / 4 FAIL**. Fallaron P05 (aprender diseño/diseño duplicados), E02 y su repetición (Figma como restricción), E04 (opcionales como restricciones). La revisión también identificó E05 como texto ambiguo convertido en restricción, E03 con rol analista omitido y P02 con una relación entre acciones/herramientas no explicitada en una misma frase. Se agregaron controles para estas observaciones; no se presenta el detector inicial como una evaluación exhaustiva.
- Llama propuso portero en proyectos Figma/web y llegó a repetir accesible en Figma cerca de cien veces. Los filtros retiraron los roles ajenos al texto. Se eliminó del prompt el ejemplo de portero y se conservó la recuperación literal del caso deportivo.
- En las tres llamadas focalizadas, **2 PASS / 1 FAIL**: Figma obligatorio y diseño quedaron correctos; E04 todavía contenía condiciones de participación no especificadas. Ese fallo se conservó y originó otra regresión. La última llamada nueva de E04, tras corregir el apoyo de palabras significativas, fue **PASS**.
- Incluso la salida cruda fresca de Figma inventó frases de lugar/horario sin datos. La extracción final las descarta porque no están respaldadas por la fuente; esto **no significa que Llama haya dejado de inventarlas**.

Duraciones reales: **0.952–21.306 s**, mediana **1.298 s**. P01 tardó 21.306 s en la primera llamada; E02 inicial/repetición 17.749/17.676 s, comprobación focalizada 4.740 s. No se atribuye causalidad ni una garantía de latencia a esta muestra. El presupuesto de tokens puede producir JSON incompleto en otros textos; ese error seguiría siendo un fallo de formato, distinto de timeout o defecto semántico.

Con la versión final se **reprocesaron las 22 respuestas reales capturadas**, sin nuevas llamadas a Ollama: **22/22 verificaciones del corpus final aprobadas**. Se midieron omisiones, falsas habilidades catalogadas, metas inesperadas, roles y restricciones. Los tiempos del replay son de procesamiento local y están separados del tiempo real de Llama. No se repitieron las 22 llamadas con cada ajuste: se usó replay para limitar carga y llamadas focalizadas para comprobar el modelo. Los resultados originales fallidos permanecen en la evidencia.

Ejemplos de salida final:

| Fuente | Resultado relevante |
| --- | --- |
| Sé programar con SQL y crear consultas | SQL una sola vez; crear consultas se conserva como capacidad explícita distinta, no como sinónimo inventado de SQL |
| Tengo experiencia en Blender y Unreal Engine 5 | Habilidades Blender y Unreal Engine 5; experiencias basadas en frases originales |
| Diseño interfaces UX/UI en Figma | UX/UI y Figma como etiquetas separadas |
| No sé Python. Domino SQL | Solo SQL como habilidad; ninguna meta Python inferida |
| No tengo experiencia laboral ni profesional. Quiero aprender diseño | Sin experiencia positiva; meta diseño, sin duplicar aprender diseño |
| Me gustan los videojuegos | Interés, sin habilidad técnica acreditada |
| Figma es obligatorio | Figma en obligatorias, no como condición logística |
| Python y SQL son opcionales | Ambas deseables; ninguna obligatoria |
| SQL obligatorio. Python no es obligatorio. No exigimos Docker | Solo SQL obligatorio; no se inventa preferencia por Python o Docker |

### MySQL QA, Nomic y frontend

Se creó vacía **softtek_formador_equipos_qa_semantics_20261025_77dd5b**, copiando solo DDL y revisión Alembic, sin registros de la principal. Se probaron FastAPI real (8011), MySQL 8/InnoDB, Nomic real y otro FastAPI aislado (8012) con host Ollama inaccesible. No se detuvieron servicios compartidos.

**54 comprobaciones aprobadas**:

- Los 10 perfiles y 6 proyectos del corpus final se confirmaron por HTTP con sus salidas revisadas, persistieron en JSON y mantuvieron revisión de fuente correcta. Los casos con contenido generaron vectores Nomic reales, finitos, de **768 dimensiones**. Antes de confirmar, el adaptador no acreditó habilidades a partir del borrador.
- P05/P07/P08 quedaron sin_contenido, con metas conservadas y sin vector; reintentar devolvió **409**. Intereses reales sin habilidades (P09) sí proporcionan contenido semántico, pero no prueban competencias.
- SQL/programar con SQL, Blender/experiencia en Blender, UE5 y Figma coincidieron con requisitos reales después de confirmar. No sé Python, deseo de aprender Docker e interés en videojuegos **no** dieron un requisito por cumplido. La recomendación Docker quedó needs_review con requisito desconocido y sin fortaleza Docker inventada, aunque había un vector real del perfil.
- El perfil vacío siguió sin_contenido con Ollama inaccesible; el perfil con contenido quedó pendiente_embedding y el reintento recuperó listo. Una interpretación fallida devolvió 503 y conservó la confirmación sin_contenido anterior. Añadir contenido y reconfirmar produjo un embedding.
- La confirmación humana fusionó alias duplicados. Publicar dos veces con la misma clave recuperó la misma fila. Recomendaciones, invitación, aceptación y equipo continuaron funcionando.

Los análisis Llama del corpus se ejecutaron contra el servicio real; para limitar llamadas, MySQL recibió por HTTP sus salidas capturadas, reprocesadas por el código final y revisadas como fixtures humanos. No se afirma que las confirmaciones volvieran a invocar Llama. La persistencia y todos los vectores de estas comprobaciones fueron reales.

Se comprobó visualmente el perfil P05 en React: mensaje **Datos confirmados; falta contenido para el análisis**, meta diseño conservada, fortalezas vacías y **sin botón Reintentar análisis**. Cero errores de consola capturados. [Captura del estado](evidencias/2026-10-25-semantica/perfil_sin_contenido.png).

La base principal conserva los mismos conteos/checksums/DDL/revisión de la tabla de la primera ronda: **no se modificó**. QA quedó con 12 usuarios/perfiles, 7 eventos, una solicitud y un participante ficticios. No se creó ni ejecutó migración sobre la principal.

### Límites y pendientes de esta ronda

- Catálogo intencionalmente limitado: fuera de esos ocho conceptos, etiquetas compuestas, paráfrasis, correferencias o intenciones complejas pueden necesitar corrección humana. No se promete comprensión general del español. No se fusionan conceptos no catalogados por semejanza; crear consultas no equivale automáticamente a SQL, ni Unreal Engine 4 a UE5.
- Las negaciones no se convierten automáticamente en hechos negativos publicados. La fuente del borrador y su clasificación interna conservan la distinción; acreditar una negación como evidencia confirmada requeriría una revisión explícita de ese contrato, que no se amplió en esta ronda.
- Los perfiles existentes no se reescriben. Los ya pendientes sin contenido adoptan sin_contenido al reintentar/reconfirmar. Etiquetas antiguas compuestas fuera de los alias exactos requieren revisión. No hay migración masiva ni regeneración automática.
- Llama crudo sigue produciendo errores; los filtros y el corpus no sustituyen la confirmación humana. Los casos fuera del catálogo y textos más largos pueden omitir hechos válidos por el control conservador de apoyo literal. La extracción literal de roles también es limitada.
- QA-06/07/08/09/10/11/12/16/17 y el restablecimiento de contraseñas bcrypt antiguas ambiguas siguen fuera de este encargo. No se agregaron reuniones, feedback, nuevos modelos o infraestructura.

La segunda ronda se entrega en un commit local de corrección semántica después de validar. No se hace push ni merge. El runner y resultados intermedios de laboratorio permanecen en `backend/.venv/qa_semantics_20261025/`; el corpus de entrada y las regresiones sí están en el repositorio. Los procesos habituales no se reiniciaron: su aplicación requiere la recarga normal del backend.

La pestaña y los tres procesos QA creados para esta ronda se cerraron al terminar. Se conserva la base aislada para reproducir las evidencias; no se limpió ni restableció la base principal.

## Tercera ronda — coherencia funcional del frontend, 2026-10-26

Inicio sobre `033f97f`, rama `feat/ai-matching`, árbol limpio. Se verificó con `git merge-base --is-ancestor` que **2157a43 y 033f97f están conservados**. Se revisaron el informe integral, el seguimiento y las evidencias disponibles. No hubo cambio de rama, merge, push, migraciones ni nuevas dependencias. Se conserva el diseño de Isaac y los módulos de autenticación, idempotencia, parser y concurrencia.

### Correcciones por hallazgo

| ID | Resultado y alcance |
| --- | --- |
| QA-06 | Disponibilidad calculada a partir del estado, capacidad incluyendo al creador, roles válidos y filas ORM reales de participantes. Los eventos exponen acepta_participacion, roles_disponibles, motivo_no_disponible y puede_solicitar; capacidad global no equivale a vacante de rol. Los adaptadores excluyen proyectos/candidatos sin una vacante utilizable antes de llamar al motor. No cambian scoring, pesos, desempates ni reglas de evidencia. Detalle, listado y selectores de invitación consumen las vacantes del servidor y no recuperan roles ocupados como alternativa. Se distinguen solicitudes pendientes e integrantes existentes. El detalle identifica la capacidad total y muestra ocupación parcial, por ejemplo 1 de 2 vacantes. Los eventos heredados sin roles conservan Participante cuando hay capacidad. |
| QA-07 | Equipos recibe cobertura_habilidades calculada con requisitos globales y habilidades de roles confirmados, deduplicadas mediante el catálogo existente, y habilidades confirmadas y permitidas de los miembros reales, incluido el creador. Un rol ocupado no prueba una habilidad. Se distingue Por acreditar de ausencia demostrada; información privada o sin confirmar produce estado desconocido cuando impide completar la evaluación. Sin requisitos útiles se muestra Desconocida y un guion, nunca 0/0 como éxito, también para lectores de pantalla. |
| QA-08 | PublicProfile carga el perfil real del usuario autenticado para comparar intereses y bloques confirmados. Ante error o falta de confirmación no inventa coincidencias. RecommendationCard admite un viewer real y deja de confiar en currentUser o bloquesComunes de demostración. Calendarios constantes siguen en mockData; los datos de demostración quedan en portada/sistema de diseño, con aviso visible de que perfiles, testimonios y cifras son ilustrativos. |
| QA-12 | q encuentra nombre, carrera y habilidades confirmadas, visibles y con consentimiento; usa el catálogo conservador, incluyendo programar con SQL. No descubre habilidades ocultas, borradores, perfiles pausados ni cuentas inactivas. Carrera, habilidad, semestre y bloques mañana/tarde/noche se filtran en el servidor antes de limit; lun-tarde sí corresponde al filtro tarde. Los selectores se basan en perfiles reales recibidos. La UI aclara que son bloques declarados, sin garantizar una hora exacta. |
| QA-16 | Inicio e Invitaciones usan un mensaje común según el tipo real de solicitud: el creador recibe Solicitud aceptada. Se incorporó el solicitante al equipo.; la persona que acepta una invitación recibe Te uniste al equipo. Los errores muestran el detalle del servidor. |
| QA-17 | /meeting muestra Reuniones no disponibles, explica que no envía ni guarda propuestas y permite volver a equipos. Se retiraron el formulario simulado, el toast de envío y la navegación al equipo ficticio t1. No se desarrolló un servicio de reuniones. |
| QA-09 | POST /eventos/{id}/confirmar exige fuente_revision de 64 caracteres hexadecimales. Omitirla produce 422; una revisión anterior produce 409; la vigente confirma y genera Nomic. React ya enviaba esa huella y ahora también explica que debe recargarse si falta. La creación inicial revisada y su clave de idempotencia conservan sus contratos. |
| QA-10 | Perfil y revisión inicial advierten que ocultar campos individuales no borra lo escrito en biografía/resumen público. Mi perfil permite corregir o vaciar ese texto, confirmarlo y regenerar su vector mediante rutas existentes. Se conserva la invalidación de resúmenes anteriores ante otros cambios semánticos; no se publica de nuevo un resumen obsoleto por defecto. El consentimiento describe también el directorio; el correo se identifica correctamente como visible en perfil público y equipos si se activa. No se hace redacción automática ni migración de biografías existentes. |

Otros ajustes de veracidad encontrados en la revisión: Inicio ya no deduce que no existen proyectos cuando solo faltan recomendaciones para una persona. El mensaje de invitación se identifica como Plantilla editable, sin atribuir su texto fijo a una generación de IA. Los niveles de fortalezas confirmados por personas se conservan en la proyección pública.

### Archivos y contratos

- Backend: `services/team_rules.py` añade una lectura de disponibilidad sin tocar los locks de aceptación; `services/team_coverage.py` calcula cobertura conservadora; rutas `eventos.py`, `solicitudes.py` y `perfiles.py` exponen los datos reales y aplican privacidad/filtros. `recommendations/orm_adapter.py` filtra imposibilidades operativas; el motor puro permanece intacto. `schemas/evento.py` añade campos de lectura y `schemas/ai_integration.py` exige la huella al confirmar.
- Frontend: `services/api.js` transporta esos contratos y filtros; `lib/contracts.js` reúne decisiones de disponibilidad, mensajes y resumen revisado; `hooks/useAuthenticatedProfile.js` obtiene la comparación real. Se conectan PublicProfile, RecommendationCard, StudentSearch, TeamCoverageChart y las páginas Inicio, Estudiantes, Perfil, Proyectos, Detalle, Invitaciones, Equipos y Reuniones. RoleCoverage muestra vacantes parciales. Se retira el cálculo de habilidades basado en roles de `lib/projects.js`.
- Regresiones permanentes: `backend/tests/test_frontend_contracts.py` (**23 casos**), `frontend/tests/contracts.test.js` (**13 casos**, Node test runner, Vite SSR y renderizado React). `frontend/package.json` añade npm test usando dependencias existentes.
- Dos tests previos se actualizan para proporcionar la huella que ahora exige el contrato; conservan sus aserciones de permisos, persistencia y recuperación de Ollama. El test de perfil malformado prepara una segunda cuenta con consentimiento y comprueba que esa cuenta sigue apareciendo; la cuenta sin consentimiento ya no se espera en el directorio. No se debilita la validación para aprobar.

**Compatibilidad deliberada:** los clientes HTTP antiguos que confirmen proyectos sin huella deberán obtener primero GET /eventos/{id} como creador y enviar su fuente_revision en la confirmación. El frontend actual es compatible y se verificó visualmente. La edición PUT mantiene su compatibilidad anterior; no confirma automáticamente IA. No se modifica el esquema MySQL.

### Reproducción y pruebas automáticas

Antes de corregir, el lote nuevo backend produjo **6 fallos / 4 aprobados** y el lote inicial de renderizado React **3 fallos / 0 aprobados**: faltaban disponibilidad y cobertura reales, no había búsqueda por equivalencia y se aceptaba una confirmación sin huella; React anunciaba coincidencias mock y cobertura completa sin evidencia. Los mensajes de adhesión y el envío ficticio se reprodujeron mediante el código activo y las capturas de auditoría previas. No se atribuye a esta ronda un recorrido visual de la versión antigua de esas dos pantallas.

La primera ejecución completa durante la implementación detectó además una regresión de consulta vacía al normalizar q. Se corrigió y se añadió una regresión con q vacío, carrera vacía y límite aplicado después de privacidad. Se mantuvieron los fallos intermedios en el laboratorio ignorado. No se cambiaron tests para ocultarlos.

| Comando final | Resultado | Duración del proceso |
| --- | --- | --- |
| python -m pytest -q | **354 aprobadas**, 331 anteriores + 23 nuevas | 32.64 s; pytest 31.33 s |
| python -m pip check | Sin dependencias rotas | 0.51 s |
| npm test | **13 aprobadas** | 1.21 s |
| npm run build | Correcto; 1990 módulos | 0.98 s |
| npm run lint | 0 errores; 1 advertencia anterior | 3.45 s |

Se mantienen las advertencias previas de Starlette TestClient/httpx y de dependencia state en RequireSession.jsx:29. Los tests backend automáticos usan SQLite aislado y embeddings simulados; no son prueba de MySQL ni de calidad Llama. El frontend renderiza componentes reales y comprueba contratos, pero no sustituye la interacción visual descrita a continuación. [Resultados completos de comandos](evidencias/2026-10-25-frontend/checks.json).

### MySQL QA y servicios reales

Se creó vacía **softtek_formador_equipos_qa_frontend_20261025_979b6c** copiando únicamente DDL y revisión Alembic, sin registros de la principal. Se usaron MySQL **8.0.46/InnoDB**, Python **3.13.15**, FastAPI **0.143.0**, SQLAlchemy **2.1.4**, React **19.3.0**, Node **24.19.0**, npm **11.17.0**, Vite **8.3.4** y Ollama **0.40.5** con Nomic Embed Text real de **768 dimensiones**. FastAPI QA en 8011 y Vite QA en 5174; el frontend de prueba apuntó exclusivamente a ese backend.

**48 comprobaciones reales aprobadas:** 33 del lote inicial, 10 adicionales y 5 de cierre; la última es una inspección de la principal sin escrituras. Son pasos de recorridos y controles, no 48 defectos independientes. Evidencias: [lote inicial](evidencias/2026-10-25-frontend/mysql_results.json), [adicionales](evidencias/2026-10-25-frontend/additional_results.json), [cierre](evidencias/2026-10-25-frontend/closeout_results.json).

- Registro/login ficticios, perfiles revisados, privacidad de fortalezas y búsqueda por Python/SQL/alias; pausa y falta de consentimiento excluyen también búsqueda por nombre. Filtros combinados y de bloque se verifican sobre MySQL antes del límite.
- Proyecto de capacidad 4, creador y un integrante: quedan 2 cupos globales pero el único rol ya está ocupado. La respuesta declara sin vacantes, candidatos devuelve [], la recomendación de proyectos lo excluye y el intento directo sigue protegido con 409.
- Otro proyecto admite dos Backend. Una adhesión aceptada ocupa una vacante, mantiene otra utilizable y persiste en participantes_evento. Una invitación duplicada y una segunda aceptación devuelven 409; consulta de candidatos por no organizador devuelve 403.
- Requisitos globales Python/SQL con roles de habilidades vacías: el creador Python aporta 1/2, SQL queda Por acreditar. Añadir un miembro con SQL confirmado permite 2/2. Ocultar las fortalezas de ese miembro vuelve la cobertura desconocida, sin revelar SQL mediante el agregado; se restauró solo su preferencia ficticia.
- Huella ausente 422, obsoleta 409 y vigente 200. Edición, invalidación visible y reconfirmación desde React persisten en MySQL con fuente actual y Nomic listo. Se comprobaron **8 vectores almacenados, finitos, de 768 dimensiones**; las regeneraciones actualizan esas mismas filas. Hubo 11 confirmaciones/creaciones con vector real incluyendo los dos guardados visuales, sin llamadas Llama en esta ronda.
- Biografía corregida desde React coincide con JSON público, estructura confirmada y revisión del vector. La solicitud enviada visualmente es una fila real única; al iniciar sesión de nuevo sigue pendiente y deshabilita el botón de solicitud y la recomendación correspondiente.

Al cierre QA conserva **7 usuarios, 7 perfiles, 3 eventos, 3 solicitudes y 2 participantes**, todos ficticios. No se limpiaron tablas ni se reinició la base. Scripts temporales en `backend/.venv/qa_frontend_20261025/`, ignorados por Git. No se volvió a ejecutar el corpus Llama: su calidad y límites siguen documentados en la segunda ronda y sus regresiones continúan pasando.

### Recorridos visuales realmente ejecutados

Navegador IAB con React QA y backend/MySQL reales, usando tres cuentas ficticias. No se simularon interacciones mediante lectura de código:

1. Login del creador; Inicio, directorio y búsqueda programar con SQL; selección de otro perfil con lun-tarde/sab-manana frente al calendario vacío del creador, sin bloques compartidos inventados. [Captura](evidencias/2026-10-25-frontend/busqueda_sql_comparacion_real.png).
2. Equipos con requisitos globales: [Python 1/2, SQL por acreditar](evidencias/2026-10-25-frontend/cobertura_global_real.png); [cobertura desconocida](evidencias/2026-10-25-frontend/cobertura_desconocida.png) para proyecto sin revisión.
3. El creador acepta una adhesión en Invitaciones y ve [Solicitud aceptada](evidencias/2026-10-25-frontend/solicitud_aceptada_creador.png). Su fila real se comprobó después con ORM.
4. Edición del proyecto: [requiere revisión y desaparecen los candidatos anteriores](evidencias/2026-10-25-frontend/edicion_requiere_revision.png); revisión manual Python/SQL y [reconfirmación lista](evidencias/2026-10-25-frontend/proyecto_reconfirmado.png), conservada al recargar. No se pulsó Interpretar descripción con IA; la revisión fue humana.
5. Corrección y guardado de biografía desde Mi perfil, confirmación y persistencia verificadas por SQL/HTTP. [Aviso de privacidad](evidencias/2026-10-25-frontend/aviso_privacidad_biografia.png).
6. Login de candidato: [Inicio](evidencias/2026-10-25-frontend/inicio_recomendacion_real.png) y [Coincidencias](evidencias/2026-10-25-frontend/coincidencias_motor_real.png) muestran el mismo proyecto real del motor. Abrir detalle, elegir Backend, [enviar solicitud](evidencias/2026-10-25-frontend/solicitud_real_enviada.png) y recargar conserva Solicitud enviada deshabilitado.
7. Otro usuario ajeno al equipo abre el proyecto con rol ocupado y capacidad sobrante: [sin botón de solicitar, con motivo explícito](evidencias/2026-10-25-frontend/proyecto_sin_vacantes_utilizables.png).
8. [Reuniones no disponibles](evidencias/2026-10-25-frontend/reuniones_no_disponibles.png); acceso a /match tras cerrar sesión redirige a autenticación.

**Cero errores de consola capturados** en la pestaña de estos recorridos: [consola.json](evidencias/2026-10-25-frontend/consola.json). No se inspeccionó una traza HAR completa de todas las llamadas; estados HTTP relevantes se conservaron en los lotes dirigidos. No se declara probado el onboarding/registro completo desde navegador en esta ronda; registro y confirmación sí se comprobaron por HTTP real, y el recorrido visual de análisis inicial corresponde a rondas anteriores.

### Principal, Git y cierre operativo

**La base principal softtek_formador_equipos no fue alterada.** Solo SELECT, SHOW y CHECKSUM para inspección. Coinciden antes/después: usuarios 1/checksum 101962764; perfiles 1/checksum 2746401420; eventos, solicitudes y participantes 0/checksum 0. DDL SHA-256 `000c70b44ca454ac24551c35ee36780ad1d729221e175bdbb51f581cd9fa8dbe`; revisión `20261022_6a`. [Estado final verificable](evidencias/2026-10-25-frontend/final_state.json).

Se cerró la pestaña temporal y se detuvieron exclusivamente los procesos QA en 8011/5174. Los servicios previos conservaron PID: backend 8000/29204, Vite 5173/42856, MySQL 3306/9036 y Ollama 11434/10056. No se reconfiguraron. Para presentar el código nuevo en esos procesos hace falta su recarga/reinicio habitual; no se ejecutó contra la principal para evitar escrituras accidentales.

La entrega se prepara como commit local de corrección del frontend sobre feat/ai-matching, con seguimiento y evidencias ficticias. El hash exacto y estado de Git se comunican al terminar; no se incluye el propio hash en el archivo que forma parte del commit. No se incluyen .env, credenciales, tokens, registros personales ni scripts privados del laboratorio. No hay push ni merges.

### Límites y pendientes vigentes

- No se encontró un bloqueo nuevo en los recorridos ejecutados, pero no se certifica producción ni todos los navegadores/dispositivos. No hubo carga sostenida, reinicio de MySQL, matriz móvil completa o auditoría de seguridad exhaustiva. Las carreras de capacidad/rol/duplicados conservan sus tests; no se repitió aquí toda la matriz concurrente MySQL de la auditoría original.
- La disponibilidad es una instantánea: otra persona puede ocupar el último cupo antes del envío/aceptación. El backend conserva la revalidación transaccional y 409; la UI presenta ese error. No se bloquea un cupo por mirar una recomendación o enviar una solicitud.
- La cobertura acredita declaraciones humanas confirmadas, no competencia demostrada. Incluye habilidades obligatorias, deseables y de roles confirmados; no certifica restricciones, experiencia, calidad técnica ni horas exactas. Un perfil privado puede impedir determinar cobertura aun cuando su integrante realmente sepa la habilidad.
- QA-11 continúa como límite explícito: un bloque tarde no garantiza lunes 16:00–18:00. No se cambió el ranking ni se inventaron disponibilidades. El vocabulario Llama fuera del catálogo y sus latencias requieren revisión humana, como en ronda 2.
- El directorio carga candidatos para aplicar filtros de privacidad antes del límite, suficiente para el MVP; no se midió escalabilidad. Las opciones de filtros se obtienen de la muestra visible recibida; q permite buscar habilidades fuera de esas opciones. No se añadió búsqueda semántica ni acreditación por intereses/metas.
- Clientes antiguos sin fuente_revision deben adaptarse. Perfiles anteriores sin consentimiento explícito no aparecen en directorio; los datos no se borran. La biografía sigue siendo un campo público independiente; ocultar una lista no redacta su texto automáticamente.
- Persiste el pendiente histórico de recuperación segura de bcrypt ambiguo de más de 72 bytes. Reuniones y feedback persistente permanecen fuera del MVP. Las advertencias previas de herramientas siguen registradas.

Siguiente encargo acotado recomendado: ensayo de presentación con dos cuentas ficticias desde registro/onboarding en navegador y revisión móvil de los recorridos ya existentes, sin añadir funcionalidades ni ampliar arquitectura.

## Cuarta ronda — escenarios reales y confiabilidad, 2026-10-26

Informe completo vigente: [QA_ESCENARIOS_REALES_MATCHING_2026-10-26.md](informes/2026-10-26-escenarios-matching.md). Inicio limpio en `9fb42cd`, misma rama `feat/ai-matching`; se conservan `2157a43`, `033f97f` y los avances anteriores. No hubo push, merges ni cambios de esquema/arquitectura.

- El proyecto real «Gestor de tareas inteligente» tiene dos vacantes utilizables y requisitos confirmados. Los tres perfiles ajenos al creador no tienen consentimiento; ORM y endpoint devuelven correctamente cero candidatos. No se cambiaron preferencias reales. Se mejoró el estado vacío con explicación y actualización sin divulgar excluidos.
- Se reprodujeron dos POST de interpretación por las suscripciones de StrictMode y un 409 competidor. React ahora comparte solo solicitudes idénticas en vuelo por sesión, sin cachear resultados ni desactivar StrictMode. El backend además rechaza un análisis cuyo texto pendiente ya cambió. El primer error visible relatado no se reprodujo naturalmente: los intentos frío/caliente mostraron resultado pese al 409. La caída aislada sí mostró 503 recuperable y el reintento visual funcionó sin repetir el formulario.
- Se corrigió una mezcla real de identidad entre dos pestañas: JWT estaba en sessionStorage e identidad en localStorage compartido. Ambos quedan ahora en la sesión de la pestaña; se verificaron organizador y candidato independientes, aceptación y equipos. El backend había protegido los accesos ajenos con 403.
- Catálogo v4 de 14 conceptos: conserva Git/FastAPI, prototipado y deporte explícitos; normaliza prefijos de interés sin duplicados; recupera listas deportivas literales y descarta composición del equipo tratada como restricción. Obligatorio prevalece sobre deseable para la misma habilidad; no se cambiaron pesos ni umbrales del ranking. Se corrigió también el texto accesible de interés compartido.
- **365 pytest + 21 frontend**, pip check y build correctos, lint con cero errores y una advertencia previa. Son 11 regresiones backend y ocho casos frontend adicionales; se fortaleció una aserción accesible existente. Las pruebas semánticas/concurrentes fallaron antes de corregir; evidencia conservada.
- **14 escenarios MySQL y tres recorridos visuales completos** (web, videojuegos, fútbol), con recomendaciones para ambos públicos, invitación, aceptación, recarga, edición y reconfirmación. Lote de 271 comprobaciones, extensión de 17, cierre de 26 y repetición de 57 en otra QA vacía; no representan esa cantidad de escenarios independientes. Carrera InnoDB del último cupo: [200,409], exactamente un participante.
- **36 intentos Llama**: 34 respuestas obtenidas y dos ConnectionError deliberados, cero timeouts observados. Corpus inicial de 14 llamadas conserva sus omisiones; replay final de esas salidas 14/14 y cuatro repeticiones reales 4/4. El replay usa cliente simulado y no cuenta como llamadas nuevas. Se mantiene revisión humana: la salida cruda todavía puede clasificar mal o redactar experiencia redundante.
- Dos QA aisladas, **57 usuarios y 23 proyectos ficticios** en total; 23 solicitudes/invitaciones y 22 filas de participantes incorporados. Primera QA: 46 perfiles listos, uno sin_contenido y uno obsoleto deliberado. Sus 46 vectores de perfil y 20 de evento son finitos, de 768 dimensiones y revisión vigente; cero incompatibles al cierre.

**Principal sin alterar:** en esta ronda ya tenía cuatro usuarios, cuatro perfiles y un evento, añadidos desde la entrega anterior. Se comparó ese estado inicial actual: conteos, checksums, DDL y Alembic siguen iguales, sin escrituras reales. La evidencia anonimizada, trazas, salidas Llama y capturas están en `docs/qa/evidencias/2026-10-26-matching/`. Los procesos habituales no se reconfiguraron; solo se detuvieron los servidores QA y se cerraron las pestañas temporales.

Pendientes explícitos: un candidato con evidencia parcial Git puede preceder a uno con Blender cuando obligatorias siguen desconocidas; requisitos globales se evalúan por persona y la asignación a roles sigue manual; QA-11 no deduce horas exactas de bloques; vocabulario fuera del catálogo y latencia requieren revisión. No se declara ranking perfecto ni fiabilidad universal de Llama. Continúa la limitación heredada de bcrypt >72 bytes. No se implementaron reuniones, feedback ni infraestructura nueva.

El commit local de esta ronda usa el mensaje `fix(mvp): stabilize analysis sessions and validate real matching`; el hash se comunica en la entrega final, fuera del documento que integra el propio commit.

## Repetición final solicitada y publicación

Se repitió el flujo principal desde React en otra QA vacía, con tres cuentas nuevas y Llama/Nomic/MySQL reales: **perfil IA → confirmación/consentimiento → proyecto → dos candidatos recomendados → invitaciones → aceptaciones → equipo completo tras recargar**. Antes de confirmar no aparecían; después aparecieron SQL y Figma con explicaciones respaldadas, sin convertir negaciones o aprendizaje en fortalezas. Cuatro interpretaciones al primer intento, sin POST generativos duplicados; cuatro vectores reales vigentes de 768 dimensiones en ese recorrido y uno adicional de otra convocatoria. También se comprobó con nueva sesión React que ambos integrantes siguen siendo recomendables para un proyecto diferente con vacantes. No hizo falta cambiar prompts ni producción adicionalmente.

La suite volvió a pasar: **365 backend y 21 frontend**, pip check/build correctos y lint sin errores, con avisos previos conservados. Treinta y tres comprobaciones finales MySQL/HTTP aprobadas; principal intacta y servicios habituales preservados. Los detalles, tiempos, las incidencias exclusivas del arnés y las capturas están en [VALIDACION_FLUJO_WEB_2026-10-26.md](informes/2026-10-26-flujo-web.md).

La corrección anterior quedó en `0c1085b`. Para esta entrega el usuario autorizó commit y push a la rama actual, `feat/ai-matching`; se publica la corrección junto con el commit de evidencia, sin merges ni force. Los límites de horarios, requisitos globales y variabilidad generativa del informe amplio siguen vigentes. Los perfiles reales sin consentimiento no se modificaron automáticamente.

## Caso MANUAL01 vacío — consentimiento visible y activación propia

Se inspeccionó el proyecto del usuario en lectura: abierto, listo, dos vacantes y sin integrantes/solicitudes para ese proyecto. Beatriz y Carla estaban confirmadas/listas, pero con consentimiento false; motor y endpoint devolvían 200 []. No se cambiaron sus permisos automáticamente ni se debilitó la política.

Inicio/Mi perfil muestran aviso; Mi perfil permite **Activar y guardar recomendaciones** enviando solo el permiso propio y bloqueando el atajo con cambios pendientes. El onboarding exige elegir si se confirma con recomendaciones apagadas; ambas opciones se conservan. El vacío da la ruta exacta en cada cuenta.

QA real: **0 → 1 → 2 candidatos** al activar SQL y diseño desde React, con dueño todavía sin consentimiento y sin cambiar requisitos/embeddings. Dos altas adicionales probaron guardar false y activar explícitamente true con Llama/Nomic reales; 29 comprobaciones HTTP/MySQL aprobadas, cinco perfiles y un proyecto ficticios. Los vectores existentes no cambiaron ni se regeneraron. Suite **367 backend + 27 frontend**, pip check/build correctos, lint sin errores y una advertencia previa.

Desde el snapshot de preparación QA la principal conservó conteos/checksums/DDL/revisión; antes hubo un alta externa, documentada para no atribuirla a QA. Las escrituras del ensayo fueron exclusivamente en la base aislada. Sin cambios de prompts, ranking ni backend de producción. [Resultados y capturas](informes/2026-10-26-consentimiento-candidatos.md). Commit y push solicitados a feat/ai-matching.
