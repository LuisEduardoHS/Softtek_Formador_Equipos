# Complementa — Formador de Equipos (Softtek)

Aplicación web para formar equipos a partir de lo que cada persona sabe hacer y de las vacantes de un proyecto. Permite describir habilidades en lenguaje natural, revisar la interpretación de IA, publicar proyectos y obtener recomendaciones explicadas para encontrar colaboradores de distintas áreas: software, diseño, videojuegos, deporte y proyectos generales.

El flujo del MVP es **registro → perfil con IA → revisión y consentimiento → proyecto → recomendaciones → invitación o solicitud → aceptación → equipo persistido**. React conserva el diseño integrado de Isaac; FastAPI verifica la identidad con JWT y guarda perfiles, proyectos, solicitudes y participantes en MySQL. Ollama ejecuta `llama3.1:8b` para extracción y `nomic-embed-text` para embeddings. El motor combina hechos confirmados y evidencia disponible; una similitud semántica no acredita por sí sola una habilidad.

## Qué puedes hacer

- Crear y editar un perfil; revisar fortalezas, aprendizaje, intereses, experiencia y resumen público antes de confirmar.
- Decidir si apareces en recomendaciones y qué campos compartes; pausar tu perfil.
- Publicar proyectos con roles, capacidad y requisitos obligatorios/deseables.
- Consultar candidatos como organizador y proyectos recomendados como participante, con razones y datos pendientes de verificar.
- Invitar, solicitar incorporación, aceptar/rechazar y consultar miembros, roles y cobertura del equipo.
- Editar un proyecto, reconfirmar la IA y reintentar un embedding pendiente.

Reuniones y feedback avanzado quedan fuera del MVP. Las recomendaciones requieren consentimiento y confirmación; `Requiere revisión` indica evidencia incompleta y no garantiza que una persona cumpla todos los requisitos. La disponibilidad exacta por horas requiere revisión humana.

## Requisitos locales

Entorno con el que se validó el proyecto el 26 de octubre de 2026:

| Herramienta | Referencia validada |
| --- | --- |
| Git | Cliente instalado y acceso al repositorio |
| Python | 3.13; las dependencias están fijadas en `backend/requirements.txt` |
| Node.js / npm | 24 / 11, con lockfile en frontend |
| MySQL | 8, con servicio activo y permiso sobre la base elegida |
| Ollama | Servicio local y modelos `llama3.1:8b` / `nomic-embed-text` |

Las instrucciones siguientes usan **PowerShell en Windows**. No necesitas Docker para el arranque descrito.

## 1. Clonar

Desde la carpeta donde guardas proyectos:

```powershell
git clone --branch feat/ai-matching https://github.com/LuisEduardoHS/Softtek_Formador_Equipos.git
Set-Location Softtek_Formador_Equipos
git branch --show-current
```

La salida debe ser `feat/ai-matching`, la rama que contiene este MVP. Si ya tienes el repositorio clonado, comienza por la configuración que te falte; conserva tus cambios y tu `.env` existente.

## 2. Preparar backend y configuración (primera vez)

Desde la raíz del repositorio:

```powershell
Set-Location backend
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
.\.venv\Scripts\python.exe -c "import secrets; print(secrets.token_urlsafe(48))"
```

Guarda el valor generado como `AUTH_SECRET` en `backend/.env`. Completa también la conexión con **tus** credenciales; este bloque es una plantilla, no una cuenta existente:

```dotenv
DATABASE_URL=mysql+pymysql://TU_USUARIO:TU_CLAVE@127.0.0.1:3306/Aplicacion
# Pegar aquí el secreto aleatorio generado arriba.
AUTH_SECRET=
OLLAMA_HOST=http://127.0.0.1:11434
OLLAMA_LLM_MODEL=llama3.1:8b
OLLAMA_EMBEDDING_MODEL=nomic-embed-text
```

`AUTH_SECRET` debe ser aleatorio y tener al menos 32 caracteres. No publiques `.env`. Si la contraseña de MySQL contiene caracteres reservados de URL, codifícalos para la cadena de conexión. Usar el ejecutable `.venv\Scripts\python.exe` evita depender de activar scripts de PowerShell.

### Base nueva

1. Inicia MySQL y abre una conexión con MySQL Workbench u otro cliente.
2. Ejecuta [database/db_actividad.sql](database/db_actividad.sql) **una sola vez en una instalación nueva**. El archivo crea y selecciona `Aplicacion`, y crea las cinco tablas: usuarios, perfiles, eventos, solicitudes y participantes.
3. Si quieres otro nombre, cambia las dos primeras instrucciones (`CREATE DATABASE` y `USE`) en una copia del SQL y utiliza el mismo nombre en `DATABASE_URL`.
4. Desde `backend/`, registra/aplica la revisión de IA sobre esa base:

