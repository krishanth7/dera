"""Unit and Integration Tests for Phase 9.5 Migration Governance.

Covers:
1. Review lifecycle state transitions.
2. Safety gate evaluation (integrity, destructive statements, validation).
3. Separation of duties (SoD) enforcement (requester self-approval prohibition).
4. Approval quorum evaluation.
5. Approval invalidation upon artifact modification.
6. Append-only tamper-evident audit hash chaining.
7. Controlled export eligibility and evidence bundle generation.
"""

import pytest
from dera.migration.governance import (
    ApprovalEvidenceBundle,
    AuditEvent,
    AuditTrailManager,
    ExportEligibilityStatus,
    GovernanceEngine,
    GovernancePolicy,
    MigrationReviewRequest,
    ReviewDecision,
    ReviewDecisionType,
    ReviewLifecycleStatus,
    SafetyGateEvaluator,
    SafetyGateResult,
    SafetyGateStatus,
)
from dera.migration.sql.enums import SqlDialectType, SqlGenerationStatus
from dera.migration.sql.reports import SqlArtifactSummary, SqlMigrationArtifact


def _make_dummy_artifact(is_destructive=False, validation_issues_count=0, status=SqlGenerationStatus.GENERATED):
    return SqlMigrationArtifact(
        artifact_id="art_test_123",
        source_plan_id="plan_123",
        source_plan_fingerprint="plan_fp_123",
        dialect=SqlDialectType.POSTGRESQL,
        target_engine="postgresql",
        compiler_version="1.0.0",
        status=status,
        artifact_fingerprint="art_fp_original",
        summary=SqlArtifactSummary(
            total_statements=2,
            destructive_statements=1 if is_destructive else 0,
            review_required_statements=1 if is_destructive else 0,
            transaction_blocks_count=1,
            preflight_checks_count=0,
            rollback_statements_count=1,
            validation_issues_count=validation_issues_count,
        ),
        rendered_sql_script="BEGIN;\nCREATE TABLE test ();\nCOMMIT;\n",
    )


def test_review_lifecycle_transitions():
    """Verify that permitted and forbidden state transitions are enforced."""
    # Permitted: DRAFT -> SUBMITTED -> UNDER_REVIEW -> APPROVED
    assert GovernanceEngine.validate_transition(ReviewLifecycleStatus.DRAFT, ReviewLifecycleStatus.SUBMITTED) is True
    assert GovernanceEngine.validate_transition(ReviewLifecycleStatus.SUBMITTED, ReviewLifecycleStatus.UNDER_REVIEW) is True
    assert GovernanceEngine.validate_transition(ReviewLifecycleStatus.UNDER_REVIEW, ReviewLifecycleStatus.APPROVED) is True

    # Forbidden: DRAFT directly to APPROVED
    assert GovernanceEngine.validate_transition(ReviewLifecycleStatus.DRAFT, ReviewLifecycleStatus.APPROVED) is False

    # Forbidden: APPROVED back to DRAFT
    assert GovernanceEngine.validate_transition(ReviewLifecycleStatus.APPROVED, ReviewLifecycleStatus.DRAFT) is False


def test_safety_gate_evaluation():
    """Verify that safety gates detect destructive changes and validation issues."""
    policy = GovernancePolicy(workspace_id="ws_123")

    # Safe artifact
    safe_art = _make_dummy_artifact(is_destructive=False)
    gates = SafetyGateEvaluator.evaluate_artifact_gates(safe_art, policy)
    gate_statuses = {g.gate_id: g.status for g in gates}
    assert gate_statuses["GATE-STATUS-001"] == SafetyGateStatus.PASS
    assert gate_statuses["GATE-VALIDATION-002"] == SafetyGateStatus.PASS
    assert gate_statuses["GATE-DESTRUCTIVE-003"] == SafetyGateStatus.PASS

    # Destructive artifact
    dest_art = _make_dummy_artifact(is_destructive=True)
    gates_dest = SafetyGateEvaluator.evaluate_artifact_gates(dest_art, policy)
    dest_map = {g.gate_id: g.status for g in gates_dest}
    assert dest_map["GATE-DESTRUCTIVE-003"] == SafetyGateStatus.REVIEW_REQUIRED


def test_separation_of_duties_blocks_self_approval():
    """Verify that a requester cannot approve their own review request when SoD is active."""
    policy = GovernancePolicy(workspace_id="ws_123", enforce_separation_of_duties=True)
    review = MigrationReviewRequest(
        review_id="rev_1",
        workspace_id="ws_123",
        artifact_id="art_1",
        artifact_fingerprint="art_fp_original",
        migration_plan_fingerprint="plan_fp",
        risk_report_fingerprint="risk_fp",
        target_dialect="POSTGRESQL",
        requester_id="user_alice",
        status=ReviewLifecycleStatus.SUBMITTED,
        created_at="2026-11-01T00:00:00Z",
    )

    decision = ReviewDecision(
        decision_id="dec_1",
        review_id="rev_1",
        reviewer_id="user_alice",  # Same as requester
        reviewer_role="admin",
        decision_type=ReviewDecisionType.APPROVE,
        artifact_fingerprint="art_fp_original",
        policy_version="1.0.0",
        reason="Self-approving my change.",
        timestamp="2026-11-01T01:00:00Z",
    )

    success, err = GovernanceEngine.record_decision(review, policy, decision, actor_role="admin")
    assert success is False
    assert "Separation of duties" in err
    assert review.status == ReviewLifecycleStatus.SUBMITTED


