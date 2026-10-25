"""Small, explicit Python/SQL vocabulary; never infer competence from a goal."""
import re
import unicodedata


def folded(value):
    return "".join(c for c in unicodedata.normalize("NFKD", value.casefold())
                   if not unicodedata.combining(c))


def canonical_skill(value):
    text = " ".join(value.split())
    pattern = (r"(?:(?:se\s+)?(?:programar|programacion)\s+(?:en\s+)?|"
               r"(?:se|domino|manejo|conozco)\s+)?(python|sql)")
    match = re.fullmatch(pattern, folded(text))
    return {"python": "Python", "sql": "SQL"}[match[1]] if match else text


def skill_statements(source, *, event=False):
    """Return explicit occurrences and their polarity, including coordinated lists.

    This is a bounded repair for two known skills, not a general language parser.
    Conflicting declarations stay out of positive competence extraction.
    """
    found = {"Python": set(), "SQL": set()}
    clauses = re.split(r"[.;!?\n]|\b(?:pero|aunque)\b|,\s*(?=(?:no\b|se\b|domino\b|manejo\b|quiero\b))",
                       folded(source))
    for clause in clauses:
        matches = list(re.finditer(r"\b(python|sql)\b", clause))
        for index, match in enumerate(matches):
            before = clause[:match.start()]
            after = clause[match.end():matches[index + 1].start() if index + 1 < len(matches) else len(clause)]
            skill = "Python" if match[1] == "python" else "SQL"
            negated_after = re.search(r"^\s+(?:no\s+(?:(?:es|lo|se)\s+)?(?:obligatori[oa]|necesari[oa]|requerid[oa]|domino|se)|"
                                      r"sin\s+experiencia)", after)
            if negated_after or (re.search(r"\b(?:no|sin)\b", before) and not re.search(r"\bno\s+solo\b", before)):
                state = "denied"
            elif re.search(r"\b(?:quiero|deseo|busco|necesito)\s+(?:aprender|mejorar)|"
                           r"\b(?:aprender|areas?\s+(?:que\s+desea\s+)?reforzar|me\s+interesa)\b", before):
                state = "goal"
            elif event:
                # Adjectives after the current skill take precedence over a
                # previous skill's adjective: Python obligatorio y SQL deseable.
                if re.search(r"\b(?:deseable|opcional|preferible|ideal|se valora)\b", after):
                    state = "preferred"
                elif re.search(r"\b(?:obligatori[oa]|imprescindible|indispensable|requerid[oa])\b", after):
                    state = "required"
                else:
                    local = re.split(r"\by\b|,", before)[-1]
                    if re.search(r"\b(?:deseable|opcional|ideal|se valora)\b", local):
                        state = "preferred"
                    elif re.search(r"\b(?:obligatori[oa]|imprescindible|necesitamos|requerimos|se requiere|exigimos)\b", before):
                        state = "required"
                    else:
                        state = "mentioned"
            elif re.search(r"\b(?:se|domino|manejo|conozco|programo|experiencia\s+en|habilidades\s+declaradas)\b", before):
                state = "affirmed"
            else:
                state = "mentioned"
            found[skill].add(state)
    return found


def reviewed_skills(values):
    """Canonicalize affirmative labels without stripping negation or intent."""
    result = []
    for value in values:
        canonical = canonical_skill(value)
        if canonical.casefold() not in {item.casefold() for item in result}:
            result.append(canonical)
    return result
