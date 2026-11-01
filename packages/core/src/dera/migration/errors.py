"""DERA Migration — Phase 9.2 Domain Exceptions.

Defines secure, informative exception types for migration risk analysis.
"""

from __future__ import annotations


class MigrationRiskAnalysisError(Exception):
    """Base exception for all migration risk analysis failures."""

    def __init__(self, message: str, code: str = "RISK_ANALYSIS_ERROR") -> None:
        super().__init__(message)
        self.message = message
        self.code = code


class InvalidComparisonReportError(MigrationRiskAnalysisError):
    """Raised when an input comparison report is invalid or missing required data."""

    def __init__(self, message: str) -> None:
        super().__init__(message, code="INVALID_COMPARISON_REPORT")


class RiskResourceLimitExceededError(MigrationRiskAnalysisError):
    """Raised when analysis operations exceed safety bounds."""

    def __init__(self, message: str, limit_name: str, actual_value: int, max_value: int) -> None:
        super().__init__(message, code="RISK_LIMIT_EXCEEDED")
        self.limit_name = limit_name
        self.actual_value = actual_value
        self.max_value = max_value


class IncompleteGraphMetadataError(MigrationRiskAnalysisError):
    """Raised when dependency graph traversal encounters unresolvable critical references."""

    def __init__(self, message: str) -> None:
        super().__init__(message, code="INCOMPLETE_GRAPH_METADATA")
