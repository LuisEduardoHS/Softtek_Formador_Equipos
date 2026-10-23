"""Deterministic public explanations from assessed facts, without model calls."""

from .schemas import MatchResult, PublicExplanation


_REVIEW_REASONS = {
    "account_state_unknown": "Estado de la cuenta por verificar.",
    "event_state_unknown": "Estado del evento por verificar.",
    "participants_unknown": "Participación en el equipo por verificar.",
    "participation_unconfirmed": "Participación pendiente de confirmación.",
    "requirements_unknown": "Requisitos del evento por verificar.",
    "requirement_unknown": "Hay requisitos sin evidencia suficiente.",
    "required_skill_contradicted_review": "Una habilidad obligatoria tiene una negación confirmada que requiere revisión.",
}

_KIND_TEXT = {
    "required_skill": "habilidad obligatoria",
    "preferred_skill": "habilidad deseable",
    "open_role": "rol solicitado",
    "explicit_constraint": "condición explícita",
}


def explain_match(result: MatchResult) -> PublicExplanation:
    """Describe only assessed evidence and missing signals; never a success rate."""
    if not isinstance(result, MatchResult):
        raise TypeError("Se requiere MatchResult.")
    if result.eligibility == "ineligible":
        # Ineligible records are not recommendations; avoid echoing details.
        return PublicExplanation()
    strengths: list[str] = []
    gaps: list[str] = []
    unknowns: list[str] = []
    for item in result.requirements:
        label = _KIND_TEXT[item.kind]
        organizer_confirmed = any(evidence.source == "organizer_confirmed"
                                  and evidence.confirmed and evidence.polarity == "affirms"
                                  for evidence in item.evidence)
        if item.status == "met":
            candidate_confirmed = any(evidence.source == "user_declared"
                                      and evidence.confirmed and evidence.polarity == "affirms"
                                      for evidence in item.evidence)
            if organizer_confirmed and candidate_confirmed:
                strengths.append(f"Evidencia confirmada para {label}: {item.requirement}.")
            else:
                unknowns.append(f"Evidencia por verificar para {label}: {item.requirement}.")
        elif item.status == "unmet_confirmed":
            if organizer_confirmed and any(evidence.source == "user_declared"
                                           and evidence.confirmed and evidence.polarity == "denies"
                                           for evidence in item.evidence):
                gaps.append(f"Contradicción confirmada para {label}: {item.requirement}.")
            else:
                unknowns.append(f"Evidencia por verificar para {label}: {item.requirement}.")
        elif item.status == "unknown":
            unknowns.append(f"Por verificar {label}: {item.requirement}.")
    if result.score_components.get("complementarity") is None:
        unknowns.append("No hay datos suficientes para evaluar la complementariedad del equipo.")
    elif result.score_components["complementarity"] > 0:
        strengths.append("Aporta una capacidad que cubre un requisito o rol aún vacante.")
    if result.score_components.get("semantic_similarity") is None:
        unknowns.append("No hay embeddings comparables para la señal semántica.")
    if result.score_components.get("interests") is not None and result.score_components["interests"] > 0:
        strengths.append("Hay coincidencia textual de intereses o preferencias con el evento.")
    if result.evidence_coverage.known == 0:
        unknowns.append("No hay requisitos con evidencia confirmada para este candidato.")
    for reason in result.eligibility_reasons:
        message = _REVIEW_REASONS.get(reason)
        if message and message not in unknowns:
            unknowns.append(message)
    if result.ranking_score is None:
        unknowns.append("No hay señales puntuables disponibles.")
    return PublicExplanation(strengths=strengths, gaps=gaps, unknowns=unknowns)
