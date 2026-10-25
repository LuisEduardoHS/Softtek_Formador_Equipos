# Estado del proyecto e integración de IA

Fecha: 25 de octubre de 2026. Revisión del código integrado en `feat/ai-matching`.

## Conclusión

El proyecto ya tiene un MVP de IA conectado entre React, FastAPI y el motor de recomendaciones. Existen extracción de perfiles y proyectos con Ollama, revisión humana, almacenamiento ORM, embeddings, autenticación con JWT y consultas reales de recomendaciones. La integración técnica principal está bastante avanzada; todavía faltan preparación de MySQL, cierre de flujos de edición/reintento y reglas de participación para considerar terminado el producto.

La estructura actual sirve. Conviene completar los recorridos de usuario y corregir contratos concretos antes de reorganizar carpetas o añadir infraestructura.

## 1. Git: qué se integró

- Inicio: rama local `feat/ai-matching`, commit `3740b29`, sin modificaciones locales.
- Se actualizaron las referencias con `git fetch origin --prune`.
- Se incorporaron los 31 commits pendientes de su rama remota mediante avance directo hasta `72eb733`.
- La rama solicitada como Isaac existe remotamente con el nombre `origin/isaac`, punta `f0c1c20`.
- Merge local: `696e2bc`, con padres `72eb733` y `f0c1c20`. Ambos historiales quedan conservados. Se verificó además que ningún archivo versionado de ninguna de las dos puntas falta en el árbol integrado.
- Respaldo del punto inicial: rama local `codex/backup-ai-matching-20261025`.
- No se hizo push. `main` y la rama remota de Isaac no se modificaron.

Hubo ocho archivos con conflictos. Se combinaron los flujos de revisión y autenticación de IA con las mejoras de Isaac: edición de proyectos, solicitudes para unirse, nombres de creadores, avance real del perfil, edición del nombre y ajustes visuales.

Decisiones necesarias para que el merge sea coherente:

1. Edición de eventos y solicitud de adhesión exigen Bearer y comprueban que el ID enviado coincida con la sesión.
2. Las notificaciones de recomendaciones siguen usando el motor común; se añadieron las notificaciones de adhesión de Isaac.
3. La edición conserva las cinco categorías de la creación: académico, personal, deportivo, videojuegos y general.
4. Al editar un evento se invalidan los requisitos confirmados y su vector anterior; la versión anterior se guarda como borrador. El evento abierto permanece abierto, con IA pendiente de revisión. Así no se recomienda usando requisitos antiguos como si fueran actuales. Falta terminar la reconfirmación desde la pantalla de edición.
5. La cobertura de roles en la respuesta se obtiene de participantes reales; no se toma una asignación del navegador como prueba de membresía.
6. Se corrigió una expresión JavaScript que podía interpretar la lista de invitaciones como una llamada a un objeto por el salto de línea, y se igualaron tipos al comparar IDs de proyecto.
7. Se añadieron seis casos de regresión: adhesión autenticada y aceptación del solicitante correcto, y edición con invalidación de IA para las cinco categorías.

## 2. Estructura y responsabilidades

```text
frontend/src/
  pages/              Pantallas y sus recorridos
  components/         Componentes visuales por área y UI compartida
  services/api.js     Cliente HTTP y conversión de contratos API → UI
  hooks/useAsync.js   Estados de carga/error y recarga
  lib/                Sesión, cobertura, avance del perfil y utilidades
  data/               Demostraciones y catálogos compartidos mezclados

backend/app/
  api/routes/         Autenticación, perfiles, eventos, solicitudes y recomendaciones
  schemas/            Contratos HTTP y confirmación humana
  models/             Cinco entidades de persistencia
  db/                 Motor SQLAlchemy y sesión por petición
  core/               Seguridad y configuración
  services/ai/
    profile_parser.py Extracción de perfil
    event_parser.py   Extracción de requisitos
    embeddings.py     Texto semántico y vectores
    integration.py    Revisión de fuente, estados y persistencia de vectores
    matching/         Evaluación y ranking puros
    recommendations/ Contextos, explicaciones, vigencia y adaptación ORM
backend/alembic/      Migraciones
backend/tests/        Pruebas de contratos, IA, motor y API

database/             SQL inicial de MySQL
docs/                 Diseños, auditorías históricas y guías de operación
```

