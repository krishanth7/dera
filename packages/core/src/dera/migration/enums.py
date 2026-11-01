"""DERA Migration — Phase 9.2 Enumerations and Classifications.

Defines strongly typed enumerations for change classifications, compatibility
levels, risk dimensions, review priority, evidence certainty, and reversibility.
"""

from __future__ import annotations

from enum import StrEnum


class StructuralChangeCategory(StrEnum):
    """Broad categorization of a structural change."""

    ADDITIVE = "ADDITIVE"
    REMOVAL = "REMOVAL"
    MODIFICATION = "MODIFICATION"
    CONSTRAINT_CHANGE = "CONSTRAINT_CHANGE"
    INDEX_CHANGE = "INDEX_CHANGE"
    RELATIONSHIP_CHANGE = "RELATIONSHIP_CHANGE"
    NAMESPACE_CHANGE = "NAMESPACE_CHANGE"
    DEFINITION_CHANGE = "DEFINITION_CHANGE"


class CompatibilityLevel(StrEnum):
    """Assessment of structural backward compatibility."""

    COMPATIBLE_WITH_KNOWN_METADATA = "COMPATIBLE_WITH_KNOWN_METADATA"
    POTENTIALLY_BREAKING = "POTENTIALLY_BREAKING"
    BREAKING_UNDER_STATED_CONDITIONS = "BREAKING_UNDER_STATED_CONDITIONS"
    REQUIRES_REVIEW = "REQUIRES_REVIEW"
    INDETERMINATE = "INDETERMINATE"
    UNSUPPORTED = "UNSUPPORTED"


class RiskDimension(StrEnum):
    """Independent risk evaluation perspectives."""

    DATA_PRESERVATION = "DATA_PRESERVATION"
    SCHEMA_COMPATIBILITY = "SCHEMA_COMPATIBILITY"
    APPLICATION_COMPATIBILITY = "APPLICATION_COMPATIBILITY"
    DEPENDENCY_IMPACT = "DEPENDENCY_IMPACT"
    MIGRATION_EXECUTION_COMPLEXITY = "MIGRATION_EXECUTION_COMPLEXITY"
    OPERATIONAL_AVAILABILITY = "OPERATIONAL_AVAILABILITY"
    REVERSIBILITY = "REVERSIBILITY"


class ReviewPriority(StrEnum):
    """Actionable review prioritization for database engineers."""

    P1_CRITICAL = "P1_CRITICAL"
    P2_HIGH = "P2_HIGH"
    P3_MEDIUM = "P3_MEDIUM"
    P4_LOW = "P4_LOW"
    P5_INFORMATIONAL = "P5_INFORMATIONAL"

    @property
    def rank(self) -> int:
        """Numerical rank for deterministic priority sorting (P1 first)."""
        ranks = {
            ReviewPriority.P1_CRITICAL: 1,
            ReviewPriority.P2_HIGH: 2,
            ReviewPriority.P3_MEDIUM: 3,
            ReviewPriority.P4_LOW: 4,
            ReviewPriority.P5_INFORMATIONAL: 5,
        }
        return ranks.get(self, 99)


class RiskEvidenceCertainty(StrEnum):
    """Degree of certainty backed by verified metadata."""

    VERIFIED = "VERIFIED"
    CONDITIONAL = "CONDITIONAL"
    INCOMPLETE = "INCOMPLETE"
    UNSUPPORTED = "UNSUPPORTED"
    NOT_EVALUATED = "NOT_EVALUATED"


class ReversibilityClassification(StrEnum):
    """Classification of whether the change can be rolled back safely."""

    POTENTIALLY_REVERSIBLE = "POTENTIALLY_REVERSIBLE"
    REVERSIBLE_UNDER_STATED_CONDITIONS = "REVERSIBLE_UNDER_STATED_CONDITIONS"
    REQUIRES_PRESERVED_DATA = "REQUIRES_PRESERVED_DATA"
    POTENTIALLY_IRREVERSIBLE = "POTENTIALLY_IRREVERSIBLE"
    INDETERMINATE = "INDETERMINATE"


class TypeConversionSafety(StrEnum):
    """Dialect-aware safety rating for data type alterations."""

    SAFE_WIDENING = "SAFE_WIDENING"
    POTENTIAL_NARROWING = "POTENTIAL_NARROWING"
    EXPLICIT_CONVERSION_REQUIRED = "EXPLICIT_CONVERSION_REQUIRED"
    UNSUPPORTED_CONVERSION = "UNSUPPORTED_CONVERSION"
    UNKNOWN = "UNKNOWN"
