"""DERA Reverse Engineering — Phase 6.3 Foreign Key Relationship Graph.

Provides a deterministic, strongly typed, immutable foreign key relationship directed multigraph
engine built on verified database constraints reconstructed in Phase 6.2 and Phase 6.1.
"""

from __future__ import annotations

from dera.reverse_engineering.graph.adjacency import AdjacencyIndex
from dera.reverse_engineering.graph.builder import ForeignKeyGraphBuilder
from dera.reverse_engineering.graph.capabilities import (
    GraphCapabilityProfile,
    assess_graph_capabilities,
)
from dera.reverse_engineering.graph.edges import ColumnPairMapping, ForeignKeyEdge
from dera.reverse_engineering.graph.errors import (
    CrossWorkspaceGraphError,
    ForeignKeyGraphError,
    GraphBuilderError,
    GraphResourceLimitError,
    GraphSerializationError,
    GraphTraversalError,
    GraphValidationError,
    InvalidEdgeError,
    InvalidNodeError,
    TraversalLimitExceededError,
    UnresolvedReferenceError,
)
from dera.reverse_engineering.graph.limits import GraphResourceLimits
from dera.reverse_engineering.graph.models import (
    ForeignKeyGraph,
    UnresolvedReason,
    UnresolvedReference,
)
from dera.reverse_engineering.graph.nodes import TableNode
from dera.reverse_engineering.graph.ordering import (
    sort_column_pairs,
    sort_foreign_key_edges,
    sort_table_nodes,
    sort_unresolved_references,
    sort_validation_findings,
)
from dera.reverse_engineering.graph.relationships import (
    all_neighbors,
    incoming_neighbors,
    incoming_relationships,
    outgoing_neighbors,
    outgoing_relationships,
    relationships_between,
)
from dera.reverse_engineering.graph.serialization import (
    FOREIGN_KEY_GRAPH_CONTRACT_VERSION,
    compute_graph_hash,
    deserialize_graph_from_dict,
    deserialize_graph_from_json,
    serialize_graph_to_dict,
    serialize_graph_to_json,
)
from dera.reverse_engineering.graph.traversal import (
    TraversalDirection,
    TraversalResult,
    TraversalStep,
    TraversalStrategy,
    find_weakly_connected_components,
    traverse,
)
from dera.reverse_engineering.graph.validation import (
    GraphValidationFinding,
    ValidationMode,
    ValidationSeverity,
    validate_foreign_key_graph,
)

__all__ = [
    # Contracts & Models
    "ColumnPairMapping",
    "ForeignKeyEdge",
    "ForeignKeyGraph",
    "TableNode",
    "UnresolvedReason",
    "UnresolvedReference",
    # Adjacency & Relationships
    "AdjacencyIndex",
    "all_neighbors",
    "incoming_neighbors",
    "incoming_relationships",
    "outgoing_neighbors",
    "outgoing_relationships",
    "relationships_between",
    # Builder
    "ForeignKeyGraphBuilder",
    # Traversal & Components
    "TraversalDirection",
    "TraversalResult",
    "TraversalStep",
    "TraversalStrategy",
    "find_weakly_connected_components",
    "traverse",
    # Validation
    "GraphValidationFinding",
    "ValidationMode",
    "ValidationSeverity",
    "validate_foreign_key_graph",
    # Capabilities & Limits
    "GraphCapabilityProfile",
    "GraphResourceLimits",
    "assess_graph_capabilities",
    # Ordering
    "sort_column_pairs",
    "sort_foreign_key_edges",
    "sort_table_nodes",
    "sort_unresolved_references",
    "sort_validation_findings",
    # Serialization
    "FOREIGN_KEY_GRAPH_CONTRACT_VERSION",
    "compute_graph_hash",
    "deserialize_graph_from_dict",
    "deserialize_graph_from_json",
    "serialize_graph_to_dict",
    "serialize_graph_to_json",
    # Errors
    "CrossWorkspaceGraphError",
    "ForeignKeyGraphError",
    "GraphBuilderError",
    "GraphResourceLimitError",
    "GraphSerializationError",
    "GraphTraversalError",
    "GraphValidationError",
    "InvalidEdgeError",
    "InvalidNodeError",
    "TraversalLimitExceededError",
    "UnresolvedReferenceError",
]
