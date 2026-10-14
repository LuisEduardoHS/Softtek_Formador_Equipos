from fastapi import FastAPI
from app.api.routes import auth
from app.db.database import engine, Base
from app.models import usuario

# Crear las tablas en MySQL automáticamente si no existen
usuario.Base.metadata.create_all(bind=engine)

app = FastAPI(title="API Universitaria - Módulo Auth")

# Registrar las rutas de autenticación
app.include_router(auth.router)

@app.get("/")
def read_root():
    return {"mensaje": "API Backend funcionando correctamente"}