La separación de parsers, motor puro y adaptador ORM es útil y debe conservarse. Las rutas orquestan persistencia y permisos; las reglas matemáticas no dependen de FastAPI. React tiene una capa de servicios central que permite ajustar contratos sin modificar todas las pantallas.

El flujo real es: texto → sugerencia IA → revisión de la persona → confirmación en BD → embedding con revisión de fuente → adaptación ORM de datos permitidos → matching → explicación pública → acción del usuario. La generación de texto no decide automáticamente quién entra al equipo.

## 3. Estado por función

| Función | Implementación existente | Pendiente para darla por terminada |
| --- | --- | --- |
| Registro, login y sesión | JWT, contraseña, verificación de cuenta y rutas privadas; pruebas HTTP | Configurar secreto y BD locales; probar el recorrido en navegador con MySQL |
| Alta de perfil con IA | Interpretación, edición de etiquetas y confirmación; persiste estructura y genera vector | Validar calidad del modelo real, arranque lento y recuperación del borrador después de recargar |
| Edición del perfil | Cambios relevantes pasan por confirmación; cambios básicos usan PUT | Mostrar estado IA y resolver explícitamente perfiles antiguos/sin confirmar aunque solo se cambien permisos |
| Privacidad | Visibilidad por campo, pausa y consentimiento para recomendaciones | Acordar política uniforme entre directorio, perfil público y recomendaciones; revisar qué señales pueden usar vectores con campos ocultos |
| Creación de proyecto | Interpreta roles/requisitos, permite revisión y alternativa manual, publica confirmado | Evaluar omisiones de extracción; mantener una fuente coherente de habilidades globales y habilidades por rol |
| Edición de proyecto | Modal y endpoint de Isaac integrados y autenticados | Mostrar/revisar requisitos y reconfirmar tras editar; hoy invalida IA y no tiene ese paso en el modal |
| Embeddings | Nomic, vector finito de 768 dimensiones y metadatos de modelo/pipeline/revisión | Mostrar estados, exponer botones de reintento y verificar recuperación real |
| Recomendaciones de proyectos | API real; Inicio y Coincidencias la consumen | Calidad de habilidades canónicas y disponibilidad; pruebas del recorrido completo con varias cuentas |
| Candidatos para proyecto | Endpoint del creador, exclusiones de miembros/pendientes y explicaciones reales | Presentación autorizada de nombres y relación clara con roles; hoy aparecen como Persona #ID y lista general |
| Invitaciones | Envío, recepción, aceptación/rechazo y membresía | Cupos, ocupación de rol, duplicados en ambos sentidos y validación transaccional |
| Solicitud para unirse | Ahora tiene endpoint real y se acepta al remitente solicitante | Validar ocupación desde participantes y cupos; recuperar solicitud pendiente al recargar el detalle |
| Equipos y cobertura | Consultan BD, incluyen miembros y roles | Reglas de baja/cambio de rol/cierre; decidir cuántas personas puede cubrir cada rol |
| Notificaciones | Invitaciones, respuestas y actividad; sugerencias usan el mismo motor | Lectura/persistencia si se requiere; evitar recalcular todo por cada evento al crecer |
| Búsqueda de personas | Directorio real y filtros parciales | Buscar también habilidades, corregir filtro de franja y sustituir catálogos de demostración |
| Reuniones | Pantalla de demostración con mensaje de éxito | Modelo, endpoint y persistencia; actualmente no envía ni guarda una propuesta |
| Feedback/descartar recomendación | Componentes heredados con estado local; no hay ruta de feedback | Definir si forma parte del MVP; persistirlo si se promete aprender de las decisiones |

## 4. Base de datos: existe el diseño, falta comprobar la instalación

[SQL inicial](../database/db_actividad.sql) define cinco tablas: `usuarios`, `perfiles_usuarios`, `eventos`, `solicitudes_equipo` y `participantes_evento`. Los modelos ya incluyen estructura IA, borradores, fechas de confirmación y metadatos de embeddings. Los participantes tienen unicidad por evento/usuario en SQL y ORM.

