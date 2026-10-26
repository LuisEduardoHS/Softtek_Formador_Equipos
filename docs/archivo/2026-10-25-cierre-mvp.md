# Cierre funcional del MVP: equipos e IA

Fecha: 25 de octubre de 2026. Rama: `feat/ai-matching`. Este documento actualiza los pendientes del diagnóstico [ESTADO_PROYECTO_2026-10-25.md](2026-10-25-estado-proyecto.md) dentro del alcance solicitado.

## Punto de partida y protección

El árbol estaba limpio en `59742f3`. Se verificó que el merge `696e2bc` tiene como padres `72eb733` y la punta de Isaac `f0c1c20`; no se repitió el merge ni se reemplazaron carpetas. Se creó el respaldo local `codex/backup-before-mvp-20261025`. Antes de editar pasaron 194 pruebas del backend, `pip check` y el build del frontend.

## Cambios implementados

### Participación e integridad de equipos

- Invitación, adhesión y aceptación aplican las mismas reglas en `team_rules.py`.
- Se bloquea el evento antes de consultar/modificar participantes o solicitudes. En MySQL se usan lecturas `FOR UPDATE` y se refresca la identidad ORM para evitar reutilizar una instantánea anterior de la sesión de autenticación. En SQLite se adquiere primero el bloqueo de escritura.
- La aceptación revalida destinatario, estado pendiente, creador actual, evento abierto, cuentas activas, perfil no pausado, membresía, capacidad y rol disponible dentro de la transacción que inserta al integrante y cambia el estado de la solicitud. Los errores deshacen toda la operación.
- La capacidad incluye al creador una sola vez aunque también exista una fila suya en participantes.
- Cada rol tiene una vacante por defecto. Se admite `vacantes` explícito de 1 a 8 dentro del JSON existente, sin tablas ni migraciones nuevas. Los nombres/IDs de roles deben ser únicos y el nombre cabe en la columna ORM de 50 caracteres.
- La ocupación procede de `ParticipanteEvento`; se ignoran las asignaciones `cubiertoPor` enviadas por el cliente. No se permite retirar/renombrar un rol ocupado ni reducir sus vacantes por debajo de los integrantes actuales.
- Se rechaza un par evento/persona que ya tenga una invitación o adhesión pendiente, en cualquiera de los dos sentidos. También se rechaza invitar a quien ya pertenece al equipo.
- El adaptador de recomendaciones conserva vacantes múltiples y deja de presentar un evento lleno como abierto para matching. Se mantienen el ranking y las explicaciones existentes.

### Edición, revisión humana y embeddings

- El modal de Isaac conserva categoría, roles, capacidad y fecha; permite editar la descripción y avisa que hay que revisar de nuevo los requisitos.
- Guardar invalida confirmación, requisitos públicos, vector y procedencia anteriores. Ediciones sucesivas conservan el último borrador revisado internamente; ese borrador no se publica como vigente.
- El detalle muestra el estado de IA y ofrece revisar requisitos actuales, interpretar de nuevo o introducir/corregir etiquetas manualmente. Se necesita una confirmación humana explícita antes de enviar al endpoint existente de confirmación.
- Una huella de la fuente detecta ediciones mientras el formulario está abierto; una revisión o edición con una huella anterior recibe 409. La UI recarga recomendaciones tras confirmar y oculta las candidaturas basadas en el análisis previo mientras falta revisión.
- Confirmar persiste los datos antes de intentar el embedding. Si Ollama falla, la UI muestra datos confirmados con análisis pendiente y un botón de reintento.
- La escritura del embedding es condicional a la revisión capturada antes del commit y a la confirmación vigente. Un resultado tardío no puede restaurar datos editados ni guardar un vector antiguo bajo la revisión de una confirmación más reciente. Un fallo tardío tampoco borra un reintento que ya tuvo éxito.
- Los reintentos usan los endpoints existentes y no convierten un perfil obsoleto en confirmado. Los bloqueos de revisión se liberan antes de esperar a Ollama.
- `mapPerfil` y `mapEventoAProyecto` conservan los estados necesarios. Perfil y proyecto muestran revisión pendiente, datos obsoletos, embedding pendiente y análisis listo. Se evita que una operación pendiente sobrescriba cambios hechos mientras el formulario está bloqueado.
- La clave de reanálisis al crear un proyecto ahora incluye todos los detalles del formulario.

### Extracción y normalización

