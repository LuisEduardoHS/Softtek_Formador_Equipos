from fastapi import FastAPI
from app.api.routes.auth import router as auth_router
from app.api.routes.perfiles import router as perfil_router
from app.api.routes.eventos import router as eventos_router
from app.db.database import engine, Base
from app.models import usuario, evento  # Se importan los modelos para registrarlos en SQLAlchemy

# Crear las tablas en MySQL automáticamente si no existen
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="API Universitaria - Equipos e Inteligencia Artificial",
    description="Backend para autenticación, perfiles de usuario, convocatorias y formación de equipos.",
    version="1.0.0"
)

# Registrar los módulos de rutas
app.include_router(auth_router)
app.include_router(perfil_router)
app.include_router(eventos_router)

@app.get("/")
def read_root():
    return {"mensaje": "API Backend funcionando correctamente"}