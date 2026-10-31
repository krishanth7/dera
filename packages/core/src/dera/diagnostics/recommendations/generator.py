"""DERA Diagnostics — Recommendation Generator.

Orchestrates deterministic recommendation assembly by matching findings against
the recommendation catalog, applying templates, and validating safety bounds.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from dera.diagnostics.recommendations.catalog import get_recommendation_for_rule
from dera.diagnostics.recommendations.safety import validate_recommendation_safety
from dera.diagnostics.recommendations.templates import format_recommendation_action

if TYPE_CHECKING:
    from dera.diagnostics.models import DiagnosticFinding


@dataclass(frozen=True)
class StructuredRecommendation:
    """Complete, advisory engineering recommendation supporting a diagnostic finding."""

    recommendation_id: str
    rule_id: str
    title: str
    description: str
    suggested_action: str
    risk_considerations: str
    verification_steps: tuple[str, ...]
    limitations: str
    version: str = "1.0.0"
    is_advisory: bool = True

    def __post_init__(self) -> None:
        validate_recommendation_safety(self.suggested_action)
        validate_recommendation_safety(self.description)

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "recommendation_id": self.recommendation_id,
            "rule_id": self.rule_id,
            "title": self.title,
            "description": self.description,
            "suggested_action": self.suggested_action,
            "risk_considerations": self.risk_considerations,
            "verification_steps": list(self.verification_steps),
            "limitations": self.limitations,
            "version": self.version,
            "is_advisory": self.is_advisory,
        }


def generate_structured_recommendation(
    finding: DiagnosticFinding,
) -> StructuredRecommendation | None:
    """Generates a structured recommendation for a diagnostic finding.

    Falls back to a safe default if no explicit catalog entry matches.
    """
    entry = get_recommendation_for_rule(finding.rule_id)
    if entry is not None:
        action = format_recommendation_action(entry, finding)
        return StructuredRecommendation(
            recommendation_id=entry.recommendation_id,
            rule_id=finding.rule_id,
            title=entry.title,
            description=entry.description,
            suggested_action=action,
            risk_considerations=entry.risk_considerations,
            verification_steps=entry.verification_steps,
            limitations=entry.limitations,
            version=entry.version,
            is_advisory=True,
        )

    # Safe fallback if finding has a recommendation string
    if finding.recommendation:
        rec_text = finding.recommendation.strip()
        validate_recommendation_safety(rec_text)
        return StructuredRecommendation(
            recommendation_id=f"REC-{finding.rule_id}",
            rule_id=finding.rule_id,
            title=f"Remediation Guidance for {finding.rule_id}",
            description=finding.description,
            suggested_action=rec_text,
            risk_considerations="Review schema migration impact prior to applying changes.",
            verification_steps=("Verify schema state after changes are applied.",),
            limitations="Advisory guidance generated from rule default recommendation.",
            version="1.0.0",
            is_advisory=True,
        )

    return None
