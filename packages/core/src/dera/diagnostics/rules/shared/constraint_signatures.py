"""Canonical constraint signatures and structural validation utilities.

Provides deterministic constraint validation, missing column reference detection,
duplicate constraint identification, and primary key redundancy analysis.
"""

from __future__ import annotations

from typing import Any


def validate_column_references_exist(
    table: Any, column_names: tuple[str, ...] | list[str]
) -> tuple[bool, tuple[str, ...]]:
    """Checks whether referenced column names exist on the parent canonical table.

    Returns:
        (True, ()) if all column names exist.
        (False, (missing_col_1, missing_col_2, ...)) if any column names are absent.
    """
    table_cols = getattr(table, "columns", ())
    existing_cols = {str(getattr(c, "name", c)).strip().lower() for c in table_cols}
    missing: list[str] = []

    for col in column_names:
        if str(col).strip().lower() not in existing_cols:
            missing.append(str(col))

    if missing:
        return False, tuple(sorted(missing))
    return True, ()


def does_unique_constraint_duplicate_pk(table: Any, uq: Any) -> bool:
    """Checks whether a UNIQUE constraint duplicates the table's declared PRIMARY KEY columns."""
    pk = getattr(table, "primary_key", None)
    if not pk:
        return False

    pk_cols_raw = getattr(pk, "columns", None) or getattr(pk, "column_names", ())
    uq_cols_raw = getattr(uq, "columns", None) or getattr(uq, "column_names", ())

    pk_cols = tuple(str(c).strip().lower() for c in pk_cols_raw)
    uq_cols = tuple(str(c).strip().lower() for c in uq_cols_raw)

    return bool(pk_cols and uq_cols and pk_cols == uq_cols)


def are_unique_constraints_duplicate(uq1: Any, uq2: Any) -> bool:
    """Checks whether two UNIQUE constraints on the same table enforce identical column sets."""
    if uq1 is uq2:
        return False

    id1 = getattr(uq1, "id", None)
    id2 = getattr(uq2, "id", None)
    if id1 and id2 and id1 == id2:
        return False

    cols1_raw = getattr(uq1, "columns", None) or getattr(uq1, "column_names", ())
    cols2_raw = getattr(uq2, "columns", None) or getattr(uq2, "column_names", ())

    cols1 = tuple(str(c).strip().lower() for c in cols1_raw)
    cols2 = tuple(str(c).strip().lower() for c in cols2_raw)

    return bool(cols1 and cols2 and cols1 == cols2)
