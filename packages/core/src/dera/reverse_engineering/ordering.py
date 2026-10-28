"""DERA Reverse Engineering — Phase 6.1 Deterministic Ordering.

Provides deterministic, reproducible sorting algorithms for all schema collections
and typed object references. Guarantees that schema representations built from identical
metadata produce identical ordering invariant to catalog query order or hash seeds.
"""

from __future__ import annotations

from collections.abc import Sequence

from dera.metadata.ordering import (
    sort_columns,
    sort_constraints,
    sort_foreign_key_mappings,
    sort_foreign_keys,
    sort_index_terms,
    sort_indexes,
    sort_namespaces,
    sort_tables,
    sort_triggers,
    sort_views,
)
from dera.reverse_engineering.references import ForeignKeyReference, TypedRef


def sort_references(references: Sequence[TypedRef]) -> tuple[TypedRef, ...]:
    """Sort TypedRef collection deterministically by expected_kind ASC, then target_id ASC."""
    return tuple(
        sorted(
            references,
            key=lambda ref: (
                ref.expected_kind.lower(),
                ref.target_id,
                ref.status.value,
            ),
        )
    )


def sort_foreign_key_references(
    references: Sequence[ForeignKeyReference],
) -> tuple[ForeignKeyReference, ...]:
    """Sort ForeignKeyReference collection deterministically.

    Order:
    1. foreign_key_name ASC (case-insensitive, then exact)
    2. source_table_name ASC
    3. referenced_table_name ASC
    4. foreign_key_id ASC
    """
    return tuple(
        sorted(
            references,
            key=lambda fk: (
                fk.foreign_key_name.lower(),
                fk.foreign_key_name,
                fk.source_table_name.lower(),
                fk.referenced_table_name.lower(),
                fk.foreign_key_id,
            ),
        )
    )


def sort_object_ids(object_ids: Sequence[str]) -> tuple[str, ...]:
    """Sort a sequence of canonical ObjectIds lexicographically."""
    return tuple(sorted(object_ids))


__all__ = [
    "sort_columns",
    "sort_constraints",
    "sort_foreign_key_mappings",
    "sort_foreign_key_references",
    "sort_foreign_keys",
    "sort_index_terms",
    "sort_indexes",
    "sort_namespaces",
    "sort_object_ids",
    "sort_references",
    "sort_tables",
    "sort_triggers",
    "sort_views",
]
