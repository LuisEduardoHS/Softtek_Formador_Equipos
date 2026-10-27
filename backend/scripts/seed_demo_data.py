r"""Carga datos ficticios completos para probar perfiles y recomendaciones.

Uso desde backend/:
    .\.venv\Scripts\python.exe scripts\seed_demo_data.py
"""

from datetime import datetime, timezone
from pathlib import Path
import sys

from passlib.context import CryptContext

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.db.database import SessionLocal
from app.models.evento import Evento
from app.models.usuario import PerfilUsuario, Usuario
from app.services.ai.integration import content_revision


PASSWORD = "12345678"
pwd_context = CryptContext(schemes=["bcrypt_sha256", "bcrypt"], deprecated="auto")
NOW = datetime.now(timezone.utc).replace(tzinfo=None)


USERS = [
    {
        "nombre": "Ana",
        "carrera": "Ingeniería de Software",
        "estado_geografico": "Jalisco",
        "municipio": "Guadalajara",
        "semestre": 7,
        "bio": "Desarrolladora full stack interesada en productos digitales accesibles.",
        "habilidades": ["Python", "FastAPI", "PostgreSQL", "React", "Docker"],
        "intereses": ["Tecnología educativa", "Accesibilidad", "Lectura"],
        "experiencia": ["API REST para plataforma universitaria", "Mentora de programación"],
        "reforzar": ["Diseño de producto", "Machine learning"],
        "disponibilidad": ["lun-tarde", "mie-tarde", "sab-manana"],
        "rol_preferido": "Desarrolladora backend",
    },
    {
        "nombre": "Bruno",
        "carrera": "Diseño Digital",
        "estado_geografico": "Jalisco",
        "municipio": "Zapopan",
        "semestre": 6,
        "bio": "Diseñador UX/UI enfocado en investigación, prototipos y comunicación visual.",
        "habilidades": ["Figma", "UX research", "Prototipado", "Design systems", "Illustrator"],
        "intereses": ["Diseño inclusivo", "Fotografía", "Videojuegos"],
        "experiencia": ["Rediseño de portal estudiantil", "Taller de prototipado"],
        "reforzar": ["HTML y CSS", "Analítica de producto"],
        "disponibilidad": ["mar-tarde", "jue-tarde", "sab-tarde"],
        "rol_preferido": "Diseñador UX",
    },
    {
        "nombre": "Carla",
        "carrera": "Administración y Finanzas",
        "estado_geografico": "Nuevo León",
        "municipio": "Monterrey",
        "semestre": 8,
        "bio": "Analista de datos y finanzas con interés en proyectos de impacto social.",
        "habilidades": ["Excel", "Análisis financiero", "SQL", "Power BI", "Presentaciones"],
        "intereses": ["Emprendimiento", "Impacto social", "Ciclismo"],
        "experiencia": ["Modelo financiero para emprendimiento", "Coordinación de presupuesto"],
        "reforzar": ["Python", "Marketing digital"],
        "disponibilidad": ["lun-noche", "mie-noche", "vie-noche"],
        "rol_preferido": "Analista de negocio",
    },
    {
        "nombre": "Diego",
        "carrera": "Ciencias de la Comunicación",
        "estado_geografico": "Ciudad de México",
        "municipio": "Coyoacán",
        "semestre": 5,
        "bio": "Comunicador y creador audiovisual para campañas, eventos y comunidades.",
        "habilidades": ["Redacción", "Storytelling", "Edición de video", "Podcast", "Redes sociales"],
        "intereses": ["Cultura", "Música", "Periodismo"],
        "experiencia": ["Podcast universitario", "Campaña de difusión cultural"],
        "reforzar": ["Métricas digitales", "Diseño gráfico"],
        "disponibilidad": ["mie-tarde", "vie-tarde", "sab-manana", "sab-tarde"],
        "rol_preferido": "Coordinador de comunicación",
    },
    {
        "nombre": "Elena",
        "carrera": "Ingeniería Industrial",
        "estado_geografico": "Querétaro",
        "municipio": "Querétaro",
        "semestre": 7,
        "bio": "Organizadora de proyectos con experiencia en procesos, logística y trabajo en equipo.",
        "habilidades": ["Gestión de proyectos", "Scrum", "Logística", "Excel", "Liderazgo"],
        "intereses": ["Sostenibilidad", "Deporte", "Voluntariado"],
        "experiencia": ["Coordinación de feria universitaria", "Mejora de procesos"],
        "reforzar": ["Programación", "Diseño de servicios"],
        "disponibilidad": ["lun-tarde", "mie-tarde", "vie-tarde"],
        "rol_preferido": "Líder de proyecto",
    },
    {
        "nombre": "Felipe",
        "carrera": "Ingeniería Mecatrónica",
        "estado_geografico": "Puebla",
        "municipio": "Puebla",
        "semestre": 6,
        "bio": "Entusiasta de la robótica, los sensores y la creación de prototipos.",
        "habilidades": ["Arduino", "Python", "Electrónica", "CAD", "Prototipado"],
        "intereses": ["Robótica", "Energía renovable", "Fútbol"],
        "experiencia": ["Prototipo de riego automático", "Competencia de robótica"],
        "reforzar": ["Comunicación", "Gestión de proyectos"],
        "disponibilidad": ["mar-tarde", "jue-tarde", "sab-manana"],
        "rol_preferido": "Desarrollador de prototipos",
    },
    {
        "nombre": "Gabriela", "carrera": "Biotecnología", "estado_geografico": "Morelos",
        "municipio": "Cuernavaca", "semestre": 6,
        "bio": "Investigadora interesada en ciencia de datos aplicada a la salud y el ambiente.",
        "habilidades": ["Análisis de datos", "R", "Excel", "Investigación", "Presentaciones"],
        "intereses": ["Ciencia", "Salud", "Naturaleza"],
        "experiencia": ["Análisis de resultados de laboratorio", "Feria de ciencias"],
        "reforzar": ["Python", "Visualización de datos"],
        "disponibilidad": ["lun-manana", "mie-manana", "vie-tarde"],
        "rol_preferido": "Analista de datos",
    },
    {
        "nombre": "Hugo", "carrera": "Ingeniería Civil", "estado_geografico": "Guanajuato",
        "municipio": "León", "semestre": 8,
        "bio": "Estudiante de construcción sostenible con experiencia en planeación y modelado.",
        "habilidades": ["AutoCAD", "Modelado 3D", "Planeación", "Excel", "Liderazgo"],
        "intereses": ["Arquitectura", "Sostenibilidad", "Fotografía"],
        "experiencia": ["Diseño de vivienda sustentable", "Coordinación de obra escolar"],
        "reforzar": ["Programación", "Diseño UX"],
        "disponibilidad": ["mar-manana", "jue-manana", "sab-tarde"],
        "rol_preferido": "Coordinador de planeación",
    },
    {
        "nombre": "Isabel", "carrera": "Psicología", "estado_geografico": "Yucatán",
        "municipio": "Mérida", "semestre": 5,
        "bio": "Facilitadora de comunidades interesada en bienestar estudiantil e investigación cualitativa.",
        "habilidades": ["Entrevistas", "Investigación cualitativa", "Facilitación", "Redacción", "Empatía"],
        "intereses": ["Bienestar", "Educación", "Arte"],
        "experiencia": ["Encuestas de bienestar universitario", "Círculo de acompañamiento"],
        "reforzar": ["Análisis de datos", "Diseño de servicios"],
        "disponibilidad": ["lun-tarde", "jue-tarde", "sab-manana"],
        "rol_preferido": "Investigadora de usuarios",
    },
    {
        "nombre": "Javier", "carrera": "Ingeniería en Computación", "estado_geografico": "Sonora",
        "municipio": "Hermosillo", "semestre": 7,
        "bio": "Desarrollador de software enfocado en aplicaciones móviles, pruebas y calidad.",
        "habilidades": ["JavaScript", "React Native", "Node.js", "Testing", "Git"],
        "intereses": ["Aplicaciones móviles", "Ciberseguridad", "Cine"],
        "experiencia": ["App móvil para biblioteca", "Pruebas automatizadas"],
        "reforzar": ["Gestión de proyectos", "Diseño visual"],
        "disponibilidad": ["mar-noche", "jue-noche", "sab-manana"],
        "rol_preferido": "Desarrollador frontend",
    },
    {
        "nombre": "Karen", "carrera": "Mercadotecnia", "estado_geografico": "Veracruz",
        "municipio": "Xalapa", "semestre": 6,
        "bio": "Estratega de marketing con experiencia en contenido, campañas y comunidades digitales.",
        "habilidades": ["Marketing digital", "SEO", "Copywriting", "Redes sociales", "Canva"],
        "intereses": ["Emprendimiento", "Música", "Cultura"],
        "experiencia": ["Campaña para emprendimiento local", "Calendario de contenidos"],
        "reforzar": ["Analítica web", "Presentaciones"],
        "disponibilidad": ["lun-noche", "mie-noche", "vie-tarde"],
        "rol_preferido": "Estratega de marketing",
    },
    {
        "nombre": "Luis", "carrera": "Física", "estado_geografico": "Coahuila",
        "municipio": "Saltillo", "semestre": 8,
        "bio": "Físico con experiencia en simulación, programación científica y divulgación.",
        "habilidades": ["Python", "Matemáticas", "Simulación", "LaTeX", "Investigación"],
        "intereses": ["Astronomía", "Ciencia", "Divulgación"],
        "experiencia": ["Simulación de sistemas dinámicos", "Club de astronomía"],
        "reforzar": ["Comunicación", "Gestión de proyectos"],
        "disponibilidad": ["mar-tarde", "jue-tarde", "sab-noche"],
        "rol_preferido": "Investigador",
    },
    {
        "nombre": "Mariana", "carrera": "Arquitectura", "estado_geografico": "Oaxaca",
        "municipio": "Oaxaca", "semestre": 7,
        "bio": "Arquitecta en formación interesada en espacios inclusivos, visualización y comunidad.",
        "habilidades": ["AutoCAD", "SketchUp", "Renderizado", "Diseño espacial", "Figma"],
        "intereses": ["Arquitectura", "Patrimonio", "Diseño inclusivo"],
        "experiencia": ["Propuesta de espacio comunitario", "Exposición de maquetas"],
        "reforzar": ["Gestión de proyectos", "Investigación cualitativa"],
        "disponibilidad": ["mie-manana", "vie-manana", "sab-tarde"],
        "rol_preferido": "Diseñadora de espacios",
    },
    {
        "nombre": "Nicolas", "carrera": "Ingeniería Ambiental", "estado_geografico": "Chiapas",
        "municipio": "Tuxtla Gutiérrez", "semestre": 5,
        "bio": "Promotor ambiental que combina educación, datos y organización comunitaria.",
        "habilidades": ["Sostenibilidad", "Excel", "Educación ambiental", "Logística", "Redacción"],
        "intereses": ["Reciclaje", "Senderismo", "Voluntariado"],
        "experiencia": ["Campaña de reciclaje", "Jornada de reforestación"],
        "reforzar": ["Visualización de datos", "Marketing digital"],
        "disponibilidad": ["lun-manana", "mie-tarde", "sab-manana"],
        "rol_preferido": "Coordinador ambiental",
    },
    {
        "nombre": "Olivia", "carrera": "Música", "estado_geografico": "Baja California",
        "municipio": "Tijuana", "semestre": 4,
        "bio": "Música y productora de audio interesada en eventos culturales y creación colaborativa.",
        "habilidades": ["Producción musical", "Edición de audio", "Composición", "Podcast", "Organización"],
        "intereses": ["Música", "Cultura", "Cine"],
        "experiencia": ["Producción de concierto estudiantil", "Podcast cultural"],
        "reforzar": ["Redes sociales", "Gestión de proyectos"],
        "disponibilidad": ["jue-noche", "vie-noche", "sab-tarde"],
        "rol_preferido": "Productora de audio",
    },
    {
        "nombre": "Pablo", "carrera": "Derecho", "estado_geografico": "Tamaulipas",
        "municipio": "Tampico", "semestre": 8,
        "bio": "Estudiante de derecho con interés en ciudadanía, debate y proyectos de impacto social.",
        "habilidades": ["Investigación jurídica", "Debate", "Redacción", "Argumentación", "Liderazgo"],
        "intereses": ["Derechos humanos", "Debate", "Voluntariado"],
        "experiencia": ["Clínica jurídica universitaria", "Torneo de debate"],
        "reforzar": ["Análisis de datos", "Comunicación digital"],
        "disponibilidad": ["mar-noche", "vie-tarde", "sab-manana"],
        "rol_preferido": "Investigador jurídico",
    },
]


