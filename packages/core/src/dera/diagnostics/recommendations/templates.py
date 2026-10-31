"""DERA Diagnostics — Recommendation Templates Engine.

Provides deterministic template formatting for parameterized engineering actions,
substituting object identifiers and evidence metrics safely without hallucinated content.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from dera.diagnostics.models import DiagnosticFinding
    from dera.diagnostics.recommendations.catalog import RecommendationEntry


def format_recommendation_action(
    entry: RecommendationEntry,
    finding: DiagnosticFinding,
) -> str:
    """Safely formats the catalog action with object context."""
    base_action = entry.suggested_action
    obj_id = finding.object_id

    # If the action has placeholders or needs specific contextualization
    if "{object_id}" in base_action:
        return base_action.replace("{object_id}", obj_id)

    # Prepend object context deterministically
    return f"For object '{obj_id}': {base_action}"
