"""DERA Comparison — Phase 9.1 Metrics Summary Calculation.

Computes accurate, non-redundant change counts across change types,
object categories, and namespaces.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from collections import Counter

from dera.comparison.enums import ComparisonChangeType
from dera.comparison.models import ComparisonSummary

if TYPE_CHECKING:
    from dera.comparison.models import SchemaChange


def compute_comparison_summary(
    changes: tuple[SchemaChange, ...] | list[SchemaChange],
    evaluated_unchanged_count: int = 0,
) -> ComparisonSummary:
    """Aggregate difference statistics across a set of sorted SchemaChange records.

    Avoids double counting child object changes as parent table additions/removals.
    """
    total_added = 0
    total_removed = 0
    total_modified = 0
    total_unsupported = 0
    total_indeterminate = 0

    by_type: Counter[str] = Counter()
    by_namespace: Counter[str] = Counter()

    for chg in changes:
        by_type[chg.object_type.value] += 1
        if chg.namespace:
            by_namespace[chg.namespace] += 1

        if chg.change_type == ComparisonChangeType.ADDED:
            total_added += 1
        elif chg.change_type == ComparisonChangeType.REMOVED:
            total_removed += 1
        elif chg.change_type == ComparisonChangeType.MODIFIED:
            total_modified += 1
        elif chg.change_type == ComparisonChangeType.UNSUPPORTED:
            total_unsupported += 1
        elif chg.change_type == ComparisonChangeType.INDETERMINATE:
            total_indeterminate += 1

    return ComparisonSummary(
        total_changes=len(changes),
        total_added=total_added,
        total_removed=total_removed,
        total_modified=total_modified,
        total_unchanged=evaluated_unchanged_count,
        total_unsupported=total_unsupported,
        total_indeterminate=total_indeterminate,
        changes_by_object_type=dict(sorted(by_type.items())),
        changes_by_namespace=dict(sorted(by_namespace.items())),
    )
