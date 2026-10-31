"""DERA API — Phase 6.6 Reverse Engineering Request & Response Schemas.

Defines strongly typed Pydantic v2 schemas for schema representation, table details,
relationship graphs, dependency analysis, snapshots, and deterministic exports.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from dera.reverse_engineering.exports.models import ExportFormat, ExportScope
from pydantic import BaseModel, ConfigDict, Field


class SchemaSummaryResponse(BaseModel):
    """Summary descriptor of an analyzed canonical schema."""

    model_config = ConfigDict(frozen=True)

    schema_id: str = Field(..., description="Canonical database ID / schema ID.")
    database_id: str = Field(..., description="Source canonical database ObjectId.")
    database_name: str = Field(..., description="Native database catalog name.")
    engine: str = Field(..., description="Normalized engine dialect identifier.")
    namespace_count: int = Field(..., description="Total namespaces in schema.")
    table_count: int = Field(..., description="Total tables in schema.")
    view_count: int = Field(..., description="Total views in schema.")
    foreign_key_count: int = Field(..., description="Total verified foreign keys.")
    completeness: str = Field(..., description="Metadata completeness level.")
    source_engine: str = Field(..., description="Underlying database engine.")
    source_version: str = Field(..., description="Underlying database version.")
    connector_version: str | None = Field(default=None, description="Connector version used.")
    collection_timestamp: datetime = Field(..., description="When metadata was extracted.")


class NamespaceSummary(BaseModel):
    """Namespace summary descriptor."""

    model_config = ConfigDict(frozen=True)

    namespace_id: str
    name: str
    table_count: int


class NamespaceListResponse(BaseModel):
    """Paginated list of namespaces."""

    model_config = ConfigDict(frozen=True)

    namespaces: list[NamespaceSummary]
    total_count: int
    next_cursor: str | None = None


class TableSummary(BaseModel):
    """Table summary descriptor."""

    model_config = ConfigDict(frozen=True)

    table_id: str
    namespace: str
    name: str
    table_type: str
    column_count: int
    has_primary_key: bool
    foreign_key_count: int


class TableListResponse(BaseModel):
    """Paginated list of tables in a schema."""

    model_config = ConfigDict(frozen=True)

    tables: list[TableSummary]
    total_count: int
    next_cursor: str | None = None


class ColumnDetailResponse(BaseModel):
    """Detailed metadata for a single column."""

    model_config = ConfigDict(frozen=True)

    column_id: str
    table_id: str
    name: str
    ordinal_position: int
    native_type: str
    canonical_type: str
    is_nullable: bool
    is_primary_key: bool
    default_expression: str | None = None


class PrimaryKeyResponse(BaseModel):
    """Primary key constraint definition."""

    model_config = ConfigDict(frozen=True)

    constraint_id: str
    name: str
    columns: list[str]


class ForeignKeySummaryResponse(BaseModel):
    """Foreign key relationship metadata."""

    model_config = ConfigDict(frozen=True)

    constraint_id: str
    name: str
    source_columns: list[str]
    referenced_table_id: str | None
    referenced_table_name: str
    referenced_columns: list[str]
    on_delete: str | None = None
    on_update: str | None = None


class ConstraintSummaryResponse(BaseModel):
    """Generic constraint descriptor."""

    model_config = ConfigDict(frozen=True)

    constraint_id: str
    name: str
    constraint_type: str
    columns: list[str]
    raw_expression: str | None = None


class IndexSummaryResponse(BaseModel):
    """Index metadata descriptor."""

    model_config = ConfigDict(frozen=True)

    index_id: str
    name: str
    is_unique: bool
    is_primary: bool
    columns: list[str]


class TableDetailResponse(BaseModel):
    """Comprehensive detail representation of a database table."""

    model_config = ConfigDict(frozen=True)

    table_id: str
    namespace: str
    name: str
    table_type: str
    columns: list[ColumnDetailResponse]
    primary_key: PrimaryKeyResponse | None = None
    foreign_keys: list[ForeignKeySummaryResponse] = Field(default_factory=list)
    unique_constraints: list[ConstraintSummaryResponse] = Field(default_factory=list)
    check_constraints: list[ConstraintSummaryResponse] = Field(default_factory=list)
    indexes: list[IndexSummaryResponse] = Field(default_factory=list)


class ConstraintListResponse(BaseModel):
    """List of constraints in a schema."""

    model_config = ConfigDict(frozen=True)

    constraints: list[ConstraintSummaryResponse]
    total_count: int


class TableNodeResponse(BaseModel):
    """Relationship graph node."""

    model_config = ConfigDict(frozen=True)

    table_id: str
    namespace: str
    name: str


class RelationshipEdgeResponse(BaseModel):
    """Relationship graph edge."""

    model_config = ConfigDict(frozen=True)

    edge_id: str
    source_table_id: str
    source_table_name: str
    target_table_id: str
    target_table_name: str
    constraint_name: str
    source_columns: list[str]
    target_columns: list[str]
    on_delete: str | None = None
    on_update: str | None = None


class RelationshipGraphResponse(BaseModel):
    """Complete foreign key relationship graph representation."""

    model_config = ConfigDict(frozen=True)

    database_name: str
    engine: str
    node_count: int
    edge_count: int
    nodes: list[TableNodeResponse]
    edges: list[RelationshipEdgeResponse]


class TableRelationshipsResponse(BaseModel):
    """Direct relationships for a specific table."""

    model_config = ConfigDict(frozen=True)

    table_id: str
    incoming: list[RelationshipEdgeResponse]
    outgoing: list[RelationshipEdgeResponse]


class TopologicalLevelResponse(BaseModel):
    """Topological parallel migration level."""

    model_config = ConfigDict(frozen=True)

    level_index: int
    table_ids: list[str]


class DependencyAnalysisResponse(BaseModel):
    """Dependency analysis summary and execution orderings."""

    model_config = ConfigDict(frozen=True)

    database_name: str
    total_tables: int
    total_edges: int
    has_cycles: bool
    cycle_count: int
    scc_count: int
    cyclic_scc_count: int
    creation_order: list[str]
    drop_order: list[str]
    levels: list[TopologicalLevelResponse]


class TableDependencyResponse(BaseModel):
    """Dependency metrics for a specific table."""

    model_config = ConfigDict(frozen=True)

    table_id: str
    direct_dependencies: list[str]
    direct_dependents: list[str]
    in_cycle: bool
    scc_id: str | None = None


class CycleInstanceResponse(BaseModel):
    """Elementary cycle detail."""

    model_config = ConfigDict(frozen=True)

    cycle_id: str
    cycle_kind: str
    table_ids: list[str]
    length: int
    breakability_strategy: str | None = None


class SCCResponse(BaseModel):
    """Strongly connected component detail."""

    model_config = ConfigDict(frozen=True)

    scc_id: str
    is_cyclic: bool
    table_ids: list[str]
    size: int


class CycleReportResponse(BaseModel):
    """Comprehensive cycle detection report."""

    model_config = ConfigDict(frozen=True)

    has_cycles: bool
    cycle_count: int
    scc_count: int
    cyclic_scc_count: int
    cycles: list[CycleInstanceResponse]
    components: list[SCCResponse]


class SnapshotCreateRequest(BaseModel):
    """Request payload to create a new immutable schema snapshot."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_id: str = Field(..., description="Canonical schema ID to snapshot.")
    tags: list[str] = Field(default_factory=list, description="Optional metadata tags.")


