"""DERA Canonical Metadata Normalization & Identity — Deterministic Ordering.

Provides deterministic, reproducible sorting algorithms for all canonical schema collections.
Ensures identical output regardless of catalog query return order or Python hash seeds.
"""

from __future__ import annotations

from collections.abc import Sequence

from dera.metadata.models.column import CanonicalColumn
from dera.metadata.models.constraint import CanonicalConstraint
from dera.metadata.models.index import CanonicalIndex, CanonicalIndexTerm
from dera.metadata.models.namespace import CanonicalNamespace
from dera.metadata.models.relationship import CanonicalForeignKey, ForeignKeyMapping
from dera.metadata.models.table import CanonicalTable
from dera.metadata.models.trigger import CanonicalTrigger
from dera.metadata.models.view import CanonicalView


def sort_columns(columns: Sequence[CanonicalColumn]) -> tuple[CanonicalColumn, ...]:
    """Sort columns by ordinal_position ASC, then name ASC."""
    return tuple(sorted(columns, key=lambda c: (c.ordinal_position, c.name.lower(), c.name)))


def sort_constraints(
    constraints: Sequence[CanonicalConstraint],
) -> tuple[CanonicalConstraint, ...]:
    """Sort constraints by name ASC, then column tuple."""
    return tuple(
        sorted(
            constraints,
            key=lambda c: (c.name.lower(), c.name, tuple(col.lower() for col in c.columns)),
        )
    )


def sort_foreign_key_mappings(
    mappings: Sequence[ForeignKeyMapping],
) -> tuple[ForeignKeyMapping, ...]:
    """Sort foreign key column pairings by source_column ASC."""
    return tuple(
        sorted(
            mappings,
            key=lambda m: (m.source_column.lower(), m.source_column),
        )
    )


def sort_foreign_keys(
    foreign_keys: Sequence[CanonicalForeignKey],
) -> tuple[CanonicalForeignKey, ...]:
    """Sort foreign keys by name ASC, then referenced_table_name ASC."""
    return tuple(
        sorted(
            foreign_keys,
            key=lambda fk: (
                fk.name.lower(),
                fk.name,
                fk.referenced_table_name.lower(),
                tuple(col.lower() for col in fk.source_columns),
            ),
        )
    )


def sort_index_terms(
    terms: Sequence[CanonicalIndexTerm],
) -> tuple[CanonicalIndexTerm, ...]:
    """Sort index terms by ordinal_position ASC."""
    return tuple(
        sorted(
            terms,
            key=lambda t: (
                t.ordinal_position,
                (t.column_name or "").lower(),
                (t.expression or "").lower(),
            ),
        )
    )


def sort_indexes(indexes: Sequence[CanonicalIndex]) -> tuple[CanonicalIndex, ...]:
    """Sort indexes by name ASC, then is_primary DESC, then is_unique DESC."""
    return tuple(
        sorted(
            indexes,
            key=lambda idx: (
                0 if idx.is_primary else 1,
                0 if idx.is_unique else 1,
                idx.name.lower(),
                idx.name,
            ),
        )
    )


def sort_triggers(triggers: Sequence[CanonicalTrigger]) -> tuple[CanonicalTrigger, ...]:
    """Sort triggers by name ASC."""
    return tuple(sorted(triggers, key=lambda tr: (tr.name.lower(), tr.name)))


def sort_tables(tables: Sequence[CanonicalTable]) -> tuple[CanonicalTable, ...]:
    """Sort tables by name ASC."""
    return tuple(sorted(tables, key=lambda tbl: (tbl.name.lower(), tbl.name)))


def sort_views(views: Sequence[CanonicalView]) -> tuple[CanonicalView, ...]:
    """Sort views by name ASC."""
    return tuple(sorted(views, key=lambda v: (v.name.lower(), v.name)))


def sort_namespaces(namespaces: Sequence[CanonicalNamespace]) -> tuple[CanonicalNamespace, ...]:
    """Sort namespaces by name ASC."""
    return tuple(sorted(namespaces, key=lambda ns: (ns.name.lower(), ns.name)))
