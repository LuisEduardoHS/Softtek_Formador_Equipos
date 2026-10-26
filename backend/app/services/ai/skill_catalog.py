"""Finite label equivalences shared by parsing and matching; no fuzzy inference."""
CATALOG_VERSION = "2026-10-25.v3"
SKILL_NAMES = ("Python", "SQL", "Blender", "Unreal Engine 5", "UX/UI", "Figma", "Docker", "Git")
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
