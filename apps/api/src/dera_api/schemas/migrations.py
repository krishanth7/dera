"""DERA API — Phase 9 Migration Engineering Contracts and Pydantic Schemas.

Defines deterministic, RFC 9457-compliant request/response models for:
- Snapshot listing and selection
- Schema snapshot comparison
- Risk assessment and blast radius metrics
- Migration plan generation and dependency ordering
- Dialect-aware SQL compilation and verification
- Governance review, decision lifecycle, and separation of duties
- Immutable audit evidence and artifact export
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

# --- Snapshots ---


class MigrationSnapshotSummary(BaseModel):
    """Summary of an immutable schema snapshot available for migration comparison."""

    id: str = Field(..., description="Unique snapshot identifier")
    name: str = Field(..., description="Display name or database identifier")
    database_id: str = Field(..., description="Source database identifier")
    database_name: str = Field(..., description="Database name")
    engine: str = Field(..., description="Database engine (postgresql, sqlite, mysql, mariadb)")
    engine_version: str = Field(default="unknown", description="Database engine version")
    captured_at: datetime = Field(..., description="Snapshot capture timestamp")
    fingerprint: str = Field(..., description="Cryptographic SHA-256 schema fingerprint")
    table_count: int = Field(default=0, description="Number of tables in snapshot")
    view_count: int = Field(default=0, description="Number of views in snapshot")
    tags: list[str] = Field(default_factory=list, description="Categorization tags")


class MigrationSnapshotListResponse(BaseModel):
    """Catalog of snapshots accessible to the authorized workspace."""

    snapshots: list[MigrationSnapshotSummary] = Field(default_factory=list)
    total_count: int = Field(default=0)


# --- Comparison (Phase 9.1) ---


class MigrationCompareRequest(BaseModel):
    """Request to compare two snapshots within authorized workspace."""

    baseline_snapshot_id: str = Field(..., description="Source baseline snapshot ID")
    target_snapshot_id: str = Field(..., description="Target destination snapshot ID")


class ComparisonSummarySchema(BaseModel):
    """Summary metrics of structural diffs."""

    total_changes: int = 0
    total_added: int = 0
    total_removed: int = 0
    total_modified: int = 0
    tables_affected: int = 0


class SchemaComparisonResponse(BaseModel):
    """Deterministic comparison report between two schema snapshots."""

    comparison_id: str = Field(..., description="Deterministic comparison ID")
    baseline_snapshot_id: str = Field(..., description="Source baseline snapshot ID")
    target_snapshot_id: str = Field(..., description="Target destination snapshot ID")
    engine: str = Field(..., description="Database engine")
    compared_at: datetime = Field(..., description="Comparison generation timestamp")
    comparison_fingerprint: str = Field(..., description="SHA-256 fingerprint of comparison report")
    summary: ComparisonSummarySchema = Field(default_factory=ComparisonSummarySchema)
    changes: list[dict[str, Any]] = Field(
        default_factory=list, description="Normalized structural changes"
    )


# --- Risk Assessment (Phase 9.2) ---


class MigrationRiskRequest(BaseModel):
    """Request to evaluate migration risks from a verified comparison report."""

    comparison_id: str = Field(..., description="Identifier of the comparison report to analyze")


class RiskSummarySchema(BaseModel):
    """Aggregate risk counts and backward-compatibility metrics."""

    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    informational_count: int = 0
    breaking_change_count: int = 0
    potentially_breaking: int = 0
    safe_change_count: int = 0
    overall_risk_level: str = "LOW"
    overall_recommendation: str = "PROCEED"


class MigrationRiskResponse(BaseModel):
    """Deterministic risk analysis and recommendation report."""

    report_id: str = Field(..., description="Unique risk report identifier")
    comparison_id: str = Field(..., description="Comparison ID analyzed")
    generated_at: datetime = Field(..., description="Generation timestamp")
    fingerprint: str = Field(..., description="Cryptographic SHA-256 fingerprint")
    summary: RiskSummarySchema = Field(default_factory=RiskSummarySchema)
    risks: list[dict[str, Any]] = Field(
        default_factory=list, description="Individual classified risk items"
    )
    recommendations: list[dict[str, Any]] = Field(
        default_factory=list, description="Prescriptive engineering recommendations"
    )


# --- Migration Planning (Phase 9.3) ---


class MigrationPlanRequest(BaseModel):
    """Request to generate a dependency-ordered migration plan."""

    comparison_id: str = Field(..., description="Comparison ID to plan operations for")


class PlanSummarySchema(BaseModel):
    """Metrics regarding planned migration stages and operations."""

    total_operations: int = 0
    total_stages: int = 0
    estimated_duration_seconds: float = 0.0
    manual_decision_gates_count: int = 0
    manual_gates_count: int = 0


class MigrationPlanResponse(BaseModel):
    """Deterministic, dependency-ordered migration plan."""

    plan_id: str = Field(..., description="Unique plan identifier")
    comparison_id: str = Field(..., description="Source comparison identifier")
    engine: str = Field(..., description="Target database engine")
    plan_fingerprint: str = Field(..., description="SHA-256 fingerprint of migration plan")
    summary: PlanSummarySchema = Field(default_factory=PlanSummarySchema)
    stages: list[dict[str, Any]] = Field(
        default_factory=list, description="Ordered execution stages"
    )
    unsupported_operations: list[dict[str, Any]] = Field(
        default_factory=list, description="Operations requiring manual migration"
    )


# --- SQL Compiler (Phase 9.4) ---


class MigrationSqlCompileRequest(BaseModel):
    """Request to compile review-only SQL artifact from plan."""

    plan_id: str = Field(..., description="Plan ID to compile SQL statements for")
    target_dialect: str | None = Field(
        default=None, description="Optional dialect override (must match engine)"
    )
    target_version: str | None = Field(default=None, description="Engine version")


class MigrationSqlArtifactResponse(BaseModel):
    """Review-only compiled SQL artifact and validation report."""

    artifact_id: str = Field(..., description="Unique artifact identifier")
    plan_id: str = Field(..., description="Source plan identifier")
    target_dialect: str = Field(..., description="Compiled SQL dialect")
    target_version: str = Field(default="default", description="Dialect version")
    compiled_at: datetime = Field(..., description="Compilation timestamp")
    artifact_fingerprint: str = Field(..., description="Cryptographic SHA-256 artifact hash")
    forward_sql: str = Field(..., description="Forward DDL statements for migration")
    rollback_sql: str = Field(
        default="", description="Compensating rollback SQL if structurally possible"
    )
    transactional: bool = Field(
        default=True, description="Whether DDL can be wrapped in a transaction"
    )
    validation_status: str = Field(
        default="VALIDATED", description="Offline structural validation status"
    )
    validation_errors: list[str] = Field(
        default_factory=list, description="Offline validation errors or warnings"
    )
    disclaimer: str = Field(
        default="GENERATED FOR REVIEW — NOT EXECUTED",
        description="Mandatory safety guarantee",
    )


# --- Governance & Approvals (Phase 9.5) ---


class GovernanceReviewSubmitRequest(BaseModel):
    """Request to submit a compiled migration artifact for governance review."""

    artifact_id: str = Field(..., description="Artifact ID to submit")
    title: str = Field(..., description="Review title or ticket reference")
    description: str = Field(default="", description="Business rationale and migration scope")
    required_approvals: int = Field(default=1, ge=1, le=5, description="Required approval quorum")


class GovernanceDecisionSubmitRequest(BaseModel):
    """Request by an authorized reviewer to record an approval, rejection, or changes request."""

    decision_type: str = Field(..., description="APPROVE, REJECT, or REQUEST_CHANGES")
    rationale: str = Field(..., min_length=5, description="Technical rationale for the decision")


class GovernanceReviewResponse(BaseModel):
    """Current governance review state and approval progress."""

    review_id: str = Field(..., description="Unique review identifier")
    artifact_id: str = Field(..., description="Bound artifact identifier")
    artifact_fingerprint: str = Field(..., description="Cryptographic fingerprint of reviewed SQL")
    requester_id: str = Field(..., description="User ID who created the review request")
    status: str = Field(
        ..., description="SUBMITTED, UNDER_REVIEW, APPROVED, REJECTED, CHANGES_REQUESTED"
    )
    title: str = Field(..., description="Review title")
    description: str = Field(default="", description="Review description")
    created_at: str | datetime = Field(..., description="Creation timestamp")
    updated_at: str | datetime = Field(..., description="Last update timestamp")
    required_approvals: int = Field(default=1)
    current_approvals: int = Field(default=0)
    decisions: list[dict[str, Any]] = Field(
        default_factory=list, description="Recorded reviewer decisions"
    )


# --- Audit & Export (Phase 9.5) ---


class AuditEventResponse(BaseModel):
    """Cryptographic audit event log entry."""

    event_id: str = Field(..., description="Unique event identifier")
    review_id: str = Field(..., description="Bound review identifier")
    event_type: str = Field(
        ..., description="LIFECYCLE_CHANGE, DECISION_RECORDED, ARTIFACT_EXPORTED"
    )
    actor_id: str = Field(..., description="Actor user ID")
    actor_role: str = Field(..., description="Actor role at time of event")
    timestamp: str | datetime = Field(..., description="Event timestamp")
    payload_hash: str = Field(..., description="SHA-256 hash of event payload")
    details: dict[str, Any] = Field(default_factory=dict)


class GovernanceAuditResponse(BaseModel):
    """Comprehensive audit trail for a governance review."""

    review_id: str = Field(..., description="Review identifier")
    events: list[AuditEventResponse] = Field(default_factory=list)


class MigrationExportResponse(BaseModel):
    """Authorized download package for an approved migration artifact."""

    export_id: str = Field(..., description="Unique export identifier")
    review_id: str = Field(..., description="Approved review identifier")
    artifact_id: str = Field(..., description="Artifact identifier")
    artifact_fingerprint: str = Field(..., description="Cryptographic SHA-256 fingerprint")
    target_dialect: str = Field(..., description="SQL dialect")
    forward_sql: str = Field(..., description="Approved forward migration SQL")
    rollback_sql: str = Field(default="", description="Approved rollback SQL")
    exported_at: datetime = Field(..., description="Export generation timestamp")
    exported_by: str = Field(..., description="Authorizing user ID who exported the artifact")
    governance_status: str = Field(
        default="APPROVED", description="Verified governance approval state"
    )
    disclaimer: str = Field(
        default="GENERATED FOR REVIEW — NOT EXECUTED",
        description="Mandatory safety guarantee",
    )