EVENTS = [
    {
        "creator": "Ana",
        "categoria": "Academico",
        "titulo": "Tutorías de programación para primer ingreso",
        "descripcion": "Proyecto académico para crear sesiones prácticas de Python y APIs para estudiantes de primer ingreso.",
        "materia": "Programación web",
        "tipo": "Proyecto académico",
        "roles": [
            {"id": "tutor", "nombre": "Tutor de programación", "habilidades": ["Python"], "vacantes": 2},
            {"id": "difusion", "nombre": "Difusión", "habilidades": ["Redacción"], "vacantes": 1},
        ],
        "skills": ["Python", "Redacción"],
        "desired": ["FastAPI", "Presentaciones"],
        "role_names": ["Tutor de programación", "Difusión"],
        "interests": ["Educación", "Tecnología educativa"],
        "horario": "lun-tarde",
    },
    {
        "creator": "Bruno",
        "categoria": "Academico",
        "titulo": "App de movilidad sustentable del campus",
        "descripcion": "Equipo para diseñar y validar una aplicación que ayude a compartir rutas de movilidad sustentable.",
        "materia": "Innovación y diseño",
        "tipo": "Proyecto académico",
        "roles": [
            {"id": "datos", "nombre": "Analista de datos", "habilidades": ["SQL"], "vacantes": 1},
            {"id": "backend", "nombre": "Backend", "habilidades": ["Python"], "vacantes": 1},
            {"id": "lider", "nombre": "Líder de proyecto", "habilidades": ["Gestión de proyectos"], "vacantes": 1},
        ],
        "skills": ["SQL", "Python"],
        "desired": ["Gestión de proyectos", "Figma"],
        "role_names": ["Analista de datos", "Backend", "Líder de proyecto"],
        "interests": ["Sostenibilidad", "Movilidad"],
        "horario": "mar-tarde",
    },
    {
        "creator": "Carla",
        "categoria": "Academico",
        "titulo": "Laboratorio de emprendimiento social",
        "descripcion": "Diseño de un modelo de negocio y una campaña para una iniciativa con impacto social.",
        "materia": "Emprendimiento",
        "tipo": "Investigación aplicada",
        "roles": [
            {"id": "negocio", "nombre": "Analista de negocio", "habilidades": ["Análisis financiero"], "vacantes": 1},
            {"id": "comunicacion", "nombre": "Comunicación", "habilidades": ["Storytelling"], "vacantes": 1},
            {"id": "ux", "nombre": "Diseño UX", "habilidades": ["Figma"], "vacantes": 1},
        ],
        "skills": ["Análisis financiero", "Storytelling", "Figma"],
        "desired": ["Marketing digital", "Presentaciones"],
        "role_names": ["Analista de negocio", "Comunicación", "Diseño UX"],
        "interests": ["Emprendimiento", "Impacto social"],
        "horario": "mie-tarde",
    },
    {
        "creator": "Elena",
        "categoria": "Academico",
        "titulo": "Prototipo de riego inteligente",
        "descripcion": "Proyecto interdisciplinario para construir un prototipo con sensores y documentar su impacto.",
        "materia": "Automatización",
        "tipo": "Prototipo",
        "roles": [
            {"id": "hardware", "nombre": "Hardware", "habilidades": ["Arduino"], "vacantes": 1},
            {"id": "procesos", "nombre": "Procesos", "habilidades": ["Gestión de proyectos"], "vacantes": 1},
        ],
        "skills": ["Arduino", "Electrónica"],
        "desired": ["Gestión de proyectos", "Sostenibilidad"],
        "role_names": ["Hardware", "Procesos"],
        "interests": ["Energía renovable", "Sostenibilidad"],
        "horario": "jue-tarde",
    },
    {
        "creator": "Diego",
        "categoria": "Personal",
        "titulo": "Podcast de historias del campus",
        "descripcion": "Proyecto personal para entrevistar estudiantes y contar historias de la comunidad universitaria.",
        "materia": "",
        "tipo": "Proyecto personal",
        "roles": [
            {"id": "audio", "nombre": "Producción de audio", "habilidades": ["Podcast"], "vacantes": 1},
            {"id": "difusion", "nombre": "Redes sociales", "habilidades": ["Redes sociales"], "vacantes": 1},
        ],
        "skills": ["Podcast", "Redes sociales"],
        "desired": ["Edición de video", "Storytelling"],
        "role_names": ["Producción de audio", "Redes sociales"],
        "interests": ["Cultura", "Periodismo"],
        "horario": "vie-tarde",
    },
    {
        "creator": "Felipe",
        "categoria": "Personal",
        "titulo": "Club de robótica de fin de semana",
        "descripcion": "Club abierto para construir prototipos con Arduino y compartir conocimientos de electrónica.",
        "materia": "",
        "tipo": "Club personal",
        "roles": [
            {"id": "robotica", "nombre": "Robótica", "habilidades": ["Arduino"], "vacantes": 2},
            {"id": "organizacion", "nombre": "Organización", "habilidades": ["Logística"], "vacantes": 1},
        ],
        "skills": ["Arduino", "Electrónica"],
        "desired": ["Logística", "CAD"],
        "role_names": ["Robótica", "Organización"],
        "interests": ["Robótica", "Fútbol"],
        "horario": "sab-manana",
    },
    {
        "creator": "Ana",
        "categoria": "Personal",
        "titulo": "Taller comunitario de alfabetización digital",
        "descripcion": "Taller voluntario para enseñar herramientas digitales básicas a personas de la comunidad.",
        "materia": "",
        "tipo": "Voluntariado",
        "roles": [
            {"id": "taller", "nombre": "Facilitación", "habilidades": ["Presentaciones"], "vacantes": 2},
            {"id": "coordinacion", "nombre": "Coordinación", "habilidades": ["Liderazgo"], "vacantes": 1},
        ],
        "skills": ["Presentaciones", "Liderazgo"],
        "desired": ["Redacción", "Gestión de proyectos"],
        "role_names": ["Facilitación", "Coordinación"],
        "interests": ["Voluntariado", "Educación"],
        "horario": "sab-tarde",
    },
    {
        "creator": "Elena",
        "categoria": "Personal",
        "titulo": "Reto de ciclismo y hábitos sostenibles",
        "descripcion": "Grupo para organizar rutas de ciclismo y registrar hábitos sostenibles durante un mes.",
        "materia": "",
        "tipo": "Actividad personal",
        "roles": [
            {"id": "logistica", "nombre": "Logística", "habilidades": ["Logística"], "vacantes": 1},
            {"id": "comunidad", "nombre": "Comunidad", "habilidades": ["Redes sociales"], "vacantes": 1},
        ],
        "skills": ["Logística", "Redes sociales"],
        "desired": ["Gestión de proyectos", "Redacción"],
        "role_names": ["Logística", "Comunidad"],
        "interests": ["Ciclismo", "Sostenibilidad"],
        "horario": "lun-noche",
    },
]


