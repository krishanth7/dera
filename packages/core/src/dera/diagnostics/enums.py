"""DERA Diagnostics — Enumerations and Constant Classifications.

Provides typed enumerations for diagnostic severity, rule applicability,
evaluation outcomes, and functional rule categories.
"""

from __future__ import annotations

from enum import StrEnum


class DiagnosticSeverity(StrEnum):
    """Deterministic severity classification for diagnostic findings."""

    INFORMATIONAL = "INFORMATIONAL"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

    @classmethod
    def from_legacy(cls, legacy_val: str) -> DiagnosticSeverity:
        """Maps legacy RuleSeverity strings to DiagnosticSeverity."""
        mapping = {
            "INFO": cls.INFORMATIONAL,
            "WARNING": cls.MEDIUM,
            "ERROR": cls.HIGH,
            "CRITICAL": cls.CRITICAL,
        }
        return mapping.get(legacy_val.upper(), cls.INFORMATIONAL)

    @property
    def rank(self) -> int:
        """Numerical rank for deterministic severity-first sorting."""
        ranks = {
            DiagnosticSeverity.CRITICAL: 5,
            DiagnosticSeverity.HIGH: 4,
            DiagnosticSeverity.MEDIUM: 3,
            DiagnosticSeverity.LOW: 2,
            DiagnosticSeverity.INFORMATIONAL: 1,
        }
        return ranks.get(self, 0)


class RuleSeverity(StrEnum):
    """Backwards-compatibility alias for legacy Phase 1-6 diagnostic severity."""

    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


class ApplicabilityStatus(StrEnum):
    """Outcome of determining whether a rule can evaluate against a context."""

    APPLICABLE = "APPLICABLE"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    UNSUPPORTED = "UNSUPPORTED"
    INSUFFICIENT_METADATA = "INSUFFICIENT_METADATA"


class EvaluationStatus(StrEnum):
    """Execution status returned by a diagnostic rule."""

    PASS = "PASS"
    FINDINGS_DETECTED = "FINDINGS_DETECTED"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    UNSUPPORTED = "UNSUPPORTED"
    INSUFFICIENT_METADATA = "INSUFFICIENT_METADATA"
    EVALUATION_ERROR = "EVALUATION_ERROR"


class RuleCategory(StrEnum):
    """Functional taxonomy for diagnostic rules."""

    STRUCTURAL_INTEGRITY = "STRUCTURAL_INTEGRITY"
    CONSTRAINTS = "CONSTRAINTS"
    INDEXES = "INDEXES"
    RELATIONSHIPS = "RELATIONSHIPS"
    DEPENDENCIES = "DEPENDENCIES"
    MAINTAINABILITY = "MAINTAINABILITY"
    METADATA_COMPLETENESS = "METADATA_COMPLETENESS"
    ENGINE_SPECIFIC = "ENGINE_SPECIFIC"
