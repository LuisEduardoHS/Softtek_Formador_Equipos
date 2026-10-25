# Formador de Equipos (Softtek / Complementa)

Plataforma para crear equipos mediante perfiles, convocatorias y recomendaciones con IA.

El [diagnóstico del 25 de octubre de 2026](docs/ESTADO_PROYECTO_2026-10-25.md) describe el estado integrado, las comprobaciones realizadas y el plan de cierre.

## Requisitos

- Python 3.10 o superior.
- Node.js LTS y npm.
- MySQL activo y una base de desarrollo configurada.
- Ollama con `llama3.1:8b` y `nomic-embed-text` para interpretar textos y generar embeddings.

## Backend

Desde `backend/`, en PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

La copia del archivo de entorno se hace solo en la configuración inicial. Completar `DATABASE_URL` y `AUTH_SECRET` en `.env`. Para generar un secreto:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Para una base nueva, ejecutar primero [database/db_actividad.sql](database/db_actividad.sql) con un cliente MySQL. Para una existente, respaldar e inspeccionar el esquema antes de migrar; el SQL inicial no actualiza tablas existentes.

Desde `backend/`, con el entorno activo y la estructura base disponible:

```powershell
python -m alembic -c alembic.ini upgrade head
uvicorn app.main:app --reload
```

La migración actual añade columnas IA a tablas existentes. FastAPI no crea las tablas al arrancar. En ejecuciones posteriores solo es necesario activar el entorno y arrancar el servidor. Documentación de la API: [Swagger local](http://127.0.0.1:8000/docs).

## Frontend

Desde `frontend/`:

```powershell
npm ci
npm run dev
```

La API usa `http://127.0.0.1:8000` por defecto; puede configurarse con `VITE_API_URL`. Utilizar la dirección que muestre Vite al arrancar.

## Comprobaciones

Desde `backend/`, con el entorno activo:

```powershell
python -m pytest -q
python -m pip check
```

Desde `frontend/`:

```powershell
npm run build
npm run lint
```

La suite usa SQLite y respuestas simuladas para las pruebas automáticas de API/IA. La validación con MySQL y los modelos locales es adicional.

## Guías

- [Estado actual y pendientes](docs/ESTADO_PROYECTO_2026-10-25.md).
- [Operación de perfiles y proyectos con IA](docs/RUNBOOK_FASE6A.md).
- [Operación de recomendaciones](docs/RUNBOOK_FASE6B.md).

Las recomendaciones necesitan perfiles revisados, consentimiento explícito y eventos abiertos. Pueden trabajar con evidencia declarada aunque un embedding esté pendiente. Reuniones y algunos elementos heredados siguen siendo demostraciones; consultar el diagnóstico antes de considerarlos implementados.