def extra_event(creator, category, title, description, event_type, schedule,
                skills, desired, roles, interests, subject=""):
    return {
        "creator": creator,
        "categoria": category,
        "titulo": title,
        "descripcion": description,
        "materia": subject,
        "tipo": event_type,
        "roles": [
            {"id": f"rol-{index}", "nombre": role, "habilidades": [skill], "vacantes": 1}
            for index, (role, skill) in enumerate(roles)
        ],
        "skills": skills,
        "desired": desired,
        "role_names": [role for role, _ in roles],
        "interests": interests,
        "horario": schedule,
    }


EVENTS.extend([
    extra_event("Gabriela", "Academico", "Datos para mejorar la salud universitaria",
                "Analizar hábitos de estudiantes y presentar hallazgos para mejorar el bienestar.",
                "Investigación aplicada", "lun-manana", ["Análisis de datos", "R"],
                ["Python", "Presentaciones"],
                [("Analista de datos", "Análisis de datos"), ("Investigación", "Investigación")],
                ["Salud", "Ciencia"], "Métodos de investigación"),
    extra_event("Hugo", "Academico", "Diseño de vivienda sustentable",
                "Proponer un modelo de vivienda accesible con materiales y procesos sostenibles.",
                "Proyecto académico", "mar-manana", ["AutoCAD", "Sostenibilidad"],
                ["Modelado 3D", "Planeación"],
                [("Diseño", "AutoCAD"), ("Planeación", "Planeación")],
                ["Arquitectura", "Sostenibilidad"], "Construcción sostenible"),
    extra_event("Isabel", "Academico", "Mapa de bienestar estudiantil",
                "Investigar necesidades de bienestar y diseñar una guía de apoyo para estudiantes.",
                "Investigación", "jue-tarde", ["Entrevistas", "Investigación cualitativa"],
                ["Figma", "Redacción"],
                [("Investigación de usuarios", "Entrevistas"), ("Contenido", "Redacción")],
                ["Bienestar", "Educación"], "Psicología social"),
    extra_event("Javier", "Academico", "Aplicación móvil de biblioteca",
                "Crear una aplicación móvil para consultar libros, horarios y recursos del campus.",
                "Desarrollo de software", "mar-noche", ["React Native", "Node.js"],
                ["Testing", "Figma"],
                [("Frontend móvil", "React Native"), ("Calidad", "Testing")],
                ["Aplicaciones móviles", "Educación"], "Ingeniería de software"),
    extra_event("Karen", "Academico", "Campaña de emprendimientos universitarios",
                "Crear una estrategia digital para dar visibilidad a proyectos de estudiantes.",
                "Proyecto de marketing", "vie-tarde", ["Marketing digital", "Copywriting"],
                ["Diseño UX", "Presentaciones"],
                [("Estrategia", "Marketing digital"), ("Contenido", "Copywriting")],
                ["Emprendimiento", "Cultura"], "Mercadotecnia"),
    extra_event("Luis", "Personal", "Club de astronomía y simulación",
                "Compartir observaciones del cielo y crear simulaciones sencillas para divulgación.",
                "Club personal", "sab-noche", ["Python", "Simulación"],
                ["Redacción", "Presentaciones"],
                [("Simulación", "Simulación"), ("Divulgación", "Redacción")],
                ["Astronomía", "Ciencia"]),
    extra_event("Mariana", "Personal", "Taller de espacios inclusivos",
                "Explorar ideas para diseñar espacios comunitarios accesibles y acogedores.",
                "Taller personal", "sab-tarde", ["Diseño espacial", "Figma"],
                ["Investigación cualitativa", "Renderizado"],
                [("Diseño", "Diseño espacial"), ("Investigación", "Investigación cualitativa")],
                ["Diseño inclusivo", "Arquitectura"]),
    extra_event("Nicolas", "Personal", "Voluntariado de reforestación",
                "Organizar jornadas de reforestación y materiales educativos para la comunidad.",
                "Voluntariado", "sab-manana", ["Educación ambiental", "Logística"],
                ["Redacción", "Redes sociales"],
                [("Logística", "Logística"), ("Educación", "Educación ambiental")],
                ["Voluntariado", "Sostenibilidad"]),
    extra_event("Olivia", "Personal", "Sesiones de producción musical",
                "Crear piezas colaborativas y registrar sesiones de música para un catálogo comunitario.",
                "Proyecto creativo", "jue-noche", ["Producción musical", "Edición de audio"],
                ["Podcast", "Organización"],
                [("Audio", "Edición de audio"), ("Producción", "Organización")],
                ["Música", "Cultura"]),
    extra_event("Pablo", "Personal", "Círculo de debate y ciudadanía",
                "Dialogar sobre derechos humanos y preparar argumentos para actividades de debate.",
                "Círculo personal", "mar-noche", ["Debate", "Argumentación"],
                ["Redacción", "Investigación"],
                [("Debate", "Debate"), ("Investigación", "Investigación jurídica")],
                ["Derechos humanos", "Debate"]),
])


