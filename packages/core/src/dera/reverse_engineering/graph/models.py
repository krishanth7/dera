"""DERA Reverse Engineering — Phase 6.3 Graph Models.

Defines the canonical, strongly typed ForeignKeyGraph contract representing verified
database relationships through immutable table nodes and directed multigraph foreign key edges.
"""

from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, ConfigDict, Field, PrivateAttr

from dera.metadata.enums import MetadataCompleteness
from dera.metadata.identity import ObjectId
from dera.metadata.provenance import MetadataProvenance
from dera.reverse_engineering.graph.adjacency import AdjacencyIndex
from dera.reverse_engineering.graph.capabilities import GraphCapabilityProfile
from dera.reverse_engineering.graph.edges import ForeignKeyEdge
from dera.reverse_engineering.graph.limits import GraphResourceLimits
from dera.reverse_engineering.graph.nodes import TableNode
from dera.reverse_engineering.graph.validation import GraphValidationFinding

if TYPE_CHECKING:
    from dera.reverse_engineering.graph.traversal import (
        TraversalDirection,
        TraversalResult,
        TraversalStrategy,
    )


class UnresolvedReason(StrEnum):
    """Categorized explanation for unresolvable foreign key relationships."""

    REFERENCED_TABLE_NOT_FOUND = "referenced_table_not_found"
    REFERENCED_COLUMN_NOT_FOUND = "referenced_column_not_found"
    METADATA_RESTRICTED = "metadata_restricted"
    METADATA_INCOMPLETE = "metadata_incomplete"
    UNSUPPORTED_CAPABILITY = "unsupported_capability"
    CROSS_WORKSPACE_REFERENCE = "cross_workspace_reference"
    INVALID_METADATA = "invalid_metadata"


class UnresolvedReference(BaseModel):
    """Auditable record of a declared foreign key constraint whose referenced entity could not be resolved.

    Preserves catalog transparency without inventing synthetic target nodes or discarding real constraints.
    """

    model_config = ConfigDict(frozen=True)

    foreign_key_id: ObjectId = Field(
        ...,
        description="Canonical ObjectId of the declared foreign key constraint.",
    )
    native_name: str = Field(
        ...,
        description="Declared native foreign key constraint identifier in catalog.",
    )
    source_table_id: ObjectId = Field(
        ...,
        description="ObjectId of child table declaring the unresolved constraint.",
    )
    source_table_name: str = Field(
        ...,
        description="Native name of the child table declaring the constraint.",
    )
    source_namespace: str = Field(
        default="public",
        description="Native schema/namespace of the child table.",
    )
    referenced_table_name: str = Field(
        ...,
        description="Target table name as declared in the foreign key definition.",
    )
    referenced_namespace: str = Field(
        default="public",
        description="Target schema/namespace as declared in the foreign key definition.",
    )
    declared_source_columns: tuple[str, ...] = Field(
        default_factory=tuple,
        description="Declared child column names.",
    )
    declared_referenced_columns: tuple[str, ...] = Field(
        default_factory=tuple,
        description="Declared referenced parent column names.",
    )
    reason: UnresolvedReason = Field(
        ...,
        description="Classification code explaining why reference could not be resolved.",
    )
    details: str = Field(
        ...,
        description="Human-readable technical explanation and diagnostic context.",
    )
    provenance: MetadataProvenance = Field(
        ...,
        description="Extraction provenance identifying the source origin.",
    )

    def __repr__(self) -> str:
        return (
            f"UnresolvedReference({self.source_namespace}.{self.source_table_name} -> "
            f"{self.referenced_namespace}.{self.referenced_table_name}, reason={self.reason.value})"
        )


