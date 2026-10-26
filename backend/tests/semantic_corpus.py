"""Finite fictitious corpus for opt-in real Llama QA; not an automatic model test."""
PROFILES = [
    {"id": "P01", "text": "Sé programar con SQL y crear consultas.", "skills": ["SQL"], "goals": []},
    {"id": "P02", "text": "Tengo experiencia en Blender y Unreal Engine 5. He modelado escenarios 3D.", "skills": ["Blender", "Unreal Engine 5"], "goals": []},
    {"id": "P03", "text": "Diseño interfaces UX/UI en Figma y he realizado prototipos para una app.", "skills": ["UX/UI", "Figma"], "goals": []},
    {"id": "P04", "text": "No sé Python. Domino SQL.", "skills": ["SQL"], "goals": [], "no_experience": True},
    {"id": "P05", "text": "No tengo experiencia laboral ni profesional. Quiero aprender diseño.", "skills": [], "goals": ["diseño"], "no_experience": True},
    {"id": "P06", "text": "Quiero aprender Docker. Mi habilidad actual es SQL.", "skills": ["SQL"], "goals": ["Docker"]},
    {"id": "P07", "text": "Me gustaría hacer algo interesante con otras personas, todavía no sé qué aportar.", "skills": [], "goals": [], "no_experience": True},
    {"id": "P08", "text": "No he usado Blender ni UE5. Quiero aprender Figma.", "skills": [], "goals": ["Figma"], "no_experience": True},
    {"id": "P09", "text": "Me gustan los videojuegos y los juegos de estrategia; no afirmo tener habilidades de programación.", "skills": [], "goals": [], "no_experience": True},
    {"id": "P10", "text": "Sé Python y SQL. He creado un panel de datos y limpiado encuestas. Me interesa la visualización y el diseño accesible. No sé Docker ni Unreal Engine 5. Quiero mejorar estadística y aprender Docker. Puedo trabajar los sábados.", "skills": ["Python", "SQL"], "goals": ["estadística", "Docker"]},
]
EVENTS = [
    {"id": "E01", "text": "Buscamos un desarrollador backend con Python obligatorio y SQL deseable para una aplicación web.", "required": ["Python"], "preferred": ["SQL"], "roles": ["desarrollador backend"]},
    {"id": "E02", "text": "Buscamos diseñador UX/UI. Figma es obligatorio para prototipar una app accesible.", "required": ["Figma"], "preferred": [], "roles": ["diseñador UX/UI"]},
    {"id": "E03", "text": "Buscamos analista con SQL obligatorio. Python no es obligatorio. No exigimos Docker.", "required": ["SQL"], "preferred": [], "roles": ["analista"]},
    {"id": "E04", "text": "Buscamos desarrollador web. Python y SQL son opcionales, no son obligatorios.", "required": [], "preferred": ["Python", "SQL"], "roles": ["desarrollador web"]},
    {"id": "E05", "text": "Queremos hacer algo creativo juntos; todavía no hemos decidido herramientas ni roles.", "required": [], "preferred": []},
    {"id": "E06", "text": "Blender obligatorio y Unreal Engine 5 deseable para modelar un escenario. Reuniones los sábados en línea.", "required": ["Blender"], "preferred": ["Unreal Engine 5"]},
]
