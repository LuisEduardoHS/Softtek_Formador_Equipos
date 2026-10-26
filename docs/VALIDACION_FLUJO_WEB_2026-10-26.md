# Validación final del flujo web: perfil IA → candidatos → equipo

Seguimiento al encargo de comprobar el recorrido principal y publicar en la rama actual si funciona. Código validado: `0c1085b`, sobre `feat/ai-matching`. No fue necesario cambiar producción ni prompts adicionales: la extracción, los filtros y la confirmación humana conservaron correctamente las habilidades de estas entradas. Los límites del [informe amplio](QA_ESCENARIOS_REALES_MATCHING_2026-10-26.md) siguen vigentes; esta repetición no certifica todas las salidas posibles de Llama.

## Prueba visual y servicios reales

Se creó otra base vacía: **softtek_formador_equipos_qa_web_20261026_6a486f**, con el mismo DDL y revisión Alembic, sin copiar registros personales. React 5174 y FastAPI 8011 se ejecutaron separados de los servicios habituales. Se utilizaron MySQL 8.0.46, llama3.1:8b y nomic-embed-text reales. Tres pestañas independientes, tres registros desde React y ningún perfil insertado por ORM para sustituir el onboarding.

| Paso ejecutado | Resultado observado |
| --- | --- |
| Registro y perfil del organizador | Python, FastAPI y Git como fortalezas; aprender UX/UI queda separado |
| Registro y perfil SQL | «Sé programar con SQL», Git, «No sé Figma» y aprender Docker: SQL/Git como fortalezas, sin Figma ni Docker acreditados |
| Registro y perfil de diseño | UX/UI, Figma y prototipado preservados; «No sé SQL» no acredita SQL; Blender queda como aprendizaje |
| Creación de proyecto | Dos roles y capacidad total de tres; SQL/Figma obligatorios y Git deseable después de interpretar/revisar |
| Antes de confirmar candidatos | Cero recomendaciones: las sugerencias IA todavía no son evidencia confirmada ni tienen consentimiento |
| Confirmar SQL y activar recomendaciones | Aparece Persona #6; explicación acredita SQL/Git y deja Figma pendiente de verificar |
| Confirmar diseño y activar recomendaciones | Aparecen Persona #6 y Persona #7; la segunda explicación acredita Figma, sin inventar SQL |
| Recomendación inversa | El proyecto aparece en «Proyectos para ti» de ambos candidatos, con evidencia propia y estado Requiere revisión |
| Revisar perfil e invitar | Se abre el perfil real, se elige el rol y se confirma el diálogo de envío; la invitación SQL pendiente excluye a esa persona de candidatos |
| Aceptar desde otras sesiones | SQL se incorpora como especialista en bases de datos; diseño como diseñador UX/UI |
| Recargar equipo | Tres integrantes, dos roles cubiertos, habilidades SQL/Figma/Git cubiertas (3/3), ninguna por acreditar |
| Proyecto lleno | Ya no recomienda incorporaciones imposibles; muestra «No hay vacantes utilizables» |
| Otra convocatoria abierta | Los mismos dos perfiles siguen apareciendo para otro proyecto: participar en un equipo no excluye globalmente a la persona |

Las fortalezas se revisaron y se asignó nivel Intermedio antes de confirmar. Las habilidades de cada rol se indicaron en la revisión del proyecto. No se agregaron capacidades para hacer coincidir artificialmente perfiles ni se cambiaron pesos, umbrales o reglas del motor. Los especialistas conservan `needs_review` porque no acreditan individualmente todos los requisitos globales; no significa que hayan desaparecido de recomendaciones ni que la invitación esté prohibida.

## Evidencia

- [Dos candidatos reales recomendados en otra convocatoria abierta](qa_flujo_final_20261026/recomendaciones_visibles_otro_proyecto.png), [árbol de la interfaz del primer proyecto con sus explicaciones](qa_flujo_final_20261026/candidatos_ax.txt) y [cabecera del proyecto confirmado antes de invitar](qa_flujo_final_20261026/dos_candidatos_recomendados.png).
- [Cero antes de confirmar](qa_flujo_final_20261026/antes_de_confirmar_sin_candidatos.png), [primer candidato SQL](qa_flujo_final_20261026/primer_candidato_sql.png), [exclusión por invitación pendiente](qa_flujo_final_20261026/invitacion_pendiente_excluye_sql.png).
- Revisión IA: [organizador](qa_flujo_final_20261026/organizador_revision_ia.png), [SQL](qa_flujo_final_20261026/sql_revision_ia.png), [diseño](qa_flujo_final_20261026/diseno_revision_ia.png), [proyecto](qa_flujo_final_20261026/proyecto_revision_ia.png).
- Proyecto recomendado a [SQL](qa_flujo_final_20261026/proyecto_recomendado_sql.png) y [diseño](qa_flujo_final_20261026/proyecto_recomendado_diseno.png).
- [Equipo completo después de recargar](qa_flujo_final_20261026/equipo_completo_recargado.png) y [proyecto lleno](qa_flujo_final_20261026/proyecto_lleno_sin_recomendaciones_imposibles.png).
- [Verificación MySQL/HTTP y revisiones](qa_flujo_final_20261026/validation.json), [salidas crudas y tiempos del SDK](qa_flujo_final_20261026/service_trace.json), [pruebas automáticas](qa_flujo_final_20261026/checks.json).