class SnapshotSummaryResponse(BaseModel):
    """Lightweight metadata descriptor for a schema snapshot."""

    model_config = ConfigDict(frozen=True)

    snapshot_id: str
    fingerprint: str
    database_id: str
    database_name: str
    engine: str
    capture_timestamp: datetime
    completeness: str
    table_count: int
    tags: list[str]


class SnapshotListResponse(BaseModel):
    """Paginated list of schema snapshots."""

    model_config = ConfigDict(frozen=True)

    snapshots: list[SnapshotSummaryResponse]
    total_count: int


class SnapshotVerifyResponse(BaseModel):
    """Outcome of cryptographic snapshot integrity verification."""

    model_config = ConfigDict(frozen=True)

    snapshot_id: str
    status: str
    is_valid: bool
    fingerprint: str
    recomputed_fingerprint: str | None = None
    details: str | None = None
    findings: list[str] = Field(default_factory=list)


class ExportCreateRequest(BaseModel):
    """Request payload to initiate a deterministic export."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    format: ExportFormat = Field(
        ..., description="Export format (json, csv, graphml, dot, snapshot)."
    )
    scope: ExportScope = Field(default=ExportScope.SCHEMA, description="Export structural scope.")
    target_id: str | None = Field(
        default=None, description="Target table or namespace ID if scoped."
    )
    schema_id: str | None = Field(default=None, description="Canonical schema ID to export.")
    snapshot_id: str | None = Field(default=None, description="Snapshot ID to export.")
    safe_mode: bool = Field(default=True, description="Enable formula injection defense for CSV.")
    pretty_print: bool = Field(default=False, description="Format export with indentation.")


class ExportJobResponse(BaseModel):
    """Status and metadata descriptor for an export job."""

    model_config = ConfigDict(frozen=True)

    export_id: str
    job_id: str
    status: str
    format: str
    scope: str
    created_at: datetime
    completed_at: datetime | None = None
    error_message: str | None = None
    download_url: str | None = None


# --- Phase 8.1 Diagnostics Schemas ---


class DiagnosticRuleMetadataResponse(BaseModel):
    """Metadata descriptor for a diagnostic rule."""

    model_config = ConfigDict(frozen=True)

    rule_id: str = Field(..., description="Stable rule identifier (e.g. DERA-SCHEMA-001).")
    title: str = Field(..., description="Human-readable title.")
    description: str = Field(..., description="Description of rule purpose and checks.")
    version: str = Field(..., description="Semantic rule version.")
    category: str = Field(..., description="Functional taxonomy category.")
    default_severity: str = Field(..., description="Default finding severity.")
    supported_object_kinds: list[str] = Field(..., description="Applicable schema object kinds.")
    required_capabilities: list[str] = Field(
        default_factory=list, description="Required capabilities."
    )
    supported_engines: list[str] = Field(
        default_factory=list, description="Supported database engines."
    )
    documentation_url: str = Field(default="", description="Reference documentation URL.")


class DiagnosticEvidenceResponse(BaseModel):
    """Verifiable piece of evidence supporting a diagnostic finding."""

    model_config = ConfigDict(frozen=True)

    object_id: str = Field(..., description="Canonical ID of the object providing evidence.")
    field_name: str = Field(..., description="Schema field or attribute observed.")
    observed_value: Any = Field(..., description="Observed value from metadata.")
    expected_value: Any | None = Field(default=None, description="Expected value if applicable.")
    message: str = Field(default="", description="Explanatory message.")
    context_data: dict[str, Any] = Field(default_factory=dict, description="Contextual details.")


class DiagnosticFindingResponse(BaseModel):
    """Structured diagnostic finding with verifiable evidence and recommendation."""

    model_config = ConfigDict(frozen=True)

    fingerprint: str = Field(..., description="Stable SHA-256 finding fingerprint.")
    rule_id: str = Field(..., description="ID of rule that produced the finding.")
    rule_version: str = Field(..., description="Version of rule that produced the finding.")
    object_id: str = Field(..., description="Canonical ID of the affected schema entity.")
    severity: str = Field(..., description="Finding severity level.")
    title: str = Field(..., description="Finding title.")
    description: str = Field(..., description="Detailed description.")
    evidence: list[DiagnosticEvidenceResponse] = Field(
        ..., description="Supporting evidence items."
    )
    severity_rationale: str = Field(..., description="Explanation of assigned severity.")
    recommendation: str | None = Field(default=None, description="Recommended remediation action.")
    category: str | None = Field(default=None, description="Rule category.")
    classification: str | None = Field(default=None, description="Finding classification.")
    original_severity: str | None = Field(default=None, description="Original rule severity.")
    confidence: str | None = Field(default=None, description="Categorical confidence status.")
    metadata_completeness: str | None = Field(default=None, description="Evidence completeness.")
    structured_recommendation: dict[str, Any] | None = Field(
        default=None, description="Structured recommendation details."
    )
    lifecycle_state: str | None = Field(default=None, description="Finding lifecycle state.")
    is_suppressed: bool = Field(default=False, description="Whether finding is suppressed.")
    suppression_id: str | None = Field(
        default=None, description="ID of active suppression if applied."
    )
    override_id: str | None = Field(default=None, description="ID of severity override if applied.")
    priority_score: int | None = Field(default=None, description="Deterministic priority score.")
    priority_rank: str | None = Field(default=None, description="Priority rank.")
    finding_id: str | None = Field(default=None, description="Unique finding ID.")


class DiagnosticEvaluationResponse(BaseModel):
    """Execution status and metrics for an individual diagnostic rule."""

    model_config = ConfigDict(frozen=True)

    rule_id: str = Field(..., description="Rule identifier.")
    rule_version: str = Field(..., description="Rule version.")
    status: str = Field(..., description="Evaluation status.")
    execution_duration_ms: float = Field(..., description="Rule execution time in milliseconds.")
    message: str = Field(default="", description="Status explanation.")
    error_details: str | None = Field(
        default=None, description="Error details if execution failed."
    )


class DiagnosticReportResponse(BaseModel):
    """Complete diagnostic report for an analyzed canonical schema or snapshot."""

    model_config = ConfigDict(frozen=True)

    evaluation_id: str = Field(..., description="Unique evaluation run identifier.")
    evaluated_at: str = Field(..., description="ISO 8601 evaluation timestamp.")
    snapshot_id: str | None = Field(
        default=None, description="Source snapshot ID if evaluated from snapshot."
    )
    rule_set_version: str = Field(..., description="Rule set version.")
    config_fingerprint: str = Field(..., description="Configuration fingerprint.")
    report_hash: str = Field(..., description="Cryptographic content hash of the report.")
    source_engine: str = Field(..., description="Database engine.")
    summary: dict[str, Any] = Field(..., description="Aggregated summary counts.")
    coverage: dict[str, Any] = Field(..., description="Rule execution coverage.")
    findings: list[DiagnosticFindingResponse] = Field(..., description="Detected findings.")
    rule_evaluations: list[DiagnosticEvaluationResponse] = Field(
        ..., description="Per-rule outcomes."
    )
    explainability: dict[str, Any] | None = Field(
        default=None, description="Report explainability metrics."
    )
    severity_policy_version: str = Field(default="1.0.0", description="Severity policy version.")
    recommendation_catalog_version: str = Field(
        default="1.0.0", description="Recommendation catalog version."
    )
    suppressions_applied: list[dict[str, Any]] = Field(
        default_factory=list, description="Suppressions applied during evaluation."
    )
    severity_overrides_applied: list[dict[str, Any]] = Field(
        default_factory=list, description="Severity overrides applied."
    )


class DiagnosticEvaluateRequest(BaseModel):
    """Optional configuration payload to customize diagnostic evaluation."""

    model_config = ConfigDict(frozen=True)

    enabled_rule_ids: list[str] | None = Field(
        default=None, description="Explicit list of rule IDs to evaluate."
    )
    disabled_rule_ids: list[str] = Field(default_factory=list, description="Rule IDs to suppress.")
    suppressions: list[dict[str, Any]] = Field(
        default_factory=list, description="Configured suppression records."
    )
    severity_overrides: list[dict[str, Any]] = Field(
        default_factory=list, description="Configured severity overrides."
    )
