# 🚀 Formador de Equipos (Softtek)

Plataforma para la creación y gestión inteligente de equipos de trabajo.

---

## 🛠️ Requisitos Previos

Antes de comenzar, asegúrate de contar con los siguientes elementos configurados en tu sistema:
* **Python** (versión 3.10 o superior)
* **Node.js** (versión LTS)
* **MySQL** activo localmente
* **Ollama** ejecutándose en segundo plano

---

## ⚙️ Guía de Instalación y Ejecución

### 🐍 1. Backend

Todas las operaciones de esta sección se ejecutan desde la carpeta `/Backend`.

#### A. Setup Inicial (Solo la primera vez)

1. **Crear el entorno virtual:**
   ```powershell
   python -m venv venv
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