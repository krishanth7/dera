"""DERA Diagnostics — Namespace Distribution Metrics Calculator.

Computes object allocation, schema concentration, and namespace imbalance ratios
to identify monolithic database schemas and empty namespaces.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from dera.diagnostics.metrics.models import NamespaceMaintainabilityMetrics


def compute_namespace_metrics(
    namespaces: Sequence[Any],
    total_database_tables: int | None = None,
) -> tuple[NamespaceMaintainabilityMetrics, ...]:
    """Computes distribution metrics across database namespaces/schemas."""
    ns_list = list(namespaces)
    if not ns_list:
        return ()

    all_table_count = (
        total_database_tables
        if total_database_tables is not None
        else sum(len(getattr(ns, "tables", ())) for ns in ns_list)
    )

    results: list[NamespaceMaintainabilityMetrics] = []
    for ns in ns_list:
        ns_name = str(getattr(ns, "name", "<unnamed_namespace>"))
        t_count = len(getattr(ns, "tables", ()))
        v_count = len(getattr(ns, "views", ()))
        total_objs = t_count + v_count

        share = round(t_count / all_table_count, 4) if all_table_count > 0 else 0.0

        results.append(
            NamespaceMaintainabilityMetrics(
                namespace_name=ns_name,
                table_count=t_count,
                view_count=v_count,
                total_objects=total_objs,
                object_share_ratio=share,
            )
        )

    return tuple(sorted(results, key=lambda m: m.namespace_name))


def compute_namespace_imbalance_ratio(
    metrics: Sequence[NamespaceMaintainabilityMetrics],
) -> float:
    """Calculates the maximum concentration of tables residing in a single namespace.

    Returns 0.0 if there is only one namespace (e.g. standard SQLite or single-schema databases).
    """
    m_list = list(metrics)
    if len(m_list) <= 1:
        return 0.0

    total_tables = sum(m.table_count for m in m_list)
    if total_tables == 0:
        return 0.0

    max_tables_in_single_ns = max(m.table_count for m in m_list)
    return round(max_tables_in_single_ns / total_tables, 4)
