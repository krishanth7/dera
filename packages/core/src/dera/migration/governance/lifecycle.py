"""Governance Lifecycle and Quorum Evaluation Engine.

Enforces:
1. Valid state transitions in the review lifecycle.
2. Separation of duties (Requester cannot approve their own request).
3. Approval quorum evaluation (e.g. required approvals, role requirements).
4. Approval invalidation upon artifact alteration.
5. Export eligibility evaluation.
"""

import hashlib
import json
from typing import Dict, List, Optional, Set, Tuple

from dera.migration.governance.audit import AuditTrailManager
from dera.migration.governance.enums import (
    ExportEligibilityStatus,
    ReviewDecisionType,
    ReviewLifecycleStatus,
    SafetyGateStatus,
)
from dera.migration.governance.models import (
    ApprovalEvidenceBundle,
    AuditEvent,
    GovernancePolicy,
    MigrationReviewRequest,
    ReviewDecision,
    SafetyGateResult,
)
from dera.migration.sql.reports import SqlMigrationArtifact


class GovernanceEngine:
    """Core state machine and policy evaluation engine for migration reviews."""

    ALLOWED_TRANSITIONS: Dict[ReviewLifecycleStatus, Set[ReviewLifecycleStatus]] = {
        ReviewLifecycleStatus.DRAFT: {
            ReviewLifecycleStatus.SUBMITTED,
            ReviewLifecycleStatus.CANCELLED,
        },
        ReviewLifecycleStatus.SUBMITTED: {
            ReviewLifecycleStatus.UNDER_REVIEW,
            ReviewLifecycleStatus.CANCELLED,
            ReviewLifecycleStatus.BLOCKED,
        },
        ReviewLifecycleStatus.UNDER_REVIEW: {
            ReviewLifecycleStatus.APPROVED,
            ReviewLifecycleStatus.REJECTED,
            ReviewLifecycleStatus.CHANGES_REQUESTED,
            ReviewLifecycleStatus.CANCELLED,
            ReviewLifecycleStatus.BLOCKED,
        },
        ReviewLifecycleStatus.CHANGES_REQUESTED: {
            ReviewLifecycleStatus.SUBMITTED,
            ReviewLifecycleStatus.CANCELLED,
            ReviewLifecycleStatus.SUPERSEDED,
        },
        ReviewLifecycleStatus.APPROVED: {
            ReviewLifecycleStatus.SUPERSEDED,
            ReviewLifecycleStatus.BLOCKED,
        },
        ReviewLifecycleStatus.REJECTED: {
            ReviewLifecycleStatus.SUPERSEDED,
        },
        ReviewLifecycleStatus.CANCELLED: set(),
        ReviewLifecycleStatus.SUPERSEDED: set(),
        ReviewLifecycleStatus.BLOCKED: {
            ReviewLifecycleStatus.CANCELLED,
            ReviewLifecycleStatus.SUPERSEDED,
        },
    }

    @classmethod
    def validate_transition(
        cls,
        current_status: ReviewLifecycleStatus,
        target_status: ReviewLifecycleStatus,
    ) -> bool:
        """Verify whether the proposed state transition is permissible."""
        return target_status in cls.ALLOWED_TRANSITIONS.get(current_status, set())

    @classmethod
    def record_decision(
        cls,
        review: MigrationReviewRequest,
        policy: GovernancePolicy,
        decision: ReviewDecision,
        actor_role: str,
    ) -> Tuple[bool, Optional[str]]:
        """Record reviewer decision enforcing SoD and role authorization."""
        if review.status not in (ReviewLifecycleStatus.SUBMITTED, ReviewLifecycleStatus.UNDER_REVIEW):
            return False, f"Review in status '{review.status.value}' cannot accept decisions."

        if actor_role.lower() not in [r.lower() for r in policy.allowed_reviewer_roles]:
            return False, f"Actor role '{actor_role}' is not in policy allowed reviewer roles."

        # Separation of Duties check
        if policy.enforce_separation_of_duties and decision.reviewer_id == review.requester_id:
            if decision.decision_type == ReviewDecisionType.APPROVE:
                return False, "Separation of duties policy forbids the requester from approving their own review request."

        # Verify fingerprint binding
        if decision.artifact_fingerprint != review.artifact_fingerprint:
            return False, "Decision artifact fingerprint does not match review request artifact fingerprint."

        # Add decision and transition to UNDER_REVIEW if currently SUBMITTED
        review.decisions.append(decision)
        if review.status == ReviewLifecycleStatus.SUBMITTED:
            review.status = ReviewLifecycleStatus.UNDER_REVIEW

        # Evaluate lifecycle transition based on decision
        if decision.decision_type == ReviewDecisionType.REJECT:
            review.status = ReviewLifecycleStatus.REJECTED
        elif decision.decision_type == ReviewDecisionType.REQUEST_CHANGES:
            review.status = ReviewLifecycleStatus.CHANGES_REQUESTED
        elif decision.decision_type == ReviewDecisionType.APPROVE:
            # Check quorum
            is_quorum_met, quorum_reason = cls.evaluate_quorum(review, policy)
            if is_quorum_met:
                review.status = ReviewLifecycleStatus.APPROVED

        return True, None

    @classmethod
    def evaluate_quorum(
        cls,
        review: MigrationReviewRequest,
        policy: GovernancePolicy,
    ) -> Tuple[bool, str]:
        """Determine if approval quorum is satisfied."""
        approvals = [d for d in review.decisions if d.decision_type == ReviewDecisionType.APPROVE]

        # Ensure unique reviewers
        unique_approvers = {d.reviewer_id for d in approvals}
        if len(unique_approvers) < policy.required_approval_quorum:
            return False, f"Required quorum is {policy.required_approval_quorum}, but only {len(unique_approvers)} distinct approval(s) present."

        # Check safety gates - all blocking gates must pass
        for gate in review.safety_gate_results:
            if gate.status in (SafetyGateStatus.FAIL, SafetyGateStatus.BLOCKED):
                return False, f"Safety gate '{gate.gate_id}' is {gate.status.value}. Quorum cannot be achieved."

        # Check destructive operations requirement
        has_destructive_gate = any(
            g.gate_id == "GATE-DESTRUCTIVE-003" and g.status == SafetyGateStatus.REVIEW_REQUIRED
            for g in review.safety_gate_results
        )
        if has_destructive_gate and policy.require_admin_for_destructive:
            admin_approvers = [
                d for d in approvals if d.reviewer_role.lower() in ("admin", "owner")
            ]
            if not admin_approvers:
                return False, "Destructive operations policy requires approval from at least one Admin or Owner."

        return True, "Quorum successfully met."

    @classmethod
    def invalidate_if_artifact_changed(
        cls,
        review: MigrationReviewRequest,
        current_artifact: SqlMigrationArtifact,
    ) -> bool:
        """Invalidate approvals if the SQL artifact fingerprint or content has changed."""
        if current_artifact.artifact_fingerprint != review.artifact_fingerprint:
            review.is_invalidated = True
            review.status = ReviewLifecycleStatus.BLOCKED
            review.invalidation_reason = (
                f"SQL artifact changed from '{review.artifact_fingerprint}' to '{current_artifact.artifact_fingerprint}'. Approvals invalidated."
            )
            return True
        return False

    @classmethod
    def evaluate_export_eligibility(
        cls,
        review: MigrationReviewRequest,
    ) -> ExportEligibilityStatus:
        """Assess if the artifact is eligible for export."""
        if review.is_invalidated or review.status == ReviewLifecycleStatus.BLOCKED:
            return ExportEligibilityStatus.BLOCKED
        if review.status == ReviewLifecycleStatus.APPROVED:
            return ExportEligibilityStatus.ELIGIBLE_FOR_CONTROLLED_EXPORT
        return ExportEligibilityStatus.REVIEW_REQUIRED

    @classmethod
    def generate_evidence_bundle(
        cls,
        review: MigrationReviewRequest,
        policy: GovernancePolicy,
    ) -> ApprovalEvidenceBundle:
        """Create an immutable evidence bundle documenting the review outcome."""
        export_status = cls.evaluate_export_eligibility(review)
        chain_head = review.audit_events[-1].event_hash if review.audit_events else AuditTrailManager.GENESIS_HASH

        payload = {
            "review_id": review.review_id,
            "workspace_id": review.workspace_id,
            "artifact_fingerprint": review.artifact_fingerprint,
            "policy_version": policy.policy_version,
            "review_status": review.status.value,
            "export_eligibility": export_status.value,
            "audit_chain_head": chain_head,
            "approvals_count": len([d for d in review.decisions if d.decision_type == ReviewDecisionType.APPROVE]),
        }
        canonical_json = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        fp = hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()

        return ApprovalEvidenceBundle(
            bundle_id=f"evb_{fp[:16]}",
            review_id=review.review_id,
            workspace_id=review.workspace_id,
            artifact_id=review.artifact_id,
            artifact_fingerprint=review.artifact_fingerprint,
            policy_version=policy.policy_version,
            review_status=review.status,
            export_eligibility=export_status,
            safety_gate_results=review.safety_gate_results,
            decisions=review.decisions,
            audit_chain_head_hash=chain_head,
            evidence_fingerprint=fp,
        )