La migración `20261022_6a` agrega columnas IA faltantes y conserva filas existentes. Supone que las tablas base ya existen: no inicializa una base vacía. El arranque de FastAPI no crea ni modifica tablas.

**Estado observado en este equipo:** servicio `MySQL80` detenido y archivo `backend/.env` ausente. No se pudo inspeccionar el esquema ni filas de una instancia MySQL. Esto no demuestra que la base no exista; impide certificar que esté creada o actualizada. Las observaciones antiguas de otros documentos sobre una base vacía corresponden a otro momento/entorno.

Secuencia necesaria:

1. Iniciar MySQL y definir usuario/base de desarrollo.
2. Crear `backend/.env` desde `.env.example`; completar `DATABASE_URL` y generar `AUTH_SECRET` de al menos 32 caracteres.
3. Si la base es nueva, ejecutar el SQL inicial. Si ya tiene datos, respaldar e inspeccionar antes; el SQL de creación de tablas no es un actualizador idempotente.
4. Desde `backend/`, ejecutar `python -m alembic -c alembic.ini upgrade head`. En una base creada con el SQL también registra la revisión.
5. Verificar conexión, tablas/columnas, unicidad de participantes y versión Alembic.
6. Crear cuentas y proyectos de prueba sin datos personales reales para ensayar ambos lados de las recomendaciones.

MySQL con JSON es suficiente para este MVP. No se necesita una base vectorial para terminar el recorrido actual. Una tabla propia de roles y campos explícitos de tipo/rol de solicitud son mejoras posteriores pequeñas: hoy el rol y el tipo viajan dentro del mensaje y se reconstruyen por nombre, lo que hace frágiles los cambios de nombre y la validación.

## 5. Hallazgos que bloquean el cierre

### A. Calidad de extracción y normalización

Las pruebas unitarias usan respuestas simuladas del modelo. Una prueba real mostró que un contrato JSON válido puede omitir información importante:

- Entrada de evento: «Buscamos un desarrollador backend con Python obligatorio y SQL deseable para una aplicación web.»
- Resultado: rol `desarrollador backend`, pero listas de habilidades obligatorias y deseables vacías.
- Entrada de perfil: «Sé programar en Python y SQL. Quiero aprender Docker. Me interesa desarrollar aplicaciones web.»
- Resultado: habilidades `programar en Python` y `programar en SQL`; Docker quedó correctamente como área de mejora.

El motor compara términos completos normalizados y equivalencias explícitas. Su catálogo inicial incluye `UE5 → Unreal Engine 5`, pero `programar en Python` no coincide con `Python`. Los embeddings pueden aportar semejanza, pero no acreditan una habilidad obligatoria. Se necesita un pequeño conjunto de evaluación real, términos canónicos revisables y métricas de omisiones/atribuciones incorrectas. Mantener confirmación humana y no convertir intereses o aprendizaje en competencias.

El parser de eventos tiene correcciones para casos concretos como Blender, Unreal, Git y portero. Conviene conservar esos casos como regresiones y evaluar frases variadas antes de agregar más excepciones aisladas.

### B. Editar, confirmar y reintentar todavía no forman un recorrido completo

Los endpoints de confirmación/reintento existen, pero el mapper `mapPerfil` descarta `perfil_estado_ia` y el mapper de proyectos no expone `estado_ia` ni `requisitos_confirmados`. No hay botones de reintento de embedding en las páginas. El modal de edición de Isaac modifica roles/categoría sin revisar los requisitos estructurados; después del merge se invalidan para evitar evidencia obsoleta, pero el usuario necesita una pantalla para reconfirmarlos.

Cambio acotado recomendado: incluir estados en los mappers, un aviso de revisión pendiente y acciones de confirmar/reintentar usando las rutas existentes. Reutilizar los controles de requisitos de creación. Preservar el borrador anterior si hay varias ediciones antes de reconfirmar.

También revisar `CreateProjectPage`: la clave de reanálisis incluye título/descripción/integrantes, pero omite categoría, materia y fecha límite aunque estos datos se envían a interpretar. Cambiarlos puede reutilizar una sugerencia anterior sin nuevo análisis.

### C. Participación y roles requieren invariantes de servidor

