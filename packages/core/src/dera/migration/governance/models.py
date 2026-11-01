"""Phase 9.5 Migration Governance Domain Models.

Defines review requests, reviewer decisions, safety gate evaluations,
governance policies, audit events, and approval evidence bundles.
"""

from typing import Any

from pydantic import BaseModel, Field

from dera.migration.governance.enums import (
    ExportEligibilityStatus,
    ReviewDecisionType,
    ReviewLifecycleStatus,
    SafetyGateStatus,
)


class SafetyGateResult(BaseModel):
    """Result of evaluating an individual safety gate rule."""

    gate_id: str
    rule_version: str
    status: SafetyGateStatus
    rationale: str
    required_remediation: str | None = None
    input_evidence: dict[str, Any] = Field(default_factory=dict)


class ReviewDecision(BaseModel):
    """Immutable record of an individual reviewer's decision."""

    decision_id: str
    review_id: str
    reviewer_id: str
    reviewer_role: str
    decision_type: ReviewDecisionType
    artifact_fingerprint: str
    policy_version: str
    reason: str
    timestamp: str
    evidence_references: list[str] = Field(default_factory=list)


class GovernancePolicy(BaseModel):
    """Immutable versioned governance policy specification."""

    policy_id: str = "gov_policy_default"
    policy_version: str = "1.0.0"
    workspace_id: str
    required_approval_quorum: int = 1
    enforce_separation_of_duties: bool = True
    require_admin_for_destructive: bool = True
    allowed_reviewer_roles: list[str] = Field(default_factory=lambda: ["owner", "admin", "editor"])
    effective_status: str = "ACTIVE"


class AuditEvent(BaseModel):
    """Append-only audit event record with cryptographic tamper-evident hash chaining."""

    event_id: str
    review_id: str
    workspace_id: str
    actor_id: str
    event_type: str
    previous_state: str | None = None
    new_state: str
    artifact_fingerprint: str
    policy_version: str
    timestamp: str
    event_payload_digest: str
    previous_event_hash: str
    event_hash: str


class MigrationReviewRequest(BaseModel):
    """Authoritative review request governing a Phase 9.4 SQL artifact."""

    review_id: str
    workspace_id: str
    artifact_id: str
    artifact_fingerprint: str
    migration_plan_fingerprint: str
    risk_report_fingerprint: str
    target_dialect: str
    target_engine_version: str | None = None
    requester_id: str
    policy_version: str = "1.0.0"
    status: ReviewLifecycleStatus = ReviewLifecycleStatus.DRAFT
    version_number: int = 1
    required_approvals: int = 1
    created_at: str

    assigned_reviewer_ids: list[str] = Field(default_factory=list)
    decisions: list[ReviewDecision] = Field(default_factory=list)
    safety_gate_results: list[SafetyGateResult] = Field(default_factory=list)
    audit_events: list[AuditEvent] = Field(default_factory=list)
    is_invalidated: bool = False
    invalidation_reason: str | None = None


class ApprovalEvidenceBundle(BaseModel):
    """Tamper-evident verification bundle generated upon review completion."""

    bundle_id: str
    review_id: str
    workspace_id: str
    artifact_id: str
    artifact_fingerprint: str
    policy_version: str
    review_status: ReviewLifecycleStatus
    export_eligibility: ExportEligibilityStatus
    safety_gate_results: list[SafetyGateResult]
    decisions: list[ReviewDecision]
    audit_chain_head_hash: str
    evidence_fingerprint: str