def test_approval_quorum_and_destructive_admin_requirement():
    """Verify quorum evaluation and admin requirement for destructive changes."""
    policy = GovernancePolicy(
        workspace_id="ws_123",
        required_approval_quorum=2,
        require_admin_for_destructive=True,
    )

    review = MigrationReviewRequest(
        review_id="rev_2",
        workspace_id="ws_123",
        artifact_id="art_2",
        artifact_fingerprint="art_fp_original",
        migration_plan_fingerprint="plan_fp",
        risk_report_fingerprint="risk_fp",
        target_dialect="POSTGRESQL",
        requester_id="user_alice",
        status=ReviewLifecycleStatus.SUBMITTED,
        created_at="2026-11-01T00:00:00Z",
        safety_gate_results=[
            SafetyGateResult(
                gate_id="GATE-DESTRUCTIVE-003",
                rule_version="1.0.0",
                status=SafetyGateStatus.REVIEW_REQUIRED,
                rationale="Destructive drop table present.",
            )
        ],
    )

    # First approval by editor
    dec1 = ReviewDecision(
        decision_id="dec_1",
        review_id="rev_2",
        reviewer_id="user_bob",
        reviewer_role="editor",
        decision_type=ReviewDecisionType.APPROVE,
        artifact_fingerprint="art_fp_original",
        policy_version="1.0.0",
        reason="Looks good to me.",
        timestamp="2026-11-01T01:00:00Z",
    )
    ok, _ = GovernanceEngine.record_decision(review, policy, dec1, actor_role="editor")
    assert ok is True
    # Quorum not met yet (need 2, and need at least one admin)
    assert review.status == ReviewLifecycleStatus.UNDER_REVIEW

    # Second approval by admin
    dec2 = ReviewDecision(
        decision_id="dec_2",
        review_id="rev_2",
        reviewer_id="user_carol",
        reviewer_role="admin",
        decision_type=ReviewDecisionType.APPROVE,
        artifact_fingerprint="art_fp_original",
        policy_version="1.0.0",
        reason="Approved as admin.",
        timestamp="2026-11-01T02:00:00Z",
    )
    ok, _ = GovernanceEngine.record_decision(review, policy, dec2, actor_role="admin")
    assert ok is True
    # Quorum now satisfied!
    assert review.status == ReviewLifecycleStatus.APPROVED


def test_approval_invalidation_when_artifact_changes():
    """Verify that modifying the SQL artifact invalidates existing approvals."""
    review = MigrationReviewRequest(
        review_id="rev_3",
        workspace_id="ws_123",
        artifact_id="art_3",
        artifact_fingerprint="art_fp_original",
        migration_plan_fingerprint="plan_fp",
        risk_report_fingerprint="risk_fp",
        target_dialect="POSTGRESQL",
        requester_id="user_alice",
        status=ReviewLifecycleStatus.APPROVED,
        created_at="2026-11-01T00:00:00Z",
    )

    # Modified artifact with different fingerprint
    altered_artifact = _make_dummy_artifact()
    altered_artifact.artifact_fingerprint = "art_fp_MUTATED_DIFFERENT"

    was_invalidated = GovernanceEngine.invalidate_if_artifact_changed(review, altered_artifact)
    assert was_invalidated is True
    assert review.is_invalidated is True
    assert review.status == ReviewLifecycleStatus.BLOCKED
    assert "SQL artifact changed" in review.invalidation_reason


def test_append_only_audit_hash_chain():
    """Verify cryptographic audit trail hash chaining and tamper detection."""
    evt1 = AuditTrailManager.create_event(
        review_id="rev_audit",
        workspace_id="ws_1",
        actor_id="user_1",
        event_type="REVIEW_CREATED",
        previous_state=None,
        new_state="DRAFT",
        artifact_fingerprint="art_fp",
        policy_version="1.0.0",
        timestamp="2026-11-01T00:00:00Z",
        payload={"action": "create"},
    )

    evt2 = AuditTrailManager.create_event(
        review_id="rev_audit",
        workspace_id="ws_1",
        actor_id="user_1",
        event_type="REVIEW_SUBMITTED",
        previous_state="DRAFT",
        new_state="SUBMITTED",
        artifact_fingerprint="art_fp",
        policy_version="1.0.0",
        timestamp="2026-11-01T00:05:00Z",
        payload={"action": "submit"},
        previous_event_hash=evt1.event_hash,
    )

    chain = [evt1, evt2]
    assert AuditTrailManager.verify_chain(chain) is True

    # Tampering with evt1 breaks chain verification
    tampered_evt1 = evt1.model_copy(update={"new_state": "SUBMITTED"})
    assert AuditTrailManager.verify_chain([tampered_evt1, evt2]) is False


def test_export_eligibility_and_evidence_bundle():
    """Verify controlled export eligibility and evidence bundle generation."""
    policy = GovernancePolicy(workspace_id="ws_123")
    review = MigrationReviewRequest(
        review_id="rev_export",
        workspace_id="ws_123",
        artifact_id="art_export",
        artifact_fingerprint="art_fp_approved",
        migration_plan_fingerprint="plan_fp",
        risk_report_fingerprint="risk_fp",
        target_dialect="POSTGRESQL",
        requester_id="user_alice",
        status=ReviewLifecycleStatus.APPROVED,
        created_at="2026-11-01T00:00:00Z",
    )

    eligibility = GovernanceEngine.evaluate_export_eligibility(review)
    assert eligibility == ExportEligibilityStatus.ELIGIBLE_FOR_CONTROLLED_EXPORT

    bundle = GovernanceEngine.generate_evidence_bundle(review, policy)
    assert bundle.review_id == "rev_export"
    assert bundle.export_eligibility == ExportEligibilityStatus.ELIGIBLE_FOR_CONTROLLED_EXPORT
    assert len(bundle.evidence_fingerprint) == 64
