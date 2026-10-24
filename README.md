
-------------------- Backend-----------------------------

# Crear el entorno virtual si es la primera vez que se ejecutara el proyecto
python -m venv venv

# activar el entorno virtual para la instalacion de los requerimientos con los que trabaja la app
.\venv\Scripts\Activate.ps1

# Dentro de la carpeta /Backend,  Instalar dependencias (si es la primera vez)
pip install -r requirements.txt

# Crea el archivo .env donde pondras la url de tu database con user y password, dentro de /Backend

///// Activacion /////
# levantar el entorno virtual creado (venv), dentro de la carpeta /Backend
.\venv\Scripts\Activate.ps1

# Iniciar el servidor de backend
uvicorn app.main:app --reload


---------------------Frontend--------------------------

# Dentro de la carpeta /Frontend, Instalar dependencias (si es la primera vez)
npm install

# Iniciar el servidor de desarrollo
npm run dev