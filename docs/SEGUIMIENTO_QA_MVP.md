# Seguimiento QA del MVP — 2026-10-25

Repositorio: `D:\projects\Softtek_Formador_Equipos`. Rama: `feat/ai-matching`. HEAD de partida y final: `568026a`. Cambios disponibles en el árbol de trabajo, sin commit, push, merge ni cambio de rama.

Se leyó el [informe integral](REPORTE_QA_REAL_2026-10-25.md) y su [evidencia JSON](qa_evidencia_20261025/datos_auditoria.json). Esta entrega implementa las correcciones de estabilidad, recuperación y autenticación solicitadas. No modifica arquitectura, framework, dependencias, esquema ni datos de la base principal. Conserva el diseño de Isaac y el motor de matching.

## Resultado por hallazgo

| ID | Estado | Corrección implementada |
| --- | --- | --- |
| QA-01 | Corregido | Validación de los campos JSON consumidos por React: visibilidad con claves conocidas y booleanos estrictos, fortalezas, listas de intereses/aprendizaje/experiencia/disponibilidad, semestre, biografía y opciones del perfil. Peticiones malformadas devuelven 422 antes de guardar. Proyección pública/privada defensiva para datos legados y privacidad inválida cerrada. Una estructura IA dañada se omite al leer, sin reescribirla. |
| QA-04 | Corregido | Habilidades de roles: listas de strings no vacíos, hasta 150 caracteres y 100 elementos; nombres de rol de 1–50, identificadores de 1–100, vacantes enteras 1–8 y bandera indispensable booleana. Requisitos estructurados y detalles usados por el frontend tienen límites/tipos. Datos legados se proyectan de forma segura en detalle, listados y equipos. El mapper React descarta objetos en habilidades y entradas de rol incompatibles. |
| QA-03 | Corregido | ConnectionError incorporado, TimeoutError, errores httpx y del SDK se traducen a errores controlados. Confirmar/crear conserva los datos y devuelve pendiente_embedding ante fallo del vector; interpretación fallida devuelve 503 y restaura el estado confirmado anterior. Se conservan los borradores y las rutas de reintento existentes. Publicación con Idempotency-Key recupera la misma fila y detecta un cuerpo distinto con 409. |
| QA-02 | Corregido con límite heredado explícito | Altas nuevas usan bcrypt_sha256 y verifican la contraseña completa. Se admiten Unicode y contraseñas largas sin colisión por el byte 72. Login conserva compatibilidad con bcrypt existente de hasta 72 bytes y migra el hash al verificar correctamente una cuenta activa. Un intento de más de 72 bytes contra bcrypt heredado se rechaza explícitamente; no se migra a partir de un prefijo ambiguo. |
| QA-13 | Corregido | Nombre 1–150, carrera 1–100, correo hasta 100, estado/municipio hasta 50 caracteres en registro; nombre/carrera también acotados en edición. La validación sucede antes de insertar, evitando el 500 de MySQL estricto por nombre de 151 caracteres. |

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
| Este documento y `docs/qa_estabilidad_20261025/` | Seguimiento y evidencia filtrada de las ejecuciones reales. El informe original y sus evidencias se conservan intactos. |

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

**63 comprobaciones reales aprobadas**: lote principal 51, comprobaciones de la versión final de idempotencia 5 y cierre 7. Algunas verifican distintos pasos del mismo recorrido; no representan 63 errores independientes. Se conservaron respuestas/estados SQL filtrados en [resultados.json](qa_estabilidad_20261025/resultados.json).

- Registro, políticas de contraseña y longitudes: 422 sin insertar; ASCII/Unicode largos autentican solo con la clave completa; cuenta bcrypt previa migra al verificar; sufijo ambiguo heredado da 422 sin tocar su hash.
- Perfil propio malformado: 422; otro usuario sigue consultando el directorio con 200. Perfil y estructura IA legados dañados se leen sin 500 ni corrección persistida automática; privacidad inválida no publica correo/campos.
- Rol con objeto en habilidades: 422 y conteo de eventos **0 → 0**. Datos legados con vacantes incompatibles no rompen detalle/equipos/recomendaciones.
- Backend separado con Ollama apuntando a `127.0.0.1:9`: interpretación 503; perfil confirmado 200 pendiente; proyecto creado/confirmado recuperable. No se apagó Ollama compartido.
- Dos POST idénticos con la misma clave devolvieron **[201,201]**, mismo ID y **una fila**. Dos peticiones concurrentes hicieron lo mismo. Un cuerpo distinto con la misma clave devolvió 409. Se volvió a comprobar la concurrencia contra la versión final del código.
- Reintentos existentes recuperaron embeddings **reales, finitos y de 768 dimensiones**, con revisión de fuente coincidente y estado listo.
- Recomendaciones con Python confirmado, exclusión de invitación pendiente, permisos ajenos 403, invitación, rechazo de duplicado, aceptación, adhesión y filas de participantes correctas. Doble aceptación devuelve 409; el equipo persiste.
- Dos llamadas Llama instrumentadas: perfil **16.397 s**, proyecto **4.182 s**, ambas HTTP 200. Una tercera interpretación se ejecutó desde el asistente React; no se instrumentó su duración. No se repitió el corpus completo de calidad de IA porque este encargo corrige estabilidad/seguridad.

Cuatro recorridos visuales adicionales en navegador IAB contra Vite 5174 y FastAPI QA 8011: login; detalle legado con candidatos; directorio/perfil legado con privacidad cerrada; publicación desde React y recarga del proyecto. **Cero errores de consola capturados**. La publicación visual quedó en evento QA **5**, una fila, clave del intento y huella persistidas, vector de 768 y estado listo. La recarga conservó el resultado.

Capturas: [detalle legado protegido](qa_estabilidad_20261025/detalle_legado_protegido.png), [directorio protegido](qa_estabilidad_20261025/directorio_perfil_legado.png), [publicación confirmada](qa_estabilidad_20261025/publicacion_react_confirmada.png), [proyecto listo tras recargar](qa_estabilidad_20261025/proyecto_persistido_listo.png).

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
2. QA-05 y aspectos semánticos de QA-14/15: extracción atómica, equivalencias SQL/Blender/Figma, negaciones, distinción de falta de contenido y evaluación amplia de timeouts. Se mantuvo la revisión humana; estos problemas de calidad no se declaran resueltos por pasar validación de tipos.
3. QA-06/07/08: disponibilidad accionable por rol, cobertura 0/0 y comparaciones con currentUser de demostración.
4. QA-09/10/11/12/16/17: huella opcional en clientes heredados, expectativas de privacidad de biografía, contrato de horarios, búsqueda por habilidad, mensaje de adhesión y reunión ficticia. No se añadieron reuniones ni otras funcionalidades.
5. No se ejecutó carga sostenida, prueba de todas las carreras posibles, migración desde cero, ni auditoría de seguridad exhaustiva. No se inyectó pérdida de respuesta en el navegador: las repeticiones y su concurrencia se verificaron mediante HTTP/MySQL, y la clave emitida por React se verificó en la fila persistida. Se verificaron los recorridos documentados; las advertencias previas de herramientas siguen visibles.

Los cambios de código y tests quedan sin commit para revisión. El informe integral previo y sus evidencias ya eran archivos sin seguimiento al iniciar este encargo y se conservaron. No hubo push ni merges.

Los servidores habituales no se reiniciaron; para ejecutar el código actualizado en esos procesos debe aplicarse su recarga/reinicio normal. La comprobación de esta entrega se hizo en procesos QA separados, ya detenidos.
