"""DERA Diagnostics — Recommendations Subsystem.

Exposes structured recommendation catalog, deterministic assembly, and safety checks.
"""

from __future__ import annotations

from dera.diagnostics.recommendations.catalog import (
    RECOMMENDATION_CATALOG,
    RECOMMENDATION_CATALOG_VERSION,
    RecommendationEntry,
    get_recommendation_for_rule,
)
from dera.diagnostics.recommendations.generator import (
    StructuredRecommendation,
    generate_structured_recommendation,
)
from dera.diagnostics.recommendations.safety import (
    RecommendationSafetyViolationError,
    validate_recommendation_safety,
)

__all__ = [
    "RECOMMENDATION_CATALOG",
    "RECOMMENDATION_CATALOG_VERSION",
    "RecommendationEntry",
    "RecommendationSafetyViolationError",
    "StructuredRecommendation",
    "generate_structured_recommendation",
    "get_recommendation_for_rule",
    "validate_recommendation_safety",
]
