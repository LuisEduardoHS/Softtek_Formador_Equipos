# Análisis de integración de IA con backend y frontend

Fecha: 21 de octubre de 2026. Rama examinada: `feat/ai-matching`, después de incorporar `origin/isaac` en `ece1ca0` (punta de Isaac: `46f59a2`). Este documento responde al mapa y las preguntas de integración del apartado 4 del plan maestro. Describe el código actual; las propuestas no están implementadas.

## 1. Estado general

La aplicación tiene tres capas identificables:

```text
frontend/src/pages y components
        -> frontend/src/services/api.js
        -> backend/app/api/routes/{auth,perfiles,eventos}.py
        -> backend/app/models + backend/app/db/database.py
        -> MySQL

backend/app/services/ai/{profile_parser,event_parser,embeddings}.py
        -> Ollama (llama3.1:8b y nomic-embed-text)
```

La última línea todavía no está conectada con las rutas. No hay endpoints de IA, ejecución automática al guardar ni persistencia de sus resultados desde el backend. La interfaz de IA tiene diseño y flujos de interacción, pero varias funciones de `api.js` devuelven datos vacíos simulados. La conexión real existente cubre registro, login, lectura de perfil y creación/lectura de eventos.

## 2. Qué existe en cada capa

| Capa | Archivos clave | Implementado | Pendiente o límite |
| --- | --- | --- | --- |
| Entrada API | `backend/app/main.py` | Registra routers, configura CORS para puertos locales y ejecuta `Base.metadata.create_all(bind=engine)` al importar. | Arranque depende de `DATABASE_URL` y de MySQL disponible. `create_all` no sustituye migraciones de cambios de esquema. |
| Autenticación | `backend/app/api/routes/auth.py`, `schemas/usuario.py` | `POST /auth/registro` y `POST /auth/login`; contraseña con bcrypt; registro crea perfil vacío. | Login devuelve identidad, sin token/sesión verificable por el servidor. |
| Perfil | `backend/app/api/routes/perfiles.py`, `schemas/perfil.py`, `models/usuario.py` | `GET /perfil/{usuario_id}` y `PUT /perfil/{usuario_id}`; el PUT combina campos de `PerfilUpdate` dentro de `datos_crudos`. | Ninguna llamada a IA ni campos IA en el ORM. No hay verificación de que el solicitante sea dueño del ID. |
| Eventos | `backend/app/api/routes/eventos.py`, `schemas/evento.py`, `models/evento.py` | `POST /eventos/`, `GET /eventos/`, `GET /eventos/{id_evento}`; consulta creador antes de crear. | No se procesa `descripcion_libre`; `requisitos_ia` llega del cliente y `embedding_requisitos` se inicia vacío. No hay edición de evento ni control de propiedad. |
| BD | `database/db_actividad.sql`, `backend/app/db/database.py` | SQL de `usuarios`, `perfiles_usuarios`, `eventos`, `solicitudes_equipo`, `participantes_evento`; conexión SQLAlchemy vía `DATABASE_URL`. | No hay migraciones versionadas. Las dos últimas tablas no tienen ORM/rutas. SQL y ORM de perfil difieren. |
| Frontend | `frontend/src/pages`, `components`, `services/api.js` | Pantallas de autenticación, perfil, proyecto y otras; llamadas HTTP reales para auth, GET perfil y eventos. | Interpretación IA, guardado final de perfil, matching, invitaciones y equipos continúan simulados o marcados TODO. |
| IA | `backend/app/services/ai` | `ProfileParser`, `EventParser`, esquemas Pydantic y generación de embeddings; pruebas unitarias. | No conoce la sesión de BD ni debe escribir directamente en ella. Las fallas semánticas IA-01 a IA-04 del plan siguen sin cerrar. |

## 3. Flujo real de datos y contratos

### Usuario y perfil

`AuthPage.jsx` usa `registrarUsuario`/`iniciarSesion` y guarda el objeto `usuario` en `localStorage`. `obtenerPerfil()` toma de allí `id_usuario` y llama a `GET /perfil/{id}`. En el asistente `ProfileSetupPage.jsx`, `interpretarPerfil(textos)` actualmente devuelve `{ fortalezas: [], reforzar: [], intereses: [] }`; al confirmar, la página muestra “Perfil guardado”, pero su función `confirm` no hace una petición de guardado.

