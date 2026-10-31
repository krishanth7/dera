"""DERA Diagnostics — Table Maintainability Metrics Calculator.

Computes column composition, nullability ratios, default expressions,
and LOB (large text/binary) column distributions per table.
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from typing import Any

from dera.diagnostics.metrics.models import TableMaintainabilityMetrics

# Regex pattern matching large object (LOB) data types
_LOB_TYPE_PATTERN = re.compile(
    r"(?:\b(text|longtext|mediumtext|clob|blob|longblob|mediumblob|bytea|image)\b|varbinary\(max\)|varchar\(max\))",
    re.IGNORECASE,
)


def is_lob_column(col: Any) -> bool:
    """Detects whether a column uses an unbounded large text or binary storage type."""
    native_type = str(getattr(col, "native_data_type", "")).strip().lower()
    if _LOB_TYPE_PATTERN.search(native_type):
        return True

    # Also check canonical type if native type is generic
    canonical_type = str(getattr(col, "canonical_type", "")).upper()
    if canonical_type in ("TEXT", "BINARY") and "(" not in native_type:
        return True

    return False


def compute_table_metrics(table: Any) -> TableMaintainabilityMetrics:
    """Computes maintainability attributes for a single table."""
    table_id = str(getattr(table, "id", getattr(table, "name", "<unnamed>")))
    table_name = str(getattr(table, "name", "<unnamed>"))
    namespace = str(getattr(table, "schema_name", getattr(table, "namespace", "public")))

    columns = list(getattr(table, "columns", ()))
    column_count = len(columns)

    nullable_count = 0
    default_count = 0
    identity_count = 0
    generated_count = 0
    lob_count = 0

    for col in columns:
        is_nullable = getattr(col, "is_nullable", True)
        if is_nullable is not False:
            nullable_count += 1

        if bool(getattr(col, "default_expression", None)):
            default_count += 1

        if bool(getattr(col, "is_identity", False)):
            identity_count += 1

        is_gen = bool(getattr(col, "is_generated", False))
        gen_mode = str(getattr(col, "generation_mode", "NONE")).upper()
        if is_gen or (gen_mode not in ("NONE", "")):
            generated_count += 1

        if is_lob_column(col):
            lob_count += 1

    nullability_ratio = round(nullable_count / column_count, 4) if column_count > 0 else 0.0

    return TableMaintainabilityMetrics(
        object_id=table_id,
        table_name=table_name,
        namespace=namespace,
        column_count=column_count,
        nullable_column_count=nullable_count,
        nullability_ratio=nullability_ratio,
        default_expression_count=default_count,
        identity_column_count=identity_count,
        generated_column_count=generated_count,
        lob_column_count=lob_count,
    )


def compute_all_table_metrics(tables: Sequence[Any]) -> tuple[TableMaintainabilityMetrics, ...]:
    """Computes maintainability metrics for an ordered sequence of tables."""
    return tuple(
        sorted(
            [compute_table_metrics(t) for t in tables],
            key=lambda m: (m.namespace, m.table_name, m.object_id),
        )
    )