La aceptación comprueba destinatario, pendiente y evento abierto, pero no comprueba cupo disponible ni si otro integrante cubrió ya el rol. La comprobación de rol ocupado al solicitar adhesión lee `cubiertoPor` del JSON almacenado; la ocupación real está en `participantes_evento` y la proyección de lectura no actualiza ese JSON. Se reprodujo mediante API con SQLite temporal: un evento de capacidad 2 aceptó dos solicitudes sucesivas para Backend y terminó con 3 personas contando al creador, con ambos nuevos participantes en el mismo rol. No requirió peticiones simultáneas.

El envío de invitación tampoco excluye de forma completa a miembros ya incorporados ni una adhesión pendiente en sentido contrario. Las consultas previas a insertar no protegen solas contra solicitudes simultáneas. La unicidad por evento/usuario evita parte de los duplicados de miembros, pero no resuelve cupos ni dos usuarios en el mismo rol.

Cambio acotado: centralizar validaciones de adhesión/invitación/aceptación en un servicio y hacer la transición dentro de una transacción, releyendo participantes y capacidad. Añadir casos de dos aceptaciones, equipo lleno, rol ocupado, solicitud inversa y cuenta que cambió de estado.

### D. Datos de demostración y promesas de la interfaz

- `PublicProfile.jsx` compara intereses con `currentUser` de `mockData`, incluso en pantallas reales de personas/perfiles. Hay que pasar el perfil del usuario autenticado.
- `RecommendationCard.jsx` también conserva comparaciones con ese usuario de demostración; su uso principal actual es demostrativo y no debe confundirse con las tarjetas reales del motor.
- `MeetingPage.jsx` usa un equipo fijo, horario fijo, muestra «Propuesta enviada» y navega a `/equipos/t1` sin petición HTTP. Debe implementarse o quedar claramente fuera del producto activo.
- `InviteModal.jsx` llama «Borrador de la IA» a un mensaje producido por una plantilla local. Corregir la etiqueta o conectar la generación si es un requisito.
- `StudentSearch` ofrece búsqueda por habilidad, pero `perfiles.py` aplica `q` a nombre/carrera. Su filtro de franja compara `tarde` con bloques como `lun-tarde` usando igualdad exacta y pierde coincidencias.
- Días, franjas y filtros comparten archivo con perfiles ficticios. Separar constantes de demostraciones aclara dependencias sin cambiar arquitectura.
- Las tarjetas de candidatos dicen estar agrupadas por rol, pero consumen una lista general por persona. Ajustar la presentación o implementar la agrupación con evidencia explícita.

### E. Operación y cobertura

Faltan pruebas de navegador y una verificación contra MySQL real. La suite actual usa SQLite; eso no prueba tipos JSON, fechas, índices y transacciones de MySQL. No hay flujo CI en el repositorio inspeccionado. Primero automatizar backend, build y lint; después añadir unos pocos recorridos de usuario críticos.

Las consultas de recomendaciones cargan todos los perfiles y eventos abiertos; notificaciones repite trabajo por evento. Para el volumen inicial puede ser suficiente. Medir y luego agregar filtros SQL, paginación y lecturas por lotes; no introducir colas/caché antes de resolver lo funcional. Llama y Nomic se ejecutan fuera del bucle async, pero la petición HTTP espera el resultado: no hay un trabajador persistente de procesamiento ni reintento automático.

## 6. Mejoras pequeñas de estructura

| Mejora | Lugar | Propósito |
| --- | --- | --- |
| Extraer constantes de días/franjas y filtros | `frontend/src/data/` | Evitar dependencia de datos ficticios en producto |
| Separar mappers y cliente HTTP de servicios por área cuando crezca | `frontend/src/services/api.js` | Mantener contratos visibles; conservar exports para no cambiar todas las páginas |
| Centralizar reglas de participación | Backend, servicio de equipos/solicitudes | Usar las mismas invariantes en invitación, adhesión y aceptación |
| Compartir revisión de requisitos entre crear y editar | Componentes de proyecto | Completar reconfirmación sin duplicar formularios |
| Unificar configuración de entorno | `core/config.py`, `services/ai/config.py`, DB y seguridad | Validar lo necesario al arrancar y evitar errores tardíos |
| Ordenar dependencias y documentación | `requirements.txt`, README y runbooks | Hay librerías de dos estrategias de contraseña; el código actual usa passlib/bcrypt. Limpiar solo después de revisar usos |
| Agregar CI con comprobaciones actuales | `.github/workflows/` | Detectar regresiones al integrar ramas |

