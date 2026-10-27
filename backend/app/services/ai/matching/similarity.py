"""Cosine signal for already generated, compatible embeddings.

This module neither generates vectors nor assigns a ranking score.
"""

import math
from collections.abc import Sequence


class InvalidEmbeddingError(ValueError):
    """A supplied vector is malformed or cannot define a cosine."""


def _validated_vector(vector: Sequence[float]) -> tuple[float, ...]:
    if isinstance(vector, (str, bytes)) or not isinstance(vector, Sequence) or not vector:
        raise InvalidEmbeddingError("El embedding debe ser una secuencia numérica no vacía.")
    if any(isinstance(value, bool) or not isinstance(value, (int, float))
           or not math.isfinite(value) for value in vector):
        raise InvalidEmbeddingError("El embedding debe contener solo números finitos.")
    values = tuple(float(value) for value in vector)
    if not math.isfinite(math.hypot(*values)) or math.hypot(*values) == 0:
        raise InvalidEmbeddingError("El embedding debe tener norma finita mayor que cero.")
    return values


def cosine_similarity(
    left: Sequence[float] | None,
    right: Sequence[float] | None,
    *,
    left_model: str | None,
    right_model: str | None,
    left_version: str | None,
    right_version: str | None,
) -> float | None:
    """Return cosine, or None when either vector/metadata is unavailable or incompatible.

    Versions identify the source/processing revision, so a stale vector is not
    silently compared with a current one. Malformed supplied vectors raise a
    controlled error. A valid orthogonal comparison genuinely returns zero.
    """
    if left is None or right is None:
        return None
    a = _validated_vector(left)
    b = _validated_vector(right)
    if len(a) != len(b):
        return None
    if not all(isinstance(value, str) and value.strip() for value in
               (left_model, right_model, left_version, right_version)):
        return None
    if left_model != right_model or left_version != right_version:
        return None
    if left_model in {"nomic-embed-text", "nomic-embed-text:latest"} and len(a) != 768:
        return None
    # Scaling before multiplication also keeps very large finite vectors safe.
    a_scale = max(abs(value) for value in a)
    b_scale = max(abs(value) for value in b)
    a_unit = tuple(value / a_scale for value in a)
    b_unit = tuple(value / b_scale for value in b)
    denominator = math.hypot(*a_unit) * math.hypot(*b_unit)
    similarity = math.fsum(x * y for x, y in zip(a_unit, b_unit)) / denominator
    return max(-1.0, min(1.0, similarity))