El backend recibe en `PerfilUpdate` los campos `bio`, `habilidades`, `intereses`, `rol_preferido`, `disponibilidad_horaria` y `redes_sociales`. Los guarda como claves JSON en `perfiles_usuarios.datos_crudos`. `ProfileParser.parse_profile(description: str)` requiere una cadena, y devuelve `StructuredProfile` con `habilidades`, `intereses`, `areas_mejora`, `experiencia` y `resumen_publico`. **No hay equivalencia directa** entre el objeto `textos` del asistente, `PerfilUpdate` y `StructuredProfile`: hace falta un adaptador explícito y decidir qué texto conserva el usuario como fuente original.

El SQL de `perfiles_usuarios` declara `nombre_mostrar`, `resumen_publico_ia`, `perfil_estructurado_ia` y `embedding_perfil`; el ORM `PerfilUsuario` solo declara `usuario_id`, `datos_crudos` y `atributos_dinamicos`. La capa de persistencia debe alinearse con el esquema real antes de intentar guardar los resultados de IA. No asumir que `create_all` agregará columnas a tablas existentes.

### Evento o proyecto

`CreateProjectPage.jsx` llama a `interpretarProyecto(form)`, que hoy devuelve `{ roles: [] }`, y luego `crearProyecto`. Esta última función sí envía `POST /eventos/` con `titulo`, `descripcion_libre`, `categoria_principal`, `detalles_especificos` (incluye roles, materia, integrantes y fecha) y `requisitos_ia: { roles }`. Los listados y el detalle usan `GET /eventos/` y `GET /eventos/{id}`.

`EventParser.parse_event(descripcion_libre, categoria_principal=None, detalles_especificos=None)` devuelve `StructuredEventRequirements` con requisitos, roles buscados, restricciones, título y resumen. El formato actual de `requisitos_ia: { roles }` del frontend **no coincide** con ese esquema: son roles de interfaz escritos por el usuario, no salida verificada del parser. Conviene mantener esos roles en `detalles_especificos` y reservar `requisitos_ia` para el resultado generado y confirmado, con una traducción clara para la UI. `embedding_requisitos` está tipado como JSON en ORM/SQL, pero `EventoOut` lo presenta como diccionario; la función de IA devuelve `list[float]`. Hay que acordar ese contrato antes de persistir y exponer vectores.

### Identidad y seguridad

El navegador guarda un ID en `localStorage`, que se usa como `creador_id` y en la URL del perfil. El backend comprueba que el ID exista, pero no demuestra que quien hace la petición sea ese usuario. Para cualquier escritura de perfil, evento o resultado de IA, la identidad debe venir de una sesión/token validado por el servidor. Mientras no exista, no debe tratarse el ID del navegador como autorización. También conviene definir qué campos de perfil pueden verse públicamente; `PerfilOut` incluye correo y `datos_crudos`.

## 4. Cómo aplicar lo ya construido de IA

La separación actual de servicios es útil: los parsers reciben texto y retornan objetos validados, y los embeddings reciben esos objetos. La integración debería hacerse en una capa backend que coordine rutas, servicios y persistencia, sin introducir acceso a MySQL en `app/services/ai`.

### Propuesta de flujo de perfil

1. El frontend envía respuestas originales de perfil a una ruta autenticada y recibe un análisis preliminar; la ruta adapta esas respuestas a un texto fiel para `ProfileParser`.
2. La UI presenta campos interpretados que el usuario pueda corregir. Definir una traducción estable entre `habilidades`/`areas_mejora` y `fortalezas`/`reforzar`, sin inventar niveles o experiencia.
3. Tras confirmación, el backend guarda los datos originales en `datos_crudos` y el análisis validado en los campos IA acordados. Genera el embedding desde el perfil confirmado, no desde datos obsoletos.
4. Un cambio posterior al texto o a los campos confirmados debe marcar el análisis/vector como desactualizado y regenerarlo de forma controlada.

### Propuesta de flujo de evento