Se hicieron **cuatro análisis generativos** (tres perfiles y un proyecto), todos al primer intento de IA: **5.921, 1.452, 2.032 y 2.677 s**. Cuatro POST de interpretación, cuatro llamadas SDK, todos HTTP 200: no reapareció la duplicación por StrictMode ni el 409 competidor. El recorrido principal generó cuatro embeddings Nomic reales; la convocatoria secundaria agregó otro: **cinco vectores**, todos de 768 dimensiones finitas y revisión vigente. No se usaron mocks para este recorrido.

El script final aprobó **33 comprobaciones dirigidas**, incluyendo filas reales, autenticación de las tres cuentas, permisos ajenos 403, equipos tras nueva sesión HTTP, revisiones de fuentes/vectores, exclusión después de aceptar y recomendaciones en otro proyecto. Son pasos de los recorridos, no 33 escenarios distintos. Estado QA final: tres usuarios, tres perfiles, **dos proyectos**, dos invitaciones aceptadas y dos filas de participantes; el creador completa los tres integrantes proyectados del primer proyecto.

La convocatoria secundaria «QA Final Vacantes abiertas» se publicó por HTTP usando como fixture los requisitos ya revisados del primer proyecto, con nueva clave de idempotencia; no se atribuye una segunda extracción Llama ni una segunda creación visual. Después se cerraron las sesiones previas, se hizo login desde React en una pestaña nueva y se recorrió Proyectos → Mis proyectos → Ver proyecto: ambas tarjetas se volvieron a mostrar, sin alterar el equipo anterior. [Respuesta del motor](qa_flujo_final_20261026/open_project.json). Un primer intento del script con clave no UUID fue rechazado correctamente con 422 sin crear el proyecto; se corrigió la clave del arnés, no la validación del backend.

Incidencia de preparación conservada: el middleware temporal copiado del laboratorio anterior autorizaba 5175 y rechazó el primer OPTIONS de registro en 5174 con 400. Se corrigió **solo ese script QA**, sin cambiar CORS de producción, y se repitió el registro. No hubo POST de registro previo a ese ajuste ni es un fallo de interpretación de IA. La [consola del organizador](qa_flujo_final_20261026/consola_organizador.json) conserva ese Failed to fetch; las consolas [SQL](qa_flujo_final_20261026/consola_sql.json), [diseño](qa_flujo_final_20261026/consola_diseno.json) y [nueva sesión](qa_flujo_final_20261026/consola_nueva_sesion.json) no capturaron errores. No se observaron nuevos errores de aplicación en el recorrido posterior.

## Suite repetida y seguridad de los datos

| Control | Resultado | Tiempo de proceso |
| --- | --- | --- |
| python -m pytest -q | 365 passed; pytest informa 32.15 s | 33.50 s |
| python -m pip check | Sin dependencias rotas | 0.47 s |
| npm test | 21 passed | 1.97 s |
| npm run build | Correcto | 0.99 s |
| npm run lint | Cero errores, una advertencia previa | 3.57 s |

Persisten la deprecación Starlette/httpx y la advertencia useEffect en RequireSession. Esta ejecución de npm test también registró un aviso WebSocket 24678 ocupado por los servidores de desarrollo/SSR; las 21 pruebas terminaron correctamente. Se conserva en el log y no se presenta como fallo de matching ni como advertencia eliminada. No se cambiaron tests para aprobar ni se añadió infraestructura.

**La base principal no fue alterada.** Conteos antes/después: usuarios 4/4, perfiles 4/4, eventos 1/1, solicitudes 0/0 y participantes 0/0. Checksums, DDL SHA-256 `fb8d8647973fdda177c17a2e4deabc571886f26ba2160e6055f8a12a52dd9128` y revisión `20261022_6a` coinciden. Todas las escrituras se limitaron a QA. No se activó consentimiento de personas reales; para que sus perfiles sean descubribles deben confirmarlos y activarlo voluntariamente.

Se cerraron las tres pestañas iniciales y la pestaña adicional de nueva sesión; se detuvieron únicamente los procesos QA de esta repetición. Los servicios habituales mantuvieron sus PID: 8000/43532, 5173/2108, 3306/9036 y 11434/10056. [Comprobación](qa_flujo_final_20261026/services_final.json). La base ficticia queda disponible para inspección.

Se registra esta evidencia en un commit de validación sobre `0c1085b`. El usuario autorizó expresamente el push a `origin/feat/ai-matching`; se comprueba avance directo y ausencia de secretos antes de publicar, sin force, merges ni cambio de rama. El resultado y hash final se comunican en la entrega.