```powershell
.\.venv\Scripts\python.exe -m alembic -c alembic.ini upgrade head
.\.venv\Scripts\python.exe -m alembic -c alembic.ini current
```

La revisión esperada es `20261022_6a`. La migración agrega columnas de IA que falten; no crea desde cero las tablas de negocio. FastAPI tampoco crea tablas al arrancar.

### Base ya existente

No vuelvas a ejecutar el SQL inicial para reinstalar tablas. Conserva la conexión existente y verifica esquema y revisión antes de migrar, con respaldo si corresponde. Si la base ya tiene las columnas y está en `20261022_6a`, no requiere inicialización adicional. No uses `stamp` para ocultar diferencias de esquema. Para las pruebas ficticias, utiliza la [preparación de QA aislada](docs/pruebas-manuales/guia-completa.md#preparacion).

## 3. Preparar Ollama (primera vez)

Con Ollama instalado e iniciado:

```powershell
ollama pull llama3.1:8b
ollama pull nomic-embed-text
ollama list
```

La descarga puede tardar y requiere espacio para los modelos. Si Ollama no está ejecutándose, inicia su aplicación o ejecuta `ollama serve` en otra terminal. No lances un segundo servicio si ya está escuchando en 11434. Comprueba el servicio con:

```powershell
Invoke-RestMethod http://127.0.0.1:11434/api/tags
```

## 4. Instalar frontend (primera vez)

En otra terminal, desde la raíz:

```powershell
Set-Location frontend
npm ci
```

El cliente usa `http://127.0.0.1:8000` como API por defecto. Si necesitas otra API, define `VITE_API_URL` antes de arrancar Vite; no confundas el backend habitual con el de QA.

## 5. Iniciar un proyecto ya clonado y configurado

Inicia MySQL y Ollama. Mantén dos terminales abiertas desde la raíz del repositorio; usa terminales nuevas si antes definiste variables de conexión para QA:

**Terminal backend:**

```powershell
Set-Location backend
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

**Terminal frontend:**

```powershell
Set-Location frontend
npm run dev -- --host 127.0.0.1 --port 5173 --strictPort
```

Abre [la web](http://127.0.0.1:5173) y, si necesitas inspeccionar contratos, [Swagger](http://127.0.0.1:8000/docs). Si el puerto está ocupado, comprueba si el servicio ya está iniciado. Cierra estos servidores con `Ctrl+C` en sus propias terminales.

No necesitas recrear el entorno, reinstalar paquetes, descargar modelos ni inicializar MySQL en cada arranque. Tras cambios de dependencias, vuelve a instalar las del componente afectado; las migraciones solo se aplican si hay revisiones nuevas pendientes. Las sesiones JWT duran ocho horas y la identidad se conserva por pestaña.

## Probar el flujo con datos completos

Abre la **[guía manual: 12 perfiles, 5 proyectos y recorridos](docs/pruebas-manuales/guia-completa.md)**. Contiene datos para cada campo, correcciones de revisión, resultados esperados, invitaciones/adhesiones, privacidad, edición y recuperación. No hace falta inventar usuarios ni utilizar datos personales.

Para ver candidatos, cada persona debe confirmar su perfil, activar Recomendaciones y mantenerlo sin pausa. El proyecto debe tener vacantes utilizables. Miembros del mismo proyecto y personas con una acción pendiente se excluyen; un listado vacío puede ser correcto.

## Comprobaciones de desarrollo

Desde `backend/`:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m pip check
```

Desde `frontend/`:

```powershell
npm test
npm run build
npm run lint
```

La última validación de código registró **367 pruebas backend y 27 frontend aprobadas**; consultar el [caso de consentimiento](docs/qa/informes/2026-10-26-consentimiento-candidatos.md) y la [evidencia del flujo completo](docs/qa/informes/2026-10-26-flujo-web.md) para distinguir SQLite/mocks de MySQL/Ollama/navegador. Pasar la suite no sustituye un recorrido real ni garantiza toda salida de Llama.

## Estructura y documentación

```text
backend/        API, modelos ORM, migraciones, IA y pruebas
frontend/       React, pantallas, contratos HTTP y pruebas
database/       SQL de inicialización para bases nuevas
docs/
  operacion/         Contratos y operación actuales
  pruebas-manuales/  Datos y pasos para probar la web
  qa/                Seguimiento, informes y evidencias fechadas
  arquitectura/      Diseños de referencia del motor
  archivo/           Diagnóstico y cierre históricos
```

El [índice de documentación](docs/README.md) es el punto de entrada. Para resolver problemas de arranque/estados IA consulta [perfiles y proyectos](docs/operacion/ia-perfiles-proyectos.md); para candidatos vacíos, vacantes y equipos, [recomendaciones y equipos](docs/operacion/recomendaciones-equipos.md).
