"""DERA Diagnostics — Relational Coupling and Dependency Metrics Calculator.

Computes degree centrality, total structural coupling, cycle membership,
and condensation depth per table node.
"""

from __future__ import annotations

from typing import Any

from dera.diagnostics.metrics.models import CouplingMaintainabilityMetrics
from dera.diagnostics.rules.shared.graph_helpers import get_table_node_map


def compute_all_coupling_metrics(
    graph: Any,
    deps: Any,
) -> tuple[CouplingMaintainabilityMetrics, ...]:
    """Computes relational coupling metrics for all table nodes in the multigraph."""
    if graph is None or deps is None:
        return ()

    node_map = get_table_node_map(graph)
    node_metrics_dict = getattr(deps, "node_metrics", {})

    results: list[CouplingMaintainabilityMetrics] = []
    for node_id_str, metrics in node_metrics_dict.items():
        node = node_map.get(node_id_str)
        if node is None:
            continue

        obj_name = f"{node.namespace_name}.{node.native_name}"
        in_deg = getattr(metrics, "in_degree", 0)
        out_deg = getattr(metrics, "out_degree", 0)
        tot_deg = in_deg + out_deg

        results.append(
            CouplingMaintainabilityMetrics(
                node_id=node_id_str,
                table_name=obj_name,
                in_degree=in_deg,
                out_degree=out_deg,
                total_degree=tot_deg,
                is_in_cycle=bool(getattr(metrics, "is_in_cycle", False)),
                condensation_depth=getattr(metrics, "depth_level", 0),
                transitive_dependents_count=getattr(metrics, "transitive_dependent_count", 0),
            )
        )

    return tuple(sorted(results, key=lambda m: (m.table_name, m.node_id)))
