"""DERA Reverse Engineering — Phase 6.4 Dependency Analysis Models & Contracts.

Defines strongly typed, immutable Pydantic v2 data models for dependency analysis,
topological ordering, cycle classification, and SCC partitioning.
"""

from __future__ import annotations

import hashlib
import json
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from dera.metadata.identity import ObjectId

DEPENDENCY_ANALYSIS_CONTRACT_VERSION = "phase-6.4-dependency-analysis-v1"


class DependencyKind(StrEnum):
    """Categorization of dependency relationship types."""

    TABLE_FOREIGN_KEY = "table_foreign_key"
    VIEW_TABLE = "view_table"
    VIEW_VIEW = "view_view"
    TRIGGER_TABLE = "trigger_table"


class CycleKind(StrEnum):
    """Classification of directed dependency cycles."""

    SELF_REFERENCING = "self_referencing"
    MUTUAL = "mutual"
    INDIRECT = "indirect"
    COMPLEX = "complex"


class BreakabilityStrategy(StrEnum):
    """Strategy for safely resolving cyclic dependencies during data insertion."""

    NULLABLE_FOREIGN_KEY = "nullable_foreign_key"
    DEFERRABLE_CONSTRAINT = "deferrable_constraint"
    POST_DATA_LOAD_CONSTRAINT = "post_data_load_constraint"
    UNBREAKABLE = "unbreakable"


class DependencyEdge(BaseModel):
    """Directed dependency edge where dependent_id relies on referenced_id."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    edge_id: str = Field(description="Unique identifier of this dependency edge (typically FK ObjectId).")
    dependent_id: ObjectId = Field(description="The dependent node (child table holding FK constraint).")
    referenced_id: ObjectId = Field(description="The referenced prerequisite node (parent table holding PK/UQ).")
    kind: DependencyKind = Field(default=DependencyKind.TABLE_FOREIGN_KEY, description="Kind of dependency.")
    is_nullable: bool = Field(default=False, description="True if at least one FK column is nullable.")
    is_deferrable: bool = Field(default=False, description="True if constraint enforcement can be deferred.")
    column_pairs: tuple[tuple[str, str], ...] = Field(
        default=(),
        description="Ordered sequence of (source_column, referenced_column) pairings.",
    )


class CycleInstance(BaseModel):
    """Identified elementary directed cycle in canonical rotation order."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    cycle_id: str = Field(description="Deterministic unique identifier for this cycle instance.")
    kind: CycleKind = Field(description="Classification of the cycle structure.")
    node_ids: tuple[ObjectId, ...] = Field(
        description="Ordered sequence of nodes in the cycle, starting at the lowest ObjectId."
    )
    edge_ids: tuple[str, ...] = Field(
        default=(),
        description="Ordered sequence of edge identifiers traversing the cycle path.",
    )
    break_edges: tuple[str, ...] = Field(
        default=(),
        description="Candidate edge identifiers that can be broken during migration.",
    )
    is_breakable: bool = Field(
        default=False,
        description="True if the cycle contains at least one breakable edge.",
    )
    recommended_break_strategy: BreakabilityStrategy = Field(
        default=BreakabilityStrategy.UNBREAKABLE,
        description="Recommended strategy for breaking the cycle during data loading.",
    )


class StronglyConnectedComponent(BaseModel):
    """Strongly connected component containing mutually reachable nodes."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    scc_id: str = Field(description="Deterministic unique identifier for this SCC.")
    node_ids: tuple[ObjectId, ...] = Field(description="Member nodes in canonical sort order.")
    is_cyclic: bool = Field(description="True if component contains a directed cycle or self-loop.")
    cycles: tuple[CycleInstance, ...] = Field(
        default=(),
        description="Elementary cycles discovered within this component.",
    )


class DependencyNodeMetrics(BaseModel):
    """Topological metrics and centrality attributes for an individual graph node."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    node_id: ObjectId = Field(description="Canonical identifier of the target node.")
    in_degree: int = Field(ge=0, description="Number of direct prerequisite dependencies.")
    out_degree: int = Field(ge=0, description="Number of direct downstream dependents.")
    transitive_dependency_count: int = Field(ge=0, description="Total upstream ancestor dependencies.")
    transitive_dependent_count: int = Field(ge=0, description="Total downstream descendant dependents.")
    depth_level: int = Field(ge=0, description="Longest dependency path length from any root node.")
    is_root: bool = Field(description="True if node has no upstream dependencies (in_degree == 0).")
    is_leaf: bool = Field(description="True if no nodes depend on this node (out_degree == 0).")
    is_in_cycle: bool = Field(description="True if node is part of a cyclic strongly connected component.")


class TopologicalLevel(BaseModel):
    """Execution layer of tables that can be processed concurrently."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    level: int = Field(ge=0, description="Zero-based dependency layer index.")
    node_ids: tuple[ObjectId, ...] = Field(
        description="Nodes in this layer, sorted deterministically by canonical ObjectId."
    )


class CondensationNode(BaseModel):
    """Supernode in the condensation DAG representing an SCC."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    condensation_id: str = Field(description="Unique identifier for the condensation node.")
    is_cyclic: bool = Field(description="True if this supernode contracts a cyclic SCC.")
    member_node_ids: tuple[ObjectId, ...] = Field(
        description="Member node ObjectIds contracted into this condensation node."
    )
    dependencies: tuple[str, ...] = Field(
        default=(),
        description="Identifiers of prerequisite condensation nodes that must precede this node.",
    )


