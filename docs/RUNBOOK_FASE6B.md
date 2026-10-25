# Fase 6B MVP: recomendaciones conectadas

## Requisitos previos

Seguir `RUNBOOK_FASE6A.md`: configurar `DATABASE_URL` y `AUTH_SECRET`, aplicar la revisión Alembic `20261022_6a` con respaldo previo y arrancar FastAPI, MySQL y React. Esta fase no cambia el esquema ni necesita Ollama en tiempo de consulta. El motor usa hechos confirmados aunque falten embeddings; solo usa un vector cuando modelo, pipeline y revisión de origen son válidos. La suite automatizada usa SQLite temporal.

Cada persona debe confirmar su perfil y activar **Recomendaciones** de manera explícita. El valor inicial es desactivado. Un perfil pausado, una cuenta inactiva o un perfil sin consentimiento queda fuera de las sugerencias a organizadores. Las habilidades vienen del perfil confirmado; las áreas de mejora nunca acreditan competencias. Requisitos de evento sin confirmación del creador permanecen desconocidos.

## API y operación

- `GET /recomendaciones/eventos/{id_evento}/candidatos?top_n=10`: Bearer del creador del evento. `top_n` acepta 1 a 20. Omite creador, integrantes, solicitudes e invitaciones pendientes, perfiles ocultos y candidatos inelegibles.
- `GET /recomendaciones/usuarios/{id_usuario}/proyectos?top_n=10`: Bearer del mismo usuario. Omite eventos cerrados, propios, donde participa o con acción pendiente. Requiere consentimiento del perfil.
- Ambas respuestas contienen identificadores, `eligibility`, `evidence_group`, cobertura, explicación y versión de política. No contienen nombres, correo, vectores, puntuaciones ni datos crudos. `needs_review` y `insufficient_evidence` se muestran como tales; una coincidencia no autoriza ni ejecuta invitaciones.
- `GET /notificaciones/{id_usuario}` conserva invitaciones y actividad de equipo. Las sugerencias IA se calculan con `recommend_candidates`; no hay un algoritmo textual paralelo. Se recalculan al leer, sin mensajes persistidos, colas ni cron.

React consulta los endpoints con la sesión validada, muestra carga, vacío y error en Inicio, Coincidencias y candidatos del proyecto. Para invitar, el organizador debe revisar perfil y rol. La ruta de invitaciones vuelve a validar propietario, estado abierto, destinatario activo/no pausado y duplicado pendiente. Antes de cualquier nueva acción de escritura, revalidar permisos, membresía, consentimiento y estado contra la base: el resultado consultado puede quedar obsoleto entre lectura y uso.

## Verificación

Desde `backend/`, con el entorno virtual activo: `python -m pytest -q` y `python -m pip check`. Desde `frontend/`: `npm run build`. Las pruebas HTTP usan una base SQLite temporal, tokens de prueba, perfiles confirmados y eventos; comprueban 401/403, top N, exclusiones, privacidad, ausencia de vectores, datos no confirmados y notificaciones.

Para un smoke de MySQL **sin escribir datos**, una vez configurada `DATABASE_URL` y aplicada la migración de 6A, ejecutar desde `backend/`:

```powershell
python -c "from sqlalchemy import text; from app.db.database import engine; c=engine.connect(); print(c.execute(text('SELECT 1')).scalar()); c.close()"
```

Después iniciar sesión con una cuenta de prueba, confirmar perfil/consentimiento y consultar ambos endpoints con su Bearer. Usar un evento propio abierto y hechos confirmados; comprobar que otro actor recibe 403 en candidatos y que la respuesta carece de `profile_embedding` y `ranking_score`. No compartir token ni cadena de conexión en logs o capturas. La observación original de esta entrega encontró una base sin tablas. En la revisión del 25 de octubre de 2026, este equipo tiene `MySQL80` detenido y no dispone de `backend/.env`; no se verificó el esquema real. Consultar el [diagnóstico actualizado](ESTADO_PROYECTO_2026-10-25.md) y preparar la estructura siguiendo 6A antes del smoke contra MySQL.

## Límites del MVP

La adaptación ORM lee instantáneas por solicitud y las notificaciones recalculan por evento; puede requerir paginación/caché cuando crezca la base. No hay generación Llama durante la consulta ni explicación generativa. Un evento o perfil legado sin confirmación da evidencia desconocida; no se promueve el texto libre ni la salida IA pendiente. La interfaz del detalle de proyecto mantiene otros elementos heredados, pero las recomendaciones visibles proceden del motor y las invitaciones pendientes del servidor.

La integración del 25 de octubre incorpora el endpoint de adhesión de Isaac: `POST /eventos/{id_evento}/solicitudes?solicitante_id=...`, con Bearer del solicitante y un cuerpo con `rol_esperado` (ID del rol) y `mensaje_explicacion`. La respuesta se gestiona desde `PATCH /invitaciones/{id_solicitud}` por el destinatario creador; la aceptación incorpora al remitente solicitante. La UI ya usa esta ruta y distingue adhesiones de invitaciones.

La edición usa `PUT /eventos/{id_evento}?usuario_id=...`, con Bearer del creador. Conserva las cinco categorías y comprueba integrantes y roles ya asignados. Invalida requisitos confirmados y embeddings anteriores; queda pendiente completar la revisión/reconfirmación desde el modal. Las comprobaciones de cupo y ocupación al aceptar, y los duplicados en ambos sentidos, siguen siendo pendientes descritos en el diagnóstico.