No recomiendo migrar a TypeScript, cambiar de framework, separar microservicios, reemplazar MySQL ni rehacer el motor para cerrar esta etapa.

## 7. Plan de cierre y criterios de aceptación

1. **Entorno y BD.** Arranque reproducible desde un clon limpio, MySQL configurado, SQL/migración aplicados y cuentas ficticias. Termina cuando registro/login y consultas reales persisten tras reiniciar.
2. **Recuperación de IA.** Estados visibles, reconfirmación de proyecto editado, reintento de embeddings y borradores recuperables. Termina cuando apagar Ollama no pierde datos y encenderlo permite continuar desde la UI.
3. **Calidad del matching.** Evaluación real de extracción y normalización de habilidades/horarios. Termina cuando Python se acredita igual desde una etiqueta revisada y una frase equivalente, y Docker como aprendizaje nunca cuenta como competencia.
4. **Integridad del equipo.** Capacidad, rol ocupado y duplicados comprobados en servidor y transacción. Termina cuando dos aceptaciones concurrentes no sobrellenan el equipo ni duplican una vacante.
5. **Recorrido completo.** Tres cuentas: creador, candidato apto y candidato con datos insuficientes. Confirmar perfiles/consentimiento, publicar proyecto, consultar candidatos/proyectos, invitar o solicitar, aceptar, ver equipo y comprobar exclusión de miembros/pendientes. Repetir con perfil pausado, sin consentimiento y evento cerrado.
6. **Cierre de producto.** Sustituir comparaciones con usuario ficticio, corregir búsqueda y mensajes; decidir reuniones, feedback, cierre/baja del equipo, fotos e idiomas según alcance. Estas últimas funciones no son necesarias para que el matching funcione, pero no deben prometer persistencia si solo son demostraciones.

## 8. Verificación ejecutada

| Verificación | Resultado | Alcance |
| --- | --- | --- |
| Instalación frontend | `npm ci --ignore-scripts`: correcta; auditoría reportó cero vulnerabilidades | Dependencias del lockfile actual |
| Instalación backend | `pip install -r requirements.txt`: correcta | Se agregaron dependencias requeridas por la rama de Isaac al entorno local |
| Backend | `python -m pytest -q`: **194 passed** | Incluye seis regresiones nuevas del merge; SQLite y respuestas simuladas |
| Dependencias Python | `python -m pip check`: sin requisitos rotos | No valida configuración de servicios |
| Frontend | `npm run build`: correcto | No es prueba visual ni de recorrido HTTP |
| Lint | Cero errores; una advertencia previa en `RequireSession.jsx` | Dependencia del estado en `useEffect` |
| Ollama | API accesible; modelos `llama3.1:8b` y `nomic-embed-text:latest` instalados | Se consultaron e invocaron localmente |
| Perfil real | Primer intento agotó 40 s; repetición con timeout de ruta de 60 s respondió en 1.65 s | Una entrada ficticia; no demuestra calidad general ni identifica por sí sola la causa del timeout |
| Evento real | Respuesta en 2.84 s, con omisión de Python/SQL | Una entrada ficticia; requiere evaluación adicional |
| Nomic real | Embeddings de perfil y evento de 768 dimensiones | Generación real, sin persistencia MySQL |
| Invariantes de participación | Reproducido: capacidad 2, dos adhesiones aceptadas y 3 personas finales | SQLite temporal por API; no modifica datos reales |
| MySQL | Servicio detenido; `.env` ausente | No se crearon tablas ni se ejecutaron migraciones contra una instancia real |
| Git | Merge con ambos padres, sin conflictos pendientes; `git diff --check` correcto | Cambios locales, sin push |

La suite emite una advertencia de deprecación de Starlette sobre su integración de TestClient con httpx; no ocasionó fallos. Las auditorías del 22 de octubre son antecedentes, y sus afirmaciones de funcionalidad pendiente deben contrastarse con este estado integrado.
