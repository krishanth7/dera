"""DERA Reverse Engineering — Phase 6.4 Dependency Analysis & Cycle Detection.

Provides deterministic, strongly typed, immutable dependency analysis, topological sorting,
strongly connected component decomposition, elementary cycle detection, and cycle
breakability evaluation for database schemas.
"""

from __future__ import annotations

from dera.reverse_engineering.dependencies.algorithms import (
    compile_cycle_report,
    compute_node_metrics,
    compute_strongly_connected_components,
    compute_topological_ordering,
    find_elementary_cycles,
)
from dera.reverse_engineering.dependencies.analyzer import DependencyAnalyzer
from dera.reverse_engineering.dependencies.errors import (
    CyclicDependencyError,
    DependencyAnalysisError,
    DependencyResourceLimitError,
    DependencySerializationError,
    DependencyValidationError,
    UnresolvableOrderError,
)
from dera.reverse_engineering.dependencies.limits import DependencyResourceLimits
from dera.reverse_engineering.dependencies.models import (
    DEPENDENCY_ANALYSIS_CONTRACT_VERSION,
    BreakabilityStrategy,
    CondensationNode,
    CycleInstance,
    CycleKind,
    CycleReport,
    DependencyAnalysisResult,
    DependencyEdge,
    DependencyKind,
    DependencyNodeMetrics,
    DependencyOrdering,
    DependencyValidationFinding,
    StronglyConnectedComponent,
    TopologicalLevel,
)
from dera.reverse_engineering.dependencies.ordering import (
    canonicalize_cycle_nodes,
    sort_condensation_nodes,
    sort_cycle_instances,
    sort_dependency_edges,
    sort_dependency_validation_findings,
    sort_sccs,
    sort_topological_levels,
)
from dera.reverse_engineering.dependencies.serialization import (
    compute_dependency_hash,
    deserialize_dependency_analysis_from_dict,
    deserialize_dependency_analysis_from_json,
    serialize_dependency_analysis_to_dict,
    serialize_dependency_analysis_to_json,
)
from dera.reverse_engineering.dependencies.validation import (
    ValidationMode,
    validate_dependency_analysis,
)

__all__ = [
    # Contracts & Models
    "DEPENDENCY_ANALYSIS_CONTRACT_VERSION",
    "BreakabilityStrategy",
    "CondensationNode",
    "CycleInstance",
    "CycleKind",
    "CycleReport",
    "DependencyAnalysisResult",
    "DependencyEdge",
    "DependencyKind",
    "DependencyNodeMetrics",
    "DependencyOrdering",
    "DependencyValidationFinding",
    "StronglyConnectedComponent",
    "TopologicalLevel",
    # Orchestrator
    "DependencyAnalyzer",
    # Configuration
    "DependencyResourceLimits",
    "ValidationMode",
    # Serialization
    "compute_dependency_hash",
    "deserialize_dependency_analysis_from_dict",
    "deserialize_dependency_analysis_from_json",
    "serialize_dependency_analysis_to_dict",
    "serialize_dependency_analysis_to_json",
    # Validation
    "validate_dependency_analysis",
    # Ordering
    "canonicalize_cycle_nodes",
    "sort_condensation_nodes",
    "sort_cycle_instances",
    "sort_dependency_edges",
    "sort_dependency_validation_findings",
    "sort_sccs",
    "sort_topological_levels",
    # Algorithms
    "compile_cycle_report",
    "compute_node_metrics",
    "compute_strongly_connected_components",
    "compute_topological_ordering",
    "find_elementary_cycles",
    # Errors
    "CyclicDependencyError",
    "DependencyAnalysisError",
    "DependencyResourceLimitError",
    "DependencySerializationError",
    "DependencyValidationError",
    "UnresolvableOrderError",
]
