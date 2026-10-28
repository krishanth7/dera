"""Deterministic multi-key ordering algorithms for Phase 6.2 Structural Reconstruction.

Ensures that reconstructed tables, columns, foreign keys, unique constraints, and check
constraints maintain mathematical repeatability invariant to dictionary or input sequence.
"""

from collections.abc import Sequence

from dera.reverse_engineering.reconstruction.models import (
    ReconstructedCheckConstraint,
    ReconstructedColumn,
    ReconstructedForeignKey,
    ReconstructedTable,
    ReconstructedUniqueConstraint,
)


def sort_columns(columns: Sequence[ReconstructedColumn]) -> tuple[ReconstructedColumn, ...]:
    """Sort columns strictly by ordinal position, with native name and ObjectId as tiebreakers."""
    sorted_cols = sorted(
        columns, key=lambda c: (c.ordinal_position, c.native_name, str(c.object_id))
    )
    return tuple(sorted_cols)


def sort_foreign_keys(
    fks: Sequence[ReconstructedForeignKey],
) -> tuple[ReconstructedForeignKey, ...]:
    """Sort foreign keys deterministically."""
    sorted_fks = sorted(
        fks,
        key=lambda k: (
            k.native_name or "",
            k.source_column_names,
            k.referenced_table_name,
            str(k.object_id),
        ),
    )
    return tuple(sorted_fks)


def sort_unique_constraints(
    uniques: Sequence[ReconstructedUniqueConstraint],
) -> tuple[ReconstructedUniqueConstraint, ...]:
    """Sort unique constraints deterministically."""
    sorted_u = sorted(
        uniques,
        key=lambda u: (
            u.native_name or "",
            u.column_names,
            str(u.object_id),
        ),
    )
    return tuple(sorted_u)


def sort_check_constraints(
    checks: Sequence[ReconstructedCheckConstraint],
) -> tuple[ReconstructedCheckConstraint, ...]:
    """Sort check constraints deterministically."""
    sorted_ck = sorted(
        checks,
        key=lambda ck: (
            ck.native_name or "",
            ck.expression,
            str(ck.object_id),
        ),
    )
    return tuple(sorted_ck)


def sort_tables(tables: Sequence[ReconstructedTable]) -> tuple[ReconstructedTable, ...]:
    """Sort tables deterministically by namespace, native name, and ObjectId."""
    sorted_t = sorted(
        tables,
        key=lambda t: (
            t.namespace,
            t.native_name,
            str(t.object_id),
        ),
    )
    return tuple(sorted_t)