1. El frontend conserva `titulo`, `descripcion_libre`, categoría, detalles y roles declarados por el organizador. Esos roles no son una salida de IA.
2. Una ruta autenticada obtiene la descripción y detalles, llama a `EventParser` y devuelve requisitos interpretados para revisión. Decidir si esto ocurre antes de publicar, después o por solicitud explícita.
3. Tras confirmación, el backend persiste el evento, los requisitos estructurados y el vector generado por `generate_event_embedding` de forma consistente. La respuesta para la UI traduce requisitos a su modelo de roles sin sobrescribir los declarados.
4. Si Ollama está apagado o excede el tiempo acordado, conservar el borrador original y mostrar un estado de procesamiento/error; no presentar un resultado vacío como análisis exitoso.

**Estos flujos son diseño propuesto, no endpoints existentes.** Las rutas, códigos de estado, tiempos de espera y si se usa trabajo diferido deben acordarse con los responsables de backend/frontend. El parser de eventos aún tiene los casos IA-02, IA-03 e IA-04 pendientes de corrección; no conviene almacenar su salida como verdad aprobada sin revisión.

## 5. Cambios necesarios antes de declarar integración completa

### Prioridad alta: contratos y persistencia

- Acordar JSON de entrada y salida para el asistente de perfil y el formulario de proyecto. Definir quién es dueño de cada campo y cuáles son datos del usuario frente a inferencias IA.
- Alinear SQL y ORM de perfil; definir tipo y representación de embeddings (`list[float]`, dimensión 768), versión del modelo, momento de generación y estado de procesamiento. Usar una migración para BD ya creada.
- Evitar que `requisitos_ia` suministrado por el cliente se confunda con resultados producidos por el servidor. Separar roles declarados de requisitos interpretados.
- Añadir autenticación/autorización real para perfiles y eventos antes de persistir análisis asociado a un usuario.

### Prioridad media: operación y experiencia

- Implementar la llamada de guardado real de `ProfileSetupPage.jsx`, luego conectar interpretación y confirmación con los contratos acordados.
- Decidir procesamiento síncrono o diferido según latencia de `llama3.1:8b` y `nomic-embed-text`; definir timeout, reintento, errores visibles e idempotencia.
- Controlar CORS y configuración de URL por entorno; `api.js` usa `VITE_API_URL` o `http://127.0.0.1:8000`.
- Revisar si el producto debe exigir `usuarios.carrera` y usar `rol_sistema="Estudiante"` por defecto, dado el alcance multitemático del plan.

### Posterior, fuera de esta integración inicial

- Matching por complementariedad, recomendaciones, solicitudes, invitaciones y equipos. Las pantallas y tablas sugieren esos módulos, pero los endpoints y la lógica no están implementados.
- Corregir y revalidar IA-01 a IA-04 antes de considerar aprobadas las fases 2 y 3; las 40 pruebas actuales no prueban fidelidad semántica real.

## 6. Orden recomendado de trabajo

1. Reunir a responsables de frontend, backend, BD e IA para fijar contratos de perfil y evento con ejemplos JSON reales o sintéticos.
2. Alinear BD/ORM y migraciones, identidad/autorización y responsabilidades de campos.
3. Conectar primero guardado de perfil y creación de evento con datos originales, verificando lectura posterior; después añadir análisis preliminar y confirmación.
4. Integrar parser y embeddings detrás de rutas/servicio backend con estados de error claros; probar con Ollama disponible e indisponible.
5. Corregir las regresiones semánticas del plan y medir respuestas reales repetidas antes de activar persistencia automática o recomendaciones.

## 7. Verificación y límites de este análisis

Se revisaron rutas, esquemas, modelos, SQL, componentes de los flujos de perfil/proyecto y `frontend/src/services/api.js`. Tras el merge, `backend/.venv/Scripts/python.exe -m pytest tests -q` dio **40 passed**. `npm run build` falló porque la instalación local de `node_modules` carece de `react-router-dom`, aunque figura en `package.json`; esto no prueba un defecto del código con dependencias instaladas. `npm run lint` reportó 32 errores de variables/importaciones sin uso y una advertencia. No se levantó MySQL ni Ollama, no se ejecutaron flujos HTTP completos y no se editaron archivos de la aplicación para este documento.