def profile_data(user):
    return {
        "fortalezas": [{"nombre": skill, "nivel": "Intermedio"} for skill in user["habilidades"]],
        "habilidades": user["habilidades"],
        "reforzar": user["reforzar"],
        "intereses": user["intereses"],
        "experiencia": user["experiencia"],
        "disponibilidad": user["disponibilidad"],
        "visibilidad": {"fortalezas": True, "intereses": True, "disponibilidad": True,
                        "reforzar": False, "correo": False},
        "pausado": False,
        "consentimiento_recomendaciones": True,
        "semestre": user["semestre"],
        "bio": user["bio"],
        "rol_preferido": user["rol_preferido"],
        "disponibilidad_horaria": ", ".join(user["disponibilidad"]),
        "redes_sociales": {"github": f"https://github.com/{user['nombre'].lower()}"},
    }


def seed():
    db = SessionLocal()
    try:
        password_hash = pwd_context.hash(PASSWORD)
        users_by_name = {}
        for data in USERS:
            email = f"{data['nombre'].lower()}@uni.com"
            user = db.query(Usuario).filter(Usuario.correo == email).first()
            if user is None:
                user = Usuario(nombre=data["nombre"], correo=email, carrera=data["carrera"],
                               estado_geografico=data["estado_geografico"],
                               municipio=data["municipio"], estado_cuenta="Activa",
                               rol_sistema="Estudiante", password_hash=password_hash)
                db.add(user)
                db.flush()
            else:
                user.nombre = data["nombre"]
                user.carrera = data["carrera"]
                user.estado_geografico = data["estado_geografico"]
                user.municipio = data["municipio"]
                user.estado_cuenta = "Activa"
                user.password_hash = password_hash

            raw = profile_data(data)
            structured = {
                "habilidades": data["habilidades"],
                "intereses": data["intereses"],
                "areas_mejora": data["reforzar"],
                "experiencia": data["experiencia"],
                "resumen_publico": data["bio"],
            }
            profile = db.get(PerfilUsuario, user.id_usuario)
            if profile is None:
                profile = PerfilUsuario(usuario_id=user.id_usuario)
                db.add(profile)
            profile.nombre_mostrar = data["nombre"]
            profile.datos_crudos = raw
            profile.atributos_dinamicos = {"tipo_perfil": "demo", "fuente": "seed_demo_data"}
            profile.perfil_estructurado_ia = structured
            profile.resumen_publico_ia = data["bio"]
            profile.perfil_fuente_revision = content_revision(structured)
            profile.perfil_confirmado_at = NOW
            profile.perfil_estado_ia = "pendiente_embedding"
            profile.embedding_perfil = None
            profile.perfil_embedding_fuente_revision = None
            users_by_name[data["nombre"]] = user

        db.flush()
        for data in EVENTS:
            creator = users_by_name[data["creator"]]
            details = {
                "integrantes": 5,
                "roles": data["roles"],
                "materia": data["materia"],
                "tipo": data["tipo"],
                "disponibilidad": [data["horario"]],
                "titulo": data["titulo"],
            }
            requirements = {
                "categoria": data["categoria"],
                "titulo_normalizado": data["titulo"],
                "resumen": data["descripcion"],
                "habilidades_obligatorias": data["skills"],
                "habilidades_deseables": data["desired"],
                "roles_buscados": data["role_names"],
                "intereses_relacionados": data["interests"],
                "restricciones_explicitas": [data["horario"]],
            }
            event = db.query(Evento).filter(
                Evento.creador_id == creator.id_usuario,
                Evento.titulo == data["titulo"],
            ).first()
            if event is None:
                event = Evento(creador_id=creator.id_usuario, titulo=data["titulo"])
                db.add(event)
            event.categoria_principal = data["categoria"]
            event.descripcion_libre = data["descripcion"]
            event.detalles_especificos = details
            event.requisitos_ia = requirements
            event.requisitos_borrador_ia = None
            event.estado_ia = "pendiente_embedding"
            event.requisitos_fuente_revision = content_revision(
                {"titulo": data["titulo"], "requirements": requirements}
            )
            event.embedding_requisitos = None
            event.embedding_fuente_revision = None
            event.requisitos_confirmados_at = NOW
            event.estado = "Abierto"

        db.commit()
        print(f"Datos demo listos: {len(USERS)} perfiles y {len(EVENTS)} eventos.")
        print("Contraseña de todos los perfiles: 12345678")
        print("Correos: " + ", ".join(f"{user['nombre'].lower()}@uni.com" for user in USERS))
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
