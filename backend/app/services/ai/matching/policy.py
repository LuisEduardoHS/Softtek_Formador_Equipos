"""Versioned, immutable ranking configuration for subphase 4.4."""

import math
from dataclasses import dataclass, field

from .eligibility import EligibilityPolicy


@dataclass(frozen=True, slots=True)
class RankingPolicy:
    version: str = "2026-10-21.v1"
    required_weight: float = 0.40
    complementarity_weight: float = 0.25
    preferred_weight: float = 0.15
    semantic_weight: float = 0.10
    interest_weight: float = 0.10
    min_available_signals: int = 2
    min_known_requirements: int = 1
    eligibility: EligibilityPolicy = field(default_factory=EligibilityPolicy)

    def __post_init__(self):
        if not isinstance(self.version, str) or not self.version.strip():
            raise ValueError("La política necesita una versión no vacía.")
        weights = self.weights
        if any(isinstance(value, bool) or not isinstance(value, (int, float))
               or not math.isfinite(value) or value < 0 for value in weights.values()):
            raise ValueError("Los pesos deben ser números finitos no negativos.")
        if not math.isclose(sum(weights.values()), 1.0, rel_tol=0, abs_tol=1e-9):
            raise ValueError("Los pesos deben sumar 1.")
        if (isinstance(self.min_available_signals, bool)
                or not isinstance(self.min_available_signals, int)
                or not 1 <= self.min_available_signals <= len(weights)):
            raise ValueError("El mínimo de señales debe estar entre 1 y 5.")
        if (isinstance(self.min_known_requirements, bool)
                or not isinstance(self.min_known_requirements, int)
                or self.min_known_requirements < 0):
            raise ValueError("El mínimo de requisitos conocidos no puede ser negativo.")
        if not isinstance(self.eligibility, EligibilityPolicy):
            raise TypeError("Se requiere EligibilityPolicy.")

    @property
    def weights(self) -> dict[str, float]:
        return {
            "required_skills": self.required_weight,
            "complementarity": self.complementarity_weight,
            "preferred_skills": self.preferred_weight,
            "semantic_similarity": self.semantic_weight,
            "interests": self.interest_weight,
        }
