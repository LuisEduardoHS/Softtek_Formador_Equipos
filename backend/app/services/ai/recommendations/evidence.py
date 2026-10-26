"""Shared evidence sufficiency label for recommendation audiences."""

from typing import Literal

from app.services.ai.matching.policy import RankingPolicy
from app.services.ai.matching.schemas import MatchResult


EvidenceGroup = Literal["sufficient_evidence", "insufficient_evidence"]


def evidence_group(result: MatchResult, policy: RankingPolicy) -> EvidenceGroup:
    """Mirror the matching policy's available-signal gate without using its score."""
    available = sum(
        result.score_components.get(name) is not None and weight > 0
        for name, weight in policy.weights.items()
    )
    if (available >= policy.min_available_signals
            and result.evidence_coverage.known >= policy.min_known_requirements):
        return "sufficient_evidence"
    return "insufficient_evidence"
