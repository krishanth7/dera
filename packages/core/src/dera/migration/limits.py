"""DERA Migration — Phase 9.2 Resource Limits.

Enforces execution bounds on processed changes, graph reachability depths,
and generated risk assessments.
"""

from __future__ import annotations

from dataclasses import dataclass

from dera.migration.errors import RiskResourceLimitExceededError


@dataclass(frozen=True)
class MigrationRiskLimits:
    """Configurable resource safety boundaries for risk analysis."""

    max_changes_to_analyze: int = 50_000
    max_graph_traversal_depth: int = 50
    max_reachable_nodes: int = 10_000
    max_risk_assessments: int = 100_000

    def check_change_count(self, count: int) -> None:
        """Validate input change count."""
        if count > self.max_changes_to_analyze:
            raise RiskResourceLimitExceededError(
                message=f"Change count {count} exceeds safety limit of {self.max_changes_to_analyze}.",
                limit_name="max_changes_to_analyze",
                actual_value=count,
                max_value=self.max_changes_to_analyze,
            )

    def check_reachable_nodes(self, count: int) -> None:
        """Validate graph reachability node count."""
        if count > self.max_reachable_nodes:
            raise RiskResourceLimitExceededError(
                message=f"Reachable dependent node count {count} exceeds limit of {self.max_reachable_nodes}.",
                limit_name="max_reachable_nodes",
                actual_value=count,
                max_value=self.max_reachable_nodes,
            )

    def check_risk_assessments_count(self, count: int) -> None:
        """Validate generated risk assessment count."""
        if count > self.max_risk_assessments:
            raise RiskResourceLimitExceededError(
                message=f"Risk assessments count {count} exceeds limit of {self.max_risk_assessments}.",
                limit_name="max_risk_assessments",
                actual_value=count,
                max_value=self.max_risk_assessments,
            )
