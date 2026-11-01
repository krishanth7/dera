"""DERA Comparison — Phase 9.1 Enumerations.

Defines strongly typed enumerations for change types, comparison status,
granularity, object kinds, and metadata completeness in schema comparison.
"""

from __future__ import annotations

from enum import StrEnum


class ComparisonChangeType(StrEnum):
    """Classification of detected schema modifications."""

    ADDED = "ADDED"
    REMOVED = "REMOVED"
    MODIFIED = "MODIFIED"
    UNCHANGED = "UNCHANGED"
    UNSUPPORTED = "UNSUPPORTED"
    INDETERMINATE = "INDETERMINATE"


class ComparisonStatus(StrEnum):
    """Overall status of comparison execution."""

    IDENTICAL = "IDENTICAL"
    DIFFERENCES_FOUND = "DIFFERENCES_FOUND"
    PARTIAL = "PARTIAL"
    UNSUPPORTED = "UNSUPPORTED"
    ERROR = "ERROR"


class DiffGranularity(StrEnum):
    """Granularity of reported differences."""

    OBJECT = "OBJECT"
    PROPERTY = "PROPERTY"
    STRUCTURAL = "STRUCTURAL"


class ComparisonObjectType(StrEnum):
    """Categorization of canonical schema objects subject to comparison."""

    NAMESPACE = "NAMESPACE"
    TABLE = "TABLE"
    COLUMN = "COLUMN"
    PRIMARY_KEY = "PRIMARY_KEY"
    FOREIGN_KEY = "FOREIGN_KEY"
    UNIQUE_CONSTRAINT = "UNIQUE_CONSTRAINT"
    CHECK_CONSTRAINT = "CHECK_CONSTRAINT"
    INDEX = "INDEX"
    RELATIONSHIP = "RELATIONSHIP"
    VIEW = "VIEW"
    TRIGGER = "TRIGGER"


class PropertyComparisonStatus(StrEnum):
    """Outcome of comparing an individual object property."""

    EQUAL = "EQUAL"
    MODIFIED = "MODIFIED"
    BEFORE_UNKNOWN = "BEFORE_UNKNOWN"
    AFTER_UNKNOWN = "AFTER_UNKNOWN"
    BOTH_UNKNOWN = "BOTH_UNKNOWN"
    UNSUPPORTED = "UNSUPPORTED"