class DependencyOrdering(BaseModel):
    """Deterministic sequence for schema creation, drop, and parallel batching."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    is_pure_dag: bool = Field(description="True if the graph is strictly acyclic.")
    creation_order: tuple[ObjectId, ...] = Field(
        default=(),
        description="Deterministic installation sequence: parents precede children.",
    )
    drop_order: tuple[ObjectId, ...] = Field(
        default=(),
        description="Deterministic destruction sequence: children precede parents (exact reverse).",
    )
    levels: tuple[TopologicalLevel, ...] = Field(
        default=(),
        description="Stratified execution layers for concurrent migration steps.",
    )
    condensed_order: tuple[str, ...] = Field(
        default=(),
        description="Topological sequence of condensation DAG components.",
    )
    unresolved_cycles_exist: bool = Field(
        default=False,
        description="True if unresolved/unbreakable cycles prevent pure topological sequencing.",
    )


class CycleReport(BaseModel):
    """Comprehensive diagnostic breakdown of cycles and cyclic components."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    has_cycles: bool = Field(description="True if one or more cycles exist in the graph.")
    cycle_count: int = Field(ge=0, description="Total number of enumerated elementary cycles.")
    scc_count: int = Field(ge=0, description="Total number of strongly connected components.")
    cyclic_scc_count: int = Field(ge=0, description="Number of cyclic strongly connected components.")
    self_referencing_count: int = Field(ge=0, description="Number of self-referencing table cycles.")
    mutual_count: int = Field(ge=0, description="Number of mutual 2-table cycles.")
    indirect_count: int = Field(ge=0, description="Number of multi-table simple cycles (>=3 tables).")
    complex_count: int = Field(ge=0, description="Number of complex intertwined multi-cycle SCCs.")
    breakable_cycle_count: int = Field(ge=0, description="Number of cycles breakable via nullable/deferrable FKs.")
    unbreakable_cycle_count: int = Field(ge=0, description="Number of unbreakable cycles.")
    cycles: tuple[CycleInstance, ...] = Field(
        default=(),
        description="Discovered elementary cycles in canonical sort order.",
    )
    sccs: tuple[StronglyConnectedComponent, ...] = Field(
        default=(),
        description="All strongly connected components in canonical sort order.",
    )


class DependencyValidationFinding(BaseModel):
    """Diagnostic validation finding from dependency analysis."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    rule_id: str = Field(description="Unique code identifying the validation rule.")
    severity: str = Field(description="Finding severity: ERROR, WARNING, or INFO.")
    message: str = Field(description="Human-readable description of the finding.")
    context: dict[str, str] = Field(default_factory=dict, description="Diagnostic contextual metadata.")


class DependencyAnalysisResult(BaseModel):
    """Root container encapsulating the complete dependency analysis result."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    contract_version: str = Field(
        default=DEPENDENCY_ANALYSIS_CONTRACT_VERSION,
        description="Contract specification version identifier.",
    )
    workspace_id: str | None = Field(default=None, description="Workspace or tenant isolation scope.")
    database_id: ObjectId = Field(description="Parent database canonical ObjectId.")
    source_graph_hash: str = Field(description="SHA-256 fingerprint of the source ForeignKeyGraph.")
    node_count: int = Field(ge=0, description="Total count of analyzed nodes.")
    edge_count: int = Field(ge=0, description="Total count of dependency edges.")
    is_dag: bool = Field(description="True if the analyzed graph is strictly a directed acyclic graph.")
    ordering: DependencyOrdering = Field(description="Topological sequences and batching layers.")
    cycle_report: CycleReport = Field(description="Diagnostic report on circular dependencies.")
    node_metrics: dict[str, DependencyNodeMetrics] = Field(
        default_factory=dict,
        description="Per-node metrics keyed by ObjectId hex value.",
    )
    root_node_ids: tuple[ObjectId, ...] = Field(
        default=(),
        description="Independent nodes with zero dependencies, sorted deterministically.",
    )
    leaf_node_ids: tuple[ObjectId, ...] = Field(
        default=(),
        description="Terminal nodes that no other nodes depend on, sorted deterministically.",
    )
    isolated_node_ids: tuple[ObjectId, ...] = Field(
        default=(),
        description="Nodes with zero dependencies and zero dependents, sorted deterministically.",
    )
    condensation_nodes: tuple[CondensationNode, ...] = Field(
        default=(),
        description="Condensation DAG supernodes in canonical sort order.",
    )
    validation_findings: tuple[DependencyValidationFinding, ...] = Field(
        default=(),
        description="Validation findings and diagnostics generated during analysis.",
    )

    def compute_hash(self) -> str:
        """Compute deterministic SHA-256 fingerprint over canonical representation."""
        data = self.model_dump(mode="json")
        canonical_json = json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()

    def get_node_metrics(self, node_id: ObjectId) -> DependencyNodeMetrics | None:
        """Retrieve precomputed metrics for a specific node."""
        return self.node_metrics.get(str(node_id))

    def get_creation_order(self) -> tuple[ObjectId, ...]:
        """Convenience accessor for deterministic table creation order."""
        return self.ordering.creation_order

    def get_drop_order(self) -> tuple[ObjectId, ...]:
        """Convenience accessor for deterministic table drop order."""
        return self.ordering.drop_order