- Se normalizan etiquetas afirmativas como `programar en Python`, `sé programar en Python`, `programación en SQL` y `programar en SQL` a sus tecnologías. El catálogo de equivalencias del motor se versionó como `2026-10-25.v2`.
- La extracción tiene una reparación acotada para menciones explícitas de Python/SQL: distingue requisitos obligatorios/deseables y habilidades declaradas frente a negaciones y aprendizaje.
- `no sé Python`, `no sé Python ni SQL`, `quiero aprender Python` y `Python no es obligatorio` no se convierten en competencias o requisitos obligatorios. Una negación confirmada con polaridad negativa conserva ese significado al evaluar matching.
- Una fortaleza enviada a confirmar como frase negativa o intención de aprendizaje se rechaza con un error claro. Las áreas de mejora siguen separadas de competencias.
- Se descarta el título del proyecto cuando el modelo lo copia como condición de participación; también se retiran negaciones de requisitos de Python/SQL colocadas incorrectamente como restricciones.
- Toda extracción sigue siendo una sugerencia hasta la revisión humana. Estas reglas no son un analizador general del español.

## Validación

- Suite final: **234 pruebas aprobadas**. Se añadieron 40 casos del MVP sobre la base de 194; una prueba anterior de carrera se actualizó para usar sesiones ORM reales.
- Casos nuevos: capacidad, creador contado una vez, rol único/múltiple, ocupación real frente a JSON, duplicados en ambos sentidos, cuentas/perfiles que cambian después del envío, respuesta repetida, rol retirado, edición/reconfirmación/reintento, equivalencias, negaciones y escrituras tardías de embeddings.
- Concurrencia con SQLite de archivo y conexiones independientes: dos aceptaciones para el último cupo, dos aceptaciones para una vacante única y creación simultánea de invitación/adhesión inversa. En cada caso termina una operación y la otra recibe 409, sin filas duplicadas ni equipo sobrellenado.
- `python -m pip check`: sin requisitos rotos.
- `npm run build`: correcto. `npm run lint`: cero errores; permanece la advertencia previa de dependencia de un hook en `RequireSession.jsx`.
- Navegador con BD temporal y cuenta ficticia: login, edición, invalidación, revisión, confirmación, fallo inicial simulado del embedding, reintento hasta listo, reintento de perfil y cambio `programar en SQL → SQL`. Sin errores en la consola del recorrido comprobado. Los embeddings de este smoke visual se simularon para reproducir de manera determinista el fallo/reintento; la interpretación del proyecto sí usó Ollama local.
- Ollama real, pruebas adicionales con textos ficticios: perfil con Python/SQL normalizados; evento con Python obligatorio y SQL deseable; negaciones sin competencias/requisitos positivos. No se escribieron datos personales reales.

## Límites y operación

1. No hay `backend/.env` en este checkout. En la observación final `MySQL80` está activo, pero no se dispone de una conexión configurada para comprobar tablas o ejecutar el recorrido contra MySQL. Las pruebas de concurrencia se ejecutaron en SQLite; queda por validar `FOR UPDATE`, aislamiento e índices sobre la instancia real con InnoDB. No se crearon/migraron tablas reales.
2. Preparar MySQL conforme al [README](../../README.md) y [runbook de 6A](../operacion/ia-perfiles-proyectos.md), incluyendo unicidad de participantes. El cambio no requiere columnas nuevas: usa el esquema y endpoints existentes. Las escrituras manuales fuera de estos endpoints deben respetar las mismas reglas.
3. Para eventos antiguos sin capacidad explícita se conserva una capacidad de ocho personas; los roles definidos tienen una vacante salvo `vacantes` explícito. Revisar configuraciones antiguas ambiguas antes de operar sobre ellas.
4. El contrato admite clientes anteriores que no envían `fuente_revision`; la interfaz actual sí la envía. Para obligar a clientes externos a usar control de revisión habrá que hacer el campo obligatorio tras migrarlos.
5. Ollama puede omitir datos o proponer etiquetas incorrectas fuera del vocabulario acotado. La confirmación humana permanece obligatoria. No se cambia la política del ranking ni se afirma que una coincidencia garantice idoneidad.
6. El tipo y rol de solicitud conservan el formato legado dentro del mensaje, generado por el servidor y con validación al aceptar; no se agregó una tabla de roles ni un nuevo modelo de solicitudes.
7. Reuniones, feedback, microservicios y reorganización general quedaron fuera del cambio. Los otros pendientes del diagnóstico, como búsqueda/catálogos o comparaciones heredadas en componentes demostrativos, siguen documentados y no se presentaron como resueltos.
8. Solo commits locales; sin push.
