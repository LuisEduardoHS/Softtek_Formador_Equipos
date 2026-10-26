"""Bounded source classification; interests and goals never prove competence."""
import re
import unicodedata
from app.services.ai.skill_catalog import SKILL_NAMES, SKILL_ALIASES, SPELLINGS


def folded(value):
    return "".join(c for c in unicodedata.normalize("NFKD", value.casefold()) if not unicodedata.combining(c))


_ALIASES = {folded(k): v for k, v in {**{s: s for s in SKILL_NAMES}, **SKILL_ALIASES}.items()}
_SPELLINGS = {folded(alias): name for name, aliases in SPELLINGS.items() for alias in aliases}
_SKILLS = re.compile(r"(?<!\w)(?:" + "|".join(re.escape(s) for s in sorted(_SPELLINGS, key=len, reverse=True)) + r")(?!\w)")
GOAL = re.compile(r"\b(?:(?:quiero|deseo|debo|necesito|busco|me gustaria)\s+(?:aprender|mejorar|reforzar|adquirir|ganar|obtener|desarrollar)|aprender|mejorar|reforzar|areas?\s+(?:que\s+desea\s+)?reforzar)\b")
INTEREST = re.compile(r"\b(?:me\s+(?:interesa[n]?|gusta[n]?)|intereses?|tengo interes)\b")
AFFIRM = re.compile(r"\b(?:se|domino|manejo|conozco|programo|uso|utilizo|diseno|juego|hago|trabajo\s+con|experiencia\s+(?:en|con)|habilidades\s+declaradas|habilidad\s+actual|he\s+(?:usado|trabajado|programado|disenado))\b")
DENIAL = re.compile(r"\b(?:no|sin|nunca)\b")
UNCERTAIN = re.compile(r"\b(?:tal vez|quiza[s]?|no estoy segur[oa]|podria|talvez)\b")


def canonical_skill(value):
    text = " ".join(value.split())
    return _ALIASES.get(folded(text), text)


def source_clauses(source):
    return [c.strip() for c in re.split(
        r"[.;!?\n]|\b(?:pero|aunque)\b|,\s*(?=(?:no\b|se\b|domino\b|manejo\b|quiero\b|me\s+(?:interesa|gusta)))",
        unicodedata.normalize("NFC", source), flags=re.I) if c.strip()]


def skill_mentions(value):
    return [_SPELLINGS[m[0]] for m in _SKILLS.finditer(folded(value))]


def skill_statements(source, *, event=False):
    """Eight catalogued tools/domains with separate source polarity and intent."""
    found = {name: set() for name in SKILL_NAMES}
    for raw_clause in source_clauses(source):
        clause = folded(raw_clause)
        matches = list(_SKILLS.finditer(clause))
        for index, match in enumerate(matches):
            before = clause[:match.start()]
            local = re.split(r"\b(?:y|e|ni|o)\b|,", before)[-1]
            context = local if any(p.search(local) for p in (DENIAL, GOAL, INTEREST, AFFIRM, UNCERTAIN)) else before
            after = clause[match.end():matches[index+1].start() if index+1 < len(matches) else len(clause)]
            tail = after
            if not re.search(r"\b(?:obligatori[oa]s?|deseables?|opcional(?:es)?|imprescindible|no)\b", tail) and matches:
                middle = _SKILLS.sub("", clause[match.end():matches[-1].end()])
                if re.fullmatch(r"[\s,]*(?:(?:y|e|ni|o)[\s,]*)*", middle):
                    tail = clause[matches[-1].end():]
            skill = _SPELLINGS[match[0]]
            negative_before = DENIAL.search(context) and not re.search(r"\bno\s+solo\b", context)
            if event:
                if negative_before or re.match(r"\s+(?:no|sin)\b", tail):
                    state = "denied"
                elif re.search(r"\b(?:deseables?|opcional(?:es)?|preferibles?|ideal|se valora)\b", tail):
                    state = "preferred"
                elif GOAL.search(context):
                    state = "goal"
                elif re.search(r"\b(?:obligatori[oa]s?|imprescindible|indispensable|requerid[oa])\b", tail):
                    state = "required"
                elif re.search(r"\b(?:deseable|opcional|ideal|se valora)\b", local):
                    state = "preferred"
                elif re.search(r"\b(?:obligatori[oa]|imprescindible|se requiere)\b", context) or re.search(
                    r"\b(?:necesitamos|requerimos|exigimos|buscamos)\s+(?:(?:saber|dominar|usar|manejar|conocer)\s+)?$", context) or (
                    re.search(r"\b(?:necesitamos|requerimos|exigimos|buscamos)\b", context) and re.search(r"\bcon\s+$", context)):
                    state = "required"
                elif skill in {"Python", "Unreal Engine 5"} and re.search(r"\bprogramador(?:a)?\s+(?:de\s+)?$", context) and re.search(
                    r"\b(?:necesitamos|buscamos|busca|requiere|requerimos)\b", context):
                    state = "required"  # Existing literal programmer/tool contract.
                else:
                    state = "mentioned"
            elif UNCERTAIN.search(context):
                state = "mentioned"
            elif negative_before and GOAL.search(context):
                state = "denied_goal"
            elif negative_before and INTEREST.search(context):
                state = "denied_interest"
            elif negative_before:
                state = "denied"
            elif GOAL.search(context):
                state = "goal"
            elif INTEREST.search(context):
                state = "interest"
            elif AFFIRM.search(context):
                state = "affirmed"
            elif canonical_skill(raw_clause) in SKILL_NAMES:
                state = "affirmed"  # A whole, explicit skill label, not a fuzzy match.
            else:
                state = "mentioned"
            found[skill].add(state)
    return found


def reviewed_skills(values):
    """Canonicalize whole affirmative labels; never strip negation or intent."""
    seen, result = set(), []
    for value in values:
        canonical = canonical_skill(value)
        key = canonical.casefold()
        if key not in seen:
            result.append(canonical)
            seen.add(key)
    return result
