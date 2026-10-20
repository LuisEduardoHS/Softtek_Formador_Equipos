import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Cargar variables de entorno desde el archivo .env
load_dotenv()

# Obtener URL de conexión
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")

# Validar que la variable de entorno exista
if not SQLALCHEMY_DATABASE_URL:
    raise ValueError(
        "❌ Error: No se encontró DATABASE_URL en el archivo .env. "
        "Asegúrate de definirla (ej. DATABASE_URL=mysql+pymysql://root:password@localhost:3306/Aplicacion)"
    )

# Crear motor con verificación de conexión automática
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_pre_ping=True
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Inyecta una sesión de base de datos por petición HTTP y la cierra al finalizar."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()