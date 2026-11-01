"""DERA Comparison — Phase 9.1 Deterministic Ordering.

Sorts schema changes and property differences according to strict, predictable rules:
1. Object type hierarchy: NAMESPACE -> TABLE -> COLUMN -> PRIMARY_KEY -> UNIQUE_CONSTRAINT -> FOREIGN_KEY -> CHECK_CONSTRAINT -> INDEX -> VIEW -> TRIGGER -> RELATIONSHIP
2. Namespace (lexicographical)
3. Parent name / Parent ID (lexicographical)
4. Native object name (lexicographical)
5. Canonical ObjectId (lexicographical)
6. ChangeType (REMOVED -> MODIFIED -> ADDED -> UNCHANGED)
7. Property name for property-level differences
8. Fingerprint as final tiebreaker
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from dera.comparison.enums import ComparisonChangeType, ComparisonObjectType
from dera.comparison.evidence import PropertyDifference

if TYPE_CHECKING:
    from dera.comparison.models import SchemaChange

OBJECT_TYPE_SORT_ORDER: dict[ComparisonObjectType, int] = {
    ComparisonObjectType.NAMESPACE: 10,
    ComparisonObjectType.TABLE: 20,
    ComparisonObjectType.COLUMN: 30,
    ComparisonObjectType.PRIMARY_KEY: 40,
    ComparisonObjectType.UNIQUE_CONSTRAINT: 50,
    ComparisonObjectType.FOREIGN_KEY: 60,
    ComparisonObjectType.CHECK_CONSTRAINT: 70,
    ComparisonObjectType.INDEX: 80,
    ComparisonObjectType.VIEW: 90,
    ComparisonObjectType.TRIGGER: 100,
    ComparisonObjectType.RELATIONSHIP: 110,
}

CHANGE_TYPE_SORT_ORDER: dict[ComparisonChangeType, int] = {
    ComparisonChangeType.REMOVED: 10,
    ComparisonChangeType.MODIFIED: 20,
    ComparisonChangeType.ADDED: 30,
    ComparisonChangeType.UNCHANGED: 40,
    ComparisonChangeType.UNSUPPORTED: 50,
    ComparisonChangeType.INDETERMINATE: 60,
}


def sort_property_differences(
    differences: tuple[PropertyDifference, ...] | list[PropertyDifference],
) -> tuple[PropertyDifference, ...]:
    """Sort property differences lexicographically by property_name."""
    return tuple(sorted(differences, key=lambda p: p.property_name))


def sort_schema_changes(
    changes: tuple[SchemaChange, ...] | list[SchemaChange],
) -> tuple[SchemaChange, ...]:
    """Sort a collection of SchemaChanges deterministically."""
    return tuple(
        sorted(
            changes,
            key=lambda c: (
                OBJECT_TYPE_SORT_ORDER.get(c.object_type, 999),
                c.namespace,
                c.parent_name or "",
                c.parent_canonical_id or "",
                c.name,
                c.canonical_id,
                CHANGE_TYPE_SORT_ORDER.get(c.change_type, 999),
                c.fingerprint,
            ),
        )
    )
