# Operación de recomendaciones, invitaciones y equipos

Requisitos: [perfiles y proyectos revisados](ia-perfiles-proyectos.md), autenticación válida y una base configurada. Ensayo completo: [guía manual](../pruebas-manuales/guia-completa.md). Evidencia y límites: [escenarios reales](../qa/informes/2026-10-26-escenarios-matching.md).

## Para que aparezcan candidatos

1. El organizador debe ser el creador autenticado del proyecto.
2. El proyecto debe estar abierto, con capacidad y al menos una vacante de rol utilizable.
3. Cada persona debe confirmar su perfil y activar Recomendaciones; cuenta activa y perfil sin pausa.
4. Solo las habilidades confirmadas y permitidas acreditan requisitos; texto pendiente, intereses y aprendizaje no acreditan competencias.
5. Se excluyen creador, miembros del mismo proyecto y personas con invitación/solicitud pendiente para ese proyecto.
6. Actualizar candidatos o recargar después de confirmar perfiles, cambiar permisos o aceptar invitaciones.

En el caso real «Gestor de tareas inteligente» se comprobó un vacío correcto por falta de consentimiento de los otros perfiles. No se habilita ese consentimiento automáticamente. La UI explica el vacío sin divulgar identidades ni cantidades de perfiles ocultos.

## API y explicaciones

| Ruta | Quién / qué devuelve |
| --- | --- |
| GET /recomendaciones/eventos/{id}/candidatos?top_n=10 | Solo creador; candidatos del motor existente |
| GET /recomendaciones/usuarios/{id}/proyectos?top_n=10 | Solo titular con consentimiento; proyectos visibles recomendados |
| GET /notificaciones/{id} | Solo titular; actividad e invitaciones, con sugerencias recalculadas cuando corresponda |
| GET /equipos/{id} | Solo titular; equipo desde participantes reales y creador |

`top_n` admite 1–20. Los DTO del motor contienen identificadores, elegibilidad, cobertura de evidencia, explicación y versión de política; omiten JWT, contraseñas, vectores y puntuaciones internas. Los nombres se consultan mediante el perfil público autorizado; por eso una tarjeta puede titularse «Persona #…».

`Requiere revisión` significa que faltan hechos para confirmar requisitos, no que la persona esté automáticamente rechazada. No exigir un orden exacto por nombre o ID. La política actual puede colocar evidencia parcial antes que otra capacidad; los requisitos globales se revisan por persona y el rol se elige manualmente. Las restricciones horarias exactas no se deducen de un bloque «tarde».

## Invitaciones, adhesiones y aceptación

- Invitación del creador: `POST /invitaciones/?de_id=...`, con destinatario, evento y rol esperado. La UI abre un diálogo; pulsar «Invitar» no basta, hay que confirmar «Enviar invitación».
- Solicitud de incorporación: `POST /eventos/{id}/solicitudes?solicitante_id=...`, con rol y mensaje. Solo el propio solicitante.
- Respuesta: `PATCH /invitaciones/{id_solicitud}` por el destinatario. En una invitación se incorpora el destinatario candidato; en una adhesión aceptada se incorpora el remitente solicitante.
- Aceptación revalida cuenta, pausa, estado del evento, capacidad, membresía, vacante y duplicados bajo bloqueo del evento. Puede responder 409 si las condiciones cambiaron.
- Un cupo no se reserva por mirar una recomendación ni por enviar una solicitud. Dos respuestas por el último cupo no deben superar la capacidad.

La capacidad total incluye al creador. Una vacante por rol es el valor inicial de la UI; la API soporta `vacantes` explícito para varias plazas. Rol ocupado y habilidades cubiertas son cosas diferentes: una persona puede declarar portero y defensa pero ocupar una sola vacante asignada.

## Cobertura, edición y persistencia

El equipo se calcula desde MySQL. La cobertura utiliza requisitos confirmados y evidencia permitida de los miembros; no representa evaluación profesional ni compatibilidad horaria. Sin información suficiente se muestra desconocida; 0/0 no demuestra cobertura completa de requisitos globales que aún existan.

Editar el proyecto invalida requisitos y vector. No interpretar datos antiguos como actuales: revisar, confirmar y después reintentar Nomic si hace falta. Preservar roles de integrantes existentes; no reducir capacidad por debajo del equipo actual. Las membresías permanecen después de recargar o volver a iniciar sesión.

Reuniones no están disponibles en este MVP. Una pantalla no debe simular un envío persistido. Directorio, Inicio, Coincidencias, detalle, Invitaciones y Equipos usan datos reales en los recorridos autenticados; la landing y el catálogo visual mantienen demostraciones identificadas.