class ForeignKeyGraph(BaseModel):
    """Canonical, immutable foreign key relationship directed multigraph.

    Guarantees:
    - Directed multigraph: supports multiple foreign keys between same tables and self-loops.
    - Strictly deterministic node and edge sequencing.
    - Comprehensive metadata provenance and auditability.
    - Instant O(1) indexed lookups for outgoing, incoming, pairwise, and neighbor queries.
    - Immutability: frozen model preventing mutation of shared graph state.
    """

    model_config = ConfigDict(frozen=True)

    contract_version: str = Field(
        default="1.0.0",
        description="Semantic version of this foreign key graph contract.",
    )
    database_id: ObjectId = Field(
        ...,
        description="Deterministic canonical ObjectId uniquely identifying the database.",
    )
    database_name: str = Field(
        ...,
        description="Logical name of the inspected database.",
    )
    engine: str = Field(
        ...,
        description="Dialect engine type (e.g. postgresql, sqlite, mysql, mariadb).",
    )
    workspace_id: str | None = Field(
        default=None,
        description="Workspace scope identifier enforcing multitenant isolation.",
    )
    nodes: tuple[TableNode, ...] = Field(
        default_factory=tuple,
        description="Stably sorted collection of real verified table nodes.",
    )
    edges: tuple[ForeignKeyEdge, ...] = Field(
        default_factory=tuple,
        description="Stably sorted collection of verified foreign key relationship edges.",
    )
    unresolved_references: tuple[UnresolvedReference, ...] = Field(
        default_factory=tuple,
        description="Stably sorted collection of unresolvable foreign key constraints.",
    )
    validation_findings: tuple[GraphValidationFinding, ...] = Field(
        default_factory=tuple,
        description="Diagnostic findings produced during graph integrity checks.",
    )
    capability_profile: GraphCapabilityProfile = Field(
        ...,
        description="Engine capability assessment and completeness status.",
    )
    completeness: MetadataCompleteness = Field(
        default=MetadataCompleteness.COMPLETE,
        description="Overall metadata completeness assessment.",
    )
    provenance: MetadataProvenance = Field(
        ...,
        description="Extraction provenance and audit record identifying source origin.",
    )

    _adjacency: AdjacencyIndex | None = PrivateAttr(default=None)
    _node_map: dict[ObjectId, TableNode] | None = PrivateAttr(default=None)
    _edge_map: dict[ObjectId, ForeignKeyEdge] | None = PrivateAttr(default=None)

    def get_adjacency(self) -> AdjacencyIndex:
        """Returns the internal AdjacencyIndex, computing and caching it if not already present."""
        if self._adjacency is None:
            object.__setattr__(self, "_adjacency", AdjacencyIndex.build(self.nodes, self.edges))
        return self._adjacency

    def _ensure_maps(self) -> None:
        if self._node_map is None:
            object.__setattr__(self, "_node_map", {node.object_id: node for node in self.nodes})
        if self._edge_map is None:
            object.__setattr__(self, "_edge_map", {edge.object_id: edge for edge in self.edges})

    @property
    def node_count(self) -> int:
        """Total number of table nodes in graph."""
        return len(self.nodes)

    @property
    def edge_count(self) -> int:
        """Total number of foreign key edges in graph."""
        return len(self.edges)

    @property
    def is_empty(self) -> bool:
        """True if graph contains zero table nodes."""
        return len(self.nodes) == 0

    def get_node(self, table_id: ObjectId) -> TableNode | None:
        """Lookup table node by its canonical ObjectId in O(1) time."""
        self._ensure_maps()
        assert self._node_map is not None
        return self._node_map.get(table_id)

    def get_node_by_name(self, table_name: str, namespace: str = "public") -> TableNode | None:
        """Lookup table node by its native table and schema names."""
        clean_tbl = table_name.lower()
        clean_ns = namespace.lower()
        for node in self.nodes:
            if node.native_name.lower() == clean_tbl and node.namespace_name.lower() == clean_ns:
                return node
        return None

    def has_node(self, table_id: ObjectId) -> bool:
        """Check whether table node exists in the graph."""
        return self.get_node(table_id) is not None

    def get_edge(self, constraint_id: ObjectId) -> ForeignKeyEdge | None:
        """Lookup foreign key edge by its canonical constraint ObjectId in O(1) time."""
        self._ensure_maps()
        assert self._edge_map is not None
        return self._edge_map.get(constraint_id)

    def outgoing(self, table_id: ObjectId) -> tuple[ForeignKeyEdge, ...]:
        """Return all foreign key edges declared by table_id (child -> parent) in O(1) time."""
        return self.get_adjacency().get_outgoing(table_id)

    def incoming(self, table_id: ObjectId) -> tuple[ForeignKeyEdge, ...]:
        """Return all foreign key edges referencing table_id (parent <- child) in O(1) time."""
        return self.get_adjacency().get_incoming(table_id)

    def relationships_between(
        self,
        source_table_id: ObjectId,
        referenced_table_id: ObjectId,
    ) -> tuple[ForeignKeyEdge, ...]:
        """Return all foreign key edges connecting source_table_id to referenced_table_id in O(1) time."""
        return self.get_adjacency().get_between(source_table_id, referenced_table_id)

    def outgoing_neighbors(self, table_id: ObjectId) -> tuple[ObjectId, ...]:
        """Return unique table ObjectIds referenced by foreign keys declared by table_id."""
        return self.get_adjacency().outgoing_neighbors(table_id)

    def incoming_neighbors(self, table_id: ObjectId) -> tuple[ObjectId, ...]:
        """Return unique table ObjectIds that reference table_id via foreign keys."""
        return self.get_adjacency().incoming_neighbors(table_id)

    def neighbors(self, table_id: ObjectId) -> tuple[ObjectId, ...]:
        """Return unique table ObjectIds connected either incoming or outgoing with table_id."""
        return self.get_adjacency().all_neighbors(table_id)

    def all_neighbors(self, table_id: ObjectId) -> tuple[ObjectId, ...]:
        """Alias for neighbors(table_id)."""
        return self.neighbors(table_id)

    def traverse(
        self,
        start_table_id: ObjectId,
        direction: TraversalDirection | str = "outgoing",
        strategy: TraversalStrategy | str = "bfs",
        limits: GraphResourceLimits | None = None,
        raise_on_limit: bool = False,
    ) -> TraversalResult:
        """Executes a bounded, deterministic BFS or DFS traversal from start_table_id."""
        from dera.reverse_engineering.graph.traversal import (
            TraversalDirection,
            TraversalStrategy,
            traverse,
        )

        dir_enum = TraversalDirection(direction) if isinstance(direction, str) else direction
        strat_enum = TraversalStrategy(strategy) if isinstance(strategy, str) else strategy
        return traverse(
            adjacency=self.get_adjacency(),
            start_table_id=start_table_id,
            direction=dir_enum,
            strategy=strat_enum,
            limits=limits,
            raise_on_limit=raise_on_limit,
        )

    def weakly_connected_components(self) -> tuple[tuple[ObjectId, ...], ...]:
        """Computes weakly connected components treating foreign key edges as undirected."""
        from dera.reverse_engineering.graph.traversal import find_weakly_connected_components

        return find_weakly_connected_components(self.nodes, self.edges)

    def compute_hash(self) -> str:
        """Computes a deterministic SHA-256 fingerprint for this graph."""
        from dera.reverse_engineering.graph.serialization import compute_graph_hash

        return compute_graph_hash(self)

    def to_dict(self) -> dict[str, Any]:
        """Serializes this graph to a JSON-compatible dictionary."""
        from dera.reverse_engineering.graph.serialization import serialize_graph_to_dict

        return serialize_graph_to_dict(self)

    def to_json(self, indent: int | None = None) -> str:
        """Serializes this graph to a deterministic JSON string."""
        from dera.reverse_engineering.graph.serialization import serialize_graph_to_json

        return serialize_graph_to_json(self, indent=indent)
