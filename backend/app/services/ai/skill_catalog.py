"""Finite label equivalences shared by parsing and matching; no fuzzy inference."""
CATALOG_VERSION = "2026-10-26.v4"
SKILL_NAMES = ("Python", "SQL", "Blender", "Unreal Engine 5", "UX/UI", "Figma", "Docker", "Git",
               "FastAPI", "prototipado", "diseño de niveles", "portero", "defensa", "delantero")
SPELLINGS = {name: (name,) for name in SKILL_NAMES}
SPELLINGS["Unreal Engine 5"] = ("Unreal Engine 5", "UE5")
SPELLINGS["UX/UI"] = ("UX/UI", "UX UI", "UI/UX")

SKILL_ALIASES = {alias: name for name, aliases in SPELLINGS.items() for alias in aliases if alias != name}
for name, aliases in SPELLINGS.items():
    for alias in aliases:
        for prefix in ("experiencia en ", "experiencia con ", "tengo experiencia en "):
            SKILL_ALIASES[prefix + alias] = name
for name in ("Python", "SQL"):
    for prefix in ("programar ", "programación ", "sé programar ", "programar en ", "programar con ", "programación en ", "programación con ",
                   "sé programar en ", "sé programar con ", "sé ", "domino ", "manejo ", "conozco "):
        SKILL_ALIASES[prefix + name] = name
for name in SKILL_NAMES:
    for prefix in ("trabajo con ", "trabajar con ", "uso de ", "uso ", "usar ", "manejo "):
        SKILL_ALIASES[prefix + name] = name
for name in ("portero", "defensa", "delantero"):
    for prefix in ("juego de ", "jugar de ", "sé jugar de "):
        SKILL_ALIASES[prefix + name] = name
