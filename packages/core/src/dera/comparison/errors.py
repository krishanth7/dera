"""DERA Comparison — Phase 9.1 Domain Exceptions.

Defines clear, secure exception types for schema snapshot comparison,
preventing secret/credential leakage and ensuring explainable failure modes.
"""

from __future__ import annotations


class ComparisonError(Exception):
    """Base exception for all schema comparison failures."""

    def __init__(self, message: str, code: str = "COMPARISON_ERROR") -> None:
        super().__init__(message)
        self.message = message
        self.code = code


class InvalidSnapshotError(ComparisonError):
    """Raised when an input snapshot fails structural or schema validation."""

    def __init__(self, message: str) -> None:
        super().__init__(message, code="INVALID_SNAPSHOT")


class IncompatibleSnapshotError(ComparisonError):
    """Raised when snapshots cannot be compared due to contract or version mismatch."""

    def __init__(self, message: str) -> None:
        super().__init__(message, code="INCOMPATIBLE_SNAPSHOT")


class UnsupportedEngineComparisonError(ComparisonError):
    """Raised when attempting a cross-engine comparison without verified compatibility."""

    def __init__(self, baseline_engine: str, target_engine: str) -> None:
        message = (
            f"Cross-engine comparison between '{baseline_engine}' and '{target_engine}' "
            "is not supported in Phase 9.1."
        )
        super().__init__(message, code="UNSUPPORTED_ENGINE_COMPARISON")
        self.baseline_engine = baseline_engine
        self.target_engine = target_engine


class MissingMetadataError(ComparisonError):
    """Raised when required structural metadata is missing from a snapshot."""

    def __init__(self, message: str) -> None:
        super().__init__(message, code="MISSING_METADATA")


class ComparisonResourceLimitExceededError(ComparisonError):
    """Raised when comparison input or output exceeds defined safety bounds."""

    def __init__(self, message: str, limit_name: str, actual_value: int, max_value: int) -> None:
        super().__init__(message, code="RESOURCE_LIMIT_EXCEEDED")
        self.limit_name = limit_name
        self.actual_value = actual_value
        self.max_value = max_value
