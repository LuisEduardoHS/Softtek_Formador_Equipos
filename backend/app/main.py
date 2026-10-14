from fastapi import FastAPI
from app.api.routes import engine
from app.models import usuario

usuario.Base.metadata.create_all(bind=engine)

app = FastAPI(title= "Plataforma de Formación de Equipos AI")

app.incluide_router(auth.router)
app.incluide_router(perfiles.router)

@app.get("/")
def root():
    return {"mensaje": "API funcionando correctamente"}