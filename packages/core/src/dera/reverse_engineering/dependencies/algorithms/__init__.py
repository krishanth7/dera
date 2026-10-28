"""DERA Reverse Engineering — Phase 6.4 Graph & Dependency Algorithms.

Exports deterministic graph algorithms: Tarjan's SCC, Johnson's bounded elementary cycle
finder, Kahn's topological sort, condensation DAG builder, and dependency metrics.
"""

from __future__ import annotations

from dera.reverse_engineering.dependencies.algorithms.cycle_analysis import (
    compile_cycle_report,
)
from dera.reverse_engineering.dependencies.algorithms.johnson import (
    find_elementary_cycles,
)
from dera.reverse_engineering.dependencies.algorithms.metrics import (
    compute_node_metrics,
)
from dera.reverse_engineering.dependencies.algorithms.tarjan import (
    compute_strongly_connected_components,
)
from dera.reverse_engineering.dependencies.algorithms.topological_sort import (
    compute_topological_ordering,
)

__all__ = [
    "compile_cycle_report",
    "compute_node_metrics",
    "compute_strongly_connected_components",
    "compute_topological_ordering",
    "find_elementary_cycles",
]
