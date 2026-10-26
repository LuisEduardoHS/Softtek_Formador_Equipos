"""Coverage from confirmed, permitted skill declarations, never role assignments."""
from pydantic import ValidationError
from app.services.ai.schemas import StructuredEventRequirements
from app.services.ai.matching.normalization import apply_equivalence
from app.services.ai.recommendations.orm_adapter import candidate_from_orm
from app.services.team_rules import event_roles
from fastapi import HTTPException


def confirmed_team_coverage(event, users, actor_id):
    unknown = {"estado": "desconocida", "total": 0, "cubiertas": [], "por_acreditar": []}
    if not event.requisitos_confirmados_at:
        return unknown
    try:
        requirements = StructuredEventRequirements.model_validate(event.requisitos_ia)
        roles = event_roles(event)
    except (ValidationError, TypeError, ValueError, HTTPException, AttributeError):
        return unknown
    terms = (requirements.habilidades_obligatorias + requirements.habilidades_deseables
             + [skill for role in roles for skill in role["habilidades"]])
    required = {apply_equivalence(term): term for term in reversed(terms)}
    if not required:
        return unknown
    known, incomplete = set(), False
    for user, profile in users:
        candidate = candidate_from_orm(user, profile, self_access=user.id_usuario == actor_id)
        if candidate.declared_skills is None:
            incomplete = True
        else:
            known.update(apply_equivalence(f.value) for f in candidate.declared_skills
                         if f.confirmed and f.polarity == "affirms")
    covered = [term for key, term in required.items() if key in known]
    pending = [term for key, term in required.items() if key not in known]
    return {"estado": "desconocida" if incomplete and pending else "conocida",
            "total": len(required), "cubiertas": covered, "por_acreditar": pending}
