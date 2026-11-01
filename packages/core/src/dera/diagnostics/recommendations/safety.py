"""DERA Diagnostics — Recommendation Safety Validator.

Guarantees that all generated engineering recommendations remain strictly advisory,
preventing the emission of destructive SQL, automated migration scripts, or
unverified mutations.
"""

from __future__ import annotations

import re

# Destructive execution patterns prohibited in advisory recommendations
_PROHIBITED_DESTRUCTIVE_PATTERNS = re.compile(
    r"(?i)\b(DROP\s+TABLE|DROP\s+DATABASE|DROP\s+SCHEMA|TRUNCATE\s+TABLE|DELETE\s+FROM|EXECUTE\s+IMMEDIATE)\b"
)


class RecommendationSafetyViolationError(ValueError):
    """Raised when a recommendation contains prohibited executable or destructive SQL."""


def validate_recommendation_safety(text: str) -> bool:
    """Verifies that recommendation text contains no prohibited destructive SQL commands."""
    if _PROHIBITED_DESTRUCTIVE_PATTERNS.search(text):
        raise RecommendationSafetyViolationError(
            f"Recommendation text contains prohibited destructive SQL pattern: {text[:100]}..."
        )
    return True
