"""Optional, constrained Spanish wording of already public match explanations.

The model receives only anonymous fact categories and chooses approved wording.
It never receives requirement text, profile data, identifiers or vectors, and its
own prose is never displayed. Invalid selections preserve the deterministic text.
"""

import json
import re
from typing import Protocol

from app.services.ai.matching.schemas import PublicExplanation

from .contracts import CandidateRecommendation, ProjectRecommendation


class StructuredTextGenerator(Protocol):
    def generate_structured(self, prompt: str, schema: dict) -> str: ...


_GROUPS = ("strengths", "gaps", "unknowns")
_PREFIXES = {"strengths": "s", "gaps": "g", "unknowns": "u"}
_MAX_FACTS = 16
_MAX_RESPONSE_CHARS = 8192
_KNOWN_LABELS = ("habilidad obligatoria", "habilidad deseable",
                 "rol solicitado", "condición explícita")
_LABEL_PATTERN = "|".join(re.escape(label) for label in _KNOWN_LABELS)
_CONFIRMED = re.compile(rf"^Evidencia confirmada para ({_LABEL_PATTERN}): (.+)\.$")
_CONTRADICTION = re.compile(rf"^Contradicción confirmada para ({_LABEL_PATTERN}): (.+)\.$")
_TO_VERIFY = re.compile(rf"^Por verificar ({_LABEL_PATTERN}): (.+)\.$")


def _approved_variants(group: str, sentence: str) -> tuple[str, ...]:
    """Every alternative preserves the original polarity and stated term."""
    if group == "strengths":
        match = _CONFIRMED.fullmatch(sentence)
        if match:
            return (sentence, f"Hay evidencia confirmada para {match[1]}: {match[2]}.")
    elif group == "gaps":
        match = _CONTRADICTION.fullmatch(sentence)
        if match:
            return (sentence, f"Se confirmó una contradicción para {match[1]}: {match[2]}.")
    else:
        match = _TO_VERIFY.fullmatch(sentence)
        if match:
            return (sentence, f"Falta verificar {match[1]}: {match[2]}.")
    return (sentence,)


def _fact_kind(group: str, sentence: str) -> str:
    pattern = {"strengths": _CONFIRMED, "gaps": _CONTRADICTION,
               "unknowns": _TO_VERIFY}[group]
    match = pattern.fullmatch(sentence)
    if match:
        return match[1].replace(" ", "_")
    return "mensaje_general"


def _facts(explanation: PublicExplanation) -> dict[str, list[tuple[str, str, tuple[str, ...]]]]:
    result = {}
    for group in _GROUPS:
        result[group] = [
            (f"{_PREFIXES[group]}{index}", _fact_kind(group, sentence),
             _approved_variants(group, sentence))
            for index, sentence in enumerate(getattr(explanation, group))
        ]
    return result


def _schema() -> dict:
    item = {
        "type": "object", "additionalProperties": False,
        "properties": {"fact_id": {"type": "string"},
                       "variant": {"type": "integer", "minimum": 0, "maximum": 1}},
        "required": ["fact_id", "variant"],
    }
    return {
        "type": "object", "additionalProperties": False,
        "properties": {group: {"type": "array", "items": item} for group in _GROUPS},
        "required": list(_GROUPS),
    }


def _prompt(facts: dict[str, list[tuple[str, str, tuple[str, ...]]]]) -> str:
    # No source sentence or real user/event identifier crosses this boundary.
    safe_facts = {
        group: [{"fact_id": fact_id, "kind": kind, "variants": len(variants)}
                for fact_id, kind, variants in entries]
        for group, entries in facts.items()
    }
    return (
        "Ordena cada lista exactamente como está y elige una variante permitida "
        "para cada fact_id. No omitas, agregues ni cambies de grupo ningún hecho. "
        "0 conserva la frase determinista; 1 usa una reformulación aprobada "
        "cuando variants=2. Responde solo JSON con strengths, gaps y unknowns; "
        "cada elemento tiene fact_id y variant. No generes texto libre. "
        + json.dumps(safe_facts, ensure_ascii=False, separators=(",", ":"))
    )


def _reject_duplicate_keys(pairs: list[tuple[str, object]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("JSON con claves duplicadas.")
        result[key] = value
    return result


def _validated_explanation(
    raw: str,
    facts: dict[str, list[tuple[str, str, tuple[str, ...]]]],
) -> PublicExplanation:
    if not isinstance(raw, str) or not raw.strip() or len(raw) > _MAX_RESPONSE_CHARS:
        raise ValueError("Respuesta vacía o excesiva.")
    choices = json.loads(raw, object_pairs_hook=_reject_duplicate_keys)
    if not isinstance(choices, dict) or set(choices) != set(_GROUPS):
        raise ValueError("Grupos de hechos inválidos.")
    output: dict[str, list[str]] = {}
    for group in _GROUPS:
        selected = choices[group]
        expected = facts[group]
        if not isinstance(selected, list) or len(selected) != len(expected):
            raise ValueError("La respuesta omitió o añadió hechos.")
        lines: list[str] = []
        for choice, (fact_id, _, variants) in zip(selected, expected):
            if (not isinstance(choice, dict) or set(choice) != {"fact_id", "variant"}
                    or choice["fact_id"] != fact_id or type(choice["variant"]) is not int
                    or not 0 <= choice["variant"] < len(variants)):
                raise ValueError("La respuesta usó un hecho o variante no autorizados.")
            lines.append(variants[choice["variant"]])
        output[group] = lines
    return PublicExplanation(**output)


def personalize_recommendation(
    recommendation: CandidateRecommendation | ProjectRecommendation,
    *,
    use_llm: bool = False,
    ai: StructuredTextGenerator | None = None,
) -> CandidateRecommendation | ProjectRecommendation:
    """Return the same public DTO type, changing only approved Spanish wording.

    The caller must explicitly request LLM enrichment. Without that request,
    or after any model/validation failure, the original deterministic explanation
    is returned. Eligibility, evidence coverage and order are untouched.
    """
    if not isinstance(recommendation, (CandidateRecommendation, ProjectRecommendation)):
        raise TypeError("Se requiere una recomendación pública validada.")
    if type(use_llm) is not bool:
        raise TypeError("use_llm debe ser booleano.")
    fallback = recommendation.model_copy(deep=True)
    if not use_llm:
        return fallback
    facts = _facts(fallback.explanation)
    count = sum(map(len, facts.values()))
    if count == 0 or count > _MAX_FACTS:
        return fallback
    try:
        if ai is None:
            from app.services.ai.ollama_client import OllamaClient
            ai = OllamaClient()
        raw = ai.generate_structured(_prompt(facts), _schema())
        approved = _validated_explanation(raw, facts)
    except Exception:
        return fallback
    return fallback.model_copy(update={"explanation": approved})
