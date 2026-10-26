"""Pure organizer recommendations built on the matching motor."""

from .candidates import recommend_candidates
from .contracts import (CandidateRecommendation, OrganizerRecommendationContext,
                        ProjectRecommendation, UserRecommendationContext)
from .explanations import personalize_recommendation
from .freshness import (ActionRecord, SourceVersions, assess_freshness,
                        build_snapshot_fingerprint, classify_pair_records,
                        context_action_state, is_repeated_recommendation,
                        same_action_pair)
from .projects import recommend_projects

__all__ = [
    "CandidateRecommendation", "OrganizerRecommendationContext", "recommend_candidates",
    "ProjectRecommendation", "UserRecommendationContext", "recommend_projects",
    "personalize_recommendation",
    "ActionRecord", "SourceVersions", "assess_freshness",
    "build_snapshot_fingerprint", "classify_pair_records", "context_action_state",
    "is_repeated_recommendation", "same_action_pair",
]
