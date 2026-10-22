from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes.auth import router as auth_router
from app.api.routes.perfiles import router as perfil_router
from app.api.routes.eventos import router as eventos_router
from app.api.routes import solicitudes
from app.api.routes import notificaciones

app = FastAPI(
    title="API Universitaria - Equipos e Inteligencia Artificial",
    description="Backend para autenticación, perfiles de usuario, convocatorias y formación de equipos.",
    version="1.0.0"
)

# Configuración de CORS incluyendo el puerto 5174
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registrar los módulos de rutas
app.include_router(auth_router)
app.include_router(perfil_router)
app.include_router(eventos_router)
app.include_router(solicitudes.router,tags=["Invitaciones y Equipos"])
app.include_router(notificaciones.router)

@app.get("/")
def read_root():
    return {"mensaje": "API Backend funcionando correctamente"}
