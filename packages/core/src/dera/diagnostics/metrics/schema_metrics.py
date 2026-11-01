"""DERA Diagnostics — Schema Complexity Metrics Calculator.

Computes aggregated counts, ratios, and structural complexity statistics
for an inspected database schema.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from dera.diagnostics.metrics.models import SchemaComplexityMetrics


def compute_schema_complexity(
    tables: Sequence[Any],
    namespaces: Sequence[Any] | None = None,
) -> SchemaComplexityMetrics:
    """Computes deterministic schema complexity metrics from canonical objects."""
    ns_list = list(namespaces or ())
    table_list = list(tables)

    table_count = len(table_list)
    view_count = sum(len(getattr(ns, "views", ())) for ns in ns_list)
    column_count = sum(len(getattr(t, "columns", ())) for t in table_list)

    constraint_count = 0
    foreign_key_count = 0
    index_count = 0

    for t in table_list:
        if getattr(t, "primary_key", None) is not None:
            constraint_count += 1

        fks = getattr(t, "foreign_keys", ())
        foreign_key_count += len(fks)
        constraint_count += len(fks)

        uqs = getattr(t, "unique_constraints", ())
        constraint_count += len(uqs)

        cks = getattr(t, "check_constraints", ())
        constraint_count += len(cks)

        idxs = getattr(t, "indexes", ())
        index_count += len(idxs)

    namespace_count = len(ns_list) if ns_list else (1 if table_count > 0 else 0)

    avg_columns = round(column_count / table_count, 2) if table_count > 0 else 0.0
    avg_constraints = round(constraint_count / table_count, 2) if table_count > 0 else 0.0

    return SchemaComplexityMetrics(
        table_count=table_count,
        view_count=view_count,
        column_count=column_count,
        constraint_count=constraint_count,
        index_count=index_count,
        foreign_key_count=foreign_key_count,
        namespace_count=namespace_count,
        avg_columns_per_table=avg_columns,
        avg_constraints_per_table=avg_constraints,
    )
