"""DERA API — Phase 9 Migration Engineering Application Service.

Coordinates schema comparisons, risk assessments, migration plans, SQL compilations,
governance reviews, approval lifecycles, and audit evidence trails in a workspace-isolated environment.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from dera.comparison.engine import SchemaComparisonEngine
from dera.comparison.models import ComparisonReport
from dera.migration.engine import MigrationRiskAnalysisEngine
from dera.migration.governance.audit import AuditTrailManager
from dera.migration.governance.enums import ReviewDecisionType, ReviewLifecycleStatus
from dera.migration.governance.lifecycle import GovernanceEngine
from dera.migration.governance.models import (
    AuditEvent,
    GovernancePolicy,
    MigrationReviewRequest,
    ReviewDecision,
)
from dera.migration.planning.engine import MigrationPlanningEngine
from dera.migration.planning.reports import MigrationPlanReport
from dera.migration.reports.models import MigrationRiskReport
from dera.migration.sql.compiler import SqlMigrationCompiler
from dera.migration.sql.reports import SqlMigrationArtifact
from dera.reverse_engineering.snapshots.models import SchemaSnapshot

from dera_api.api.v1.endpoints.reverse_engineering.service import ReverseEngineeringService


class MigrationService:
    """Workspace-isolated application service for Phase 9 Migration Engineering."""

    def __init__(self, re_service: ReverseEngineeringService) -> None:
        self._re_service = re_service
        self._comparison_engine = SchemaComparisonEngine()
        self._risk_engine = MigrationRiskAnalysisEngine()
        self._planning_engine = MigrationPlanningEngine()
        self._sql_compiler = SqlMigrationCompiler()

        # In-memory tenant-isolated state store: (workspace_id, object_id) -> Object
        self._comparisons: dict[tuple[str, str], ComparisonReport] = {}
        self._risk_reports: dict[tuple[str, str], MigrationRiskReport] = {}
        self._plans: dict[tuple[str, str], MigrationPlanReport] = {}
        self._artifacts: dict[tuple[str, str], SqlMigrationArtifact] = {}
        self._reviews: dict[tuple[str, str], MigrationReviewRequest] = {}

    # --- Snapshots ---

    async def list_snapshots(self, workspace_id: str) -> list[SchemaSnapshot]:
        """List all valid snapshots belonging to the workspace."""
        return await self._re_service.list_snapshots(workspace_id=workspace_id)

    async def get_snapshot(self, workspace_id: str, snapshot_id: str) -> SchemaSnapshot | None:
        """Retrieve snapshot ensuring workspace boundary."""
        return await self._re_service.get_snapshot(
            workspace_id=workspace_id, snapshot_id=snapshot_id
        )

    # --- Comparison (Phase 9.1) ---

    async def compare_snapshots(
        self,
        workspace_id: str,
        baseline_snapshot_id: str,
        target_snapshot_id: str,
    ) -> ComparisonReport:
        """Execute deterministic schema comparison between two workspace snapshots."""
        baseline = await self.get_snapshot(workspace_id, baseline_snapshot_id)
        if not baseline:
            raise ValueError(f"Baseline snapshot '{baseline_snapshot_id}' not found in workspace.")

        target = await self.get_snapshot(workspace_id, target_snapshot_id)
        if not target:
            raise ValueError(f"Target snapshot '{target_snapshot_id}' not found in workspace.")

        if baseline.engine != target.engine:
            raise ValueError(
                f"Cannot compare snapshots across different engines: '{baseline.engine}' vs '{target.engine}'."
            )

        report = self._comparison_engine.compare(baseline=baseline, target=target)
        key = (workspace_id, report.report_id)
        self._comparisons[key] = report
        return report

    def get_comparison(self, workspace_id: str, comparison_id: str) -> ComparisonReport | None:
        """Retrieve comparison report for authorized workspace."""
        return self._comparisons.get((workspace_id, comparison_id))

    # --- Risk Assessment (Phase 9.2) ---

    def assess_risk(self, workspace_id: str, comparison_id: str) -> MigrationRiskReport:
        """Execute deterministic risk assessment for a verified comparison."""
        comparison = self.get_comparison(workspace_id, comparison_id)
        if not comparison:
            raise ValueError(f"Comparison '{comparison_id}' not found in workspace.")

        report = self._risk_engine.analyze(comparison_report=comparison)
        key = (workspace_id, report.report_id)
        self._risk_reports[key] = report
        return report

    def get_risk_report(self, workspace_id: str, report_id: str) -> MigrationRiskReport | None:
        """Retrieve risk report."""
        return self._risk_reports.get((workspace_id, report_id))

    # --- Planning (Phase 9.3) ---

    def generate_plan(self, workspace_id: str, comparison_id: str) -> MigrationPlanReport:
        """Generate dependency-ordered migration plan from verified comparison and risk report."""
        comparison = self.get_comparison(workspace_id, comparison_id)
        if not comparison:
            raise ValueError(f"Comparison '{comparison_id}' not found in workspace.")

        # Ensure associated risk report exists or generate it
        matching_risk = None
        for (ws, _), r_rep in self._risk_reports.items():
            if ws == workspace_id and r_rep.comparison_report_id == comparison_id:
                matching_risk = r_rep
                break

        if not matching_risk:
            matching_risk = self.assess_risk(workspace_id, comparison_id)

        plan = self._planning_engine.plan_migration(
            comparison_report=comparison,
            risk_report=matching_risk,
        )
        key = (workspace_id, plan.plan_id)
        self._plans[key] = plan
        return plan

    def get_plan(self, workspace_id: str, plan_id: str) -> MigrationPlanReport | None:
        """Retrieve migration plan."""
        return self._plans.get((workspace_id, plan_id))

    # --- SQL Compilation (Phase 9.4) ---

    def compile_sql_artifact(
        self,
        workspace_id: str,
        plan_id: str,
        target_dialect: str | None = None,
        target_version: str | None = None,
    ) -> SqlMigrationArtifact:
        """Compile review-only SQL artifact from plan."""
        plan = self.get_plan(workspace_id, plan_id)
        if not plan:
            raise ValueError(f"Plan '{plan_id}' not found in workspace.")

        dialect = target_dialect or plan.target_engine
        artifact = self._sql_compiler.compile_plan(
            plan_report=plan,
            target_engine=dialect,
            target_version=target_version,
        )
        key = (workspace_id, artifact.artifact_id)
        self._artifacts[key] = artifact
        return artifact

    def get_sql_artifact(self, workspace_id: str, artifact_id: str) -> SqlMigrationArtifact | None:
        """Retrieve compiled SQL artifact."""
        return self._artifacts.get((workspace_id, artifact_id))

    # --- Governance & Approvals (Phase 9.5) ---

    async def submit_for_review(
        self,
        workspace_id: str,
        artifact_id: str,
        requester_id: str,
        title: str,
        description: str = "",
        policy: GovernancePolicy | None = None,
        db_session: AsyncSession | None = None,
    ) -> MigrationReviewRequest:
        """Create and submit a governance review request bound to an immutable artifact."""
        artifact = self.get_sql_artifact(workspace_id, artifact_id)
        if not artifact:
            raise ValueError(f"Artifact '{artifact_id}' not found in workspace.")

        review_id = f"rev_{uuid.uuid4().hex[:12]}"
        now_iso = datetime.now(UTC).isoformat()

        # Enforce governance policy quorum and settings
        effective_policy = policy or GovernancePolicy(
            policy_id="gov_policy_default",
            workspace_id=workspace_id,
            required_approval_quorum=1,
            enforce_separation_of_duties=True,
            allowed_reviewer_roles=["owner", "admin", "editor"],
        )

        from dera.migration.governance.safety import SafetyGateEvaluator
        gate_results = SafetyGateEvaluator.evaluate_artifact_gates(artifact, effective_policy)

        # Correct fingerprint linkage: link to source_risk_report_fingerprint
        risk_fp = artifact.source_risk_report_fingerprint or artifact.source_plan_fingerprint

        # Create initial audit event
        audit_event = AuditTrailManager.create_event(
            review_id=review_id,
            workspace_id=workspace_id,
            actor_id=requester_id,
            event_type="SUBMIT_REVIEW",
            previous_state=None,
            new_state=ReviewLifecycleStatus.SUBMITTED.value,
            artifact_fingerprint=artifact.artifact_fingerprint,
            policy_version=effective_policy.policy_version,
            timestamp=now_iso,
            payload={"title": title, "description": description},
            previous_event_hash=None,
        )

        review = MigrationReviewRequest(
            review_id=review_id,
            workspace_id=workspace_id,
            artifact_id=artifact.artifact_id,
            artifact_fingerprint=artifact.artifact_fingerprint,
            migration_plan_fingerprint=artifact.source_plan_fingerprint,
            risk_report_fingerprint=risk_fp,
            target_dialect=artifact.dialect.value
            if hasattr(artifact.dialect, "value")
            else str(artifact.dialect),
            target_engine_version=None,
            requester_id=requester_id,
            policy_version=effective_policy.policy_version,
            status=ReviewLifecycleStatus.SUBMITTED,
            created_at=now_iso,
            decisions=[],
            safety_gate_results=gate_results,
            audit_events=[audit_event],
        )

        review_key = (workspace_id, review_id)
        self._reviews[review_key] = review

        if db_session is not None:
            ws_uuid = uuid.UUID(workspace_id)
            from dera_api.repositories.migration_governance import MigrationGovernanceRepository
            repo = MigrationGovernanceRepository(db_session)
            await repo.save_review(
                workspace_id=ws_uuid,
                review=review,
                title=title,
                description=description,
                required_approvals=effective_policy.required_approval_quorum,
            )

        return review

    async def get_review(
        self,
        workspace_id: str,
        review_id: str,
        db_session: AsyncSession | None = None,
    ) -> MigrationReviewRequest | None:
        """Retrieve review request from cache or durable persistence."""
        cached = self._reviews.get((workspace_id, review_id))
        if cached:
            return cached

        if db_session is not None:
            try:
                ws_uuid = uuid.UUID(workspace_id)
                from dera_api.repositories.migration_governance import MigrationGovernanceRepository
                repo = MigrationGovernanceRepository(db_session)
                record = await repo.get_by_review_id(ws_uuid, review_id)
                if record:
                    domain_review = repo.to_domain_model(record)
                    self._reviews[(workspace_id, review_id)] = domain_review
                    return domain_review
            except Exception:
                pass

        return None

    async def record_decision(
        self,
        workspace_id: str,
        review_id: str,
        reviewer_id: str,
        effective_role: str,
        decision_type_str: str,
        rationale: str,
        policy: GovernancePolicy | None = None,
        db_session: AsyncSession | None = None,
    ) -> MigrationReviewRequest:
        """Record reviewer decision enforcing SoD and role authorization."""
        review = await self.get_review(workspace_id, review_id, db_session=db_session)
        if not review:
            raise ValueError(f"Review '{review_id}' not found in workspace.")

        try:
            decision_type = ReviewDecisionType[decision_type_str.upper()]
        except KeyError:
            raise ValueError(f"Invalid decision type: '{decision_type_str}'.") from None

        decision_id = f"dec_{uuid.uuid4().hex[:12]}"
        now_iso = datetime.now(UTC).isoformat()

        decision = ReviewDecision(
            decision_id=decision_id,
            review_id=review_id,
            reviewer_id=reviewer_id,
            reviewer_role=effective_role,
            decision_type=decision_type,
            artifact_fingerprint=review.artifact_fingerprint,
            policy_version=review.policy_version,
            reason=rationale,
            timestamp=now_iso,
        )

        effective_policy = policy or GovernancePolicy(
            policy_id="default_policy",
            workspace_id=workspace_id,
            required_approval_quorum=1,
            enforce_separation_of_duties=True,
            require_admin_for_destructive=True,
            allowed_reviewer_roles=["owner", "admin", "editor"],
        )

        # Enforce server-side role check: only admin or owner can record approve/reject decisions
        if effective_role.lower() not in ["owner", "admin"]:
            raise PermissionError(
                f"Your role '{effective_role}' lacks permission to record review decisions. Admin or Owner required."
            )

        prev_state = review.status.value
        prev_hash = review.audit_events[-1].event_hash if review.audit_events else None

        success, err = GovernanceEngine.record_decision(
            review=review,
            policy=effective_policy,
            decision=decision,
            actor_role=effective_role,
        )
        if not success:
            if "Separation of duties" in (err or ""):
                raise PermissionError(err)
            raise ValueError(err or "Failed to record review decision.")

        # Cryptographic audit chaining
        audit_event = AuditTrailManager.create_event(
            review_id=review_id,
            workspace_id=workspace_id,
            actor_id=reviewer_id,
            event_type="RECORD_DECISION",
            previous_state=prev_state,
            new_state=review.status.value,
            artifact_fingerprint=review.artifact_fingerprint,
            policy_version=review.policy_version,
            timestamp=now_iso,
            payload={"decision": decision_type.value, "reason": rationale},
            previous_event_hash=prev_hash,
        )
        review.audit_events.append(audit_event)

        if db_session is not None:
            ws_uuid = uuid.UUID(workspace_id)
            from dera_api.repositories.migration_governance import MigrationGovernanceRepository
            repo = MigrationGovernanceRepository(db_session)
            await repo.save_decision_and_audit(
                workspace_id=ws_uuid,
                review=review,
                decision=decision,
                audit_event=audit_event,
            )

        return review

    async def get_audit_trail(
        self,
        workspace_id: str,
        review_id: str,
        db_session: AsyncSession | None = None,
    ) -> list[AuditEvent]:
        """Retrieve immutable audit events for review."""
        review = await self.get_review(workspace_id, review_id, db_session=db_session)
        if not review:
            raise ValueError(f"Review '{review_id}' not found in workspace.")
        return review.audit_events

    async def export_approved_artifact(
        self,
        workspace_id: str,
        review_id: str,
        user_id: str,
        user_role: str,
        db_session: AsyncSession | None = None,
    ) -> dict[str, Any]:
        """Export approved artifact ensuring fail-closed status and immutable audit record."""
        review = await self.get_review(workspace_id, review_id, db_session=db_session)
        if not review:
            raise ValueError(f"Review '{review_id}' not found in workspace.")

        if review.status != ReviewLifecycleStatus.APPROVED:
            raise PermissionError(
                f"Cannot export artifact for review with status '{review.status.value}'. Must be APPROVED."
            )

        artifact = self.get_sql_artifact(workspace_id, review.artifact_id)
        if not artifact:
            raise ValueError(f"Artifact '{review.artifact_id}' not found in workspace.")

        # Tampering check: fingerprint must match exactly
        if artifact.artifact_fingerprint != review.artifact_fingerprint:
            raise ValueError(
                "Integrity violation: artifact content has changed since governance review approval."
            )

        now = datetime.now(UTC)
        export_id = f"exp_{uuid.uuid4().hex[:12]}"
        prev_hash = review.audit_events[-1].event_hash if review.audit_events else None

        # Record export event in audit trail
        audit_event = AuditTrailManager.create_event(
            review_id=review_id,
            workspace_id=workspace_id,
            actor_id=user_id,
            event_type="EXPORT_ARTIFACT",
            previous_state=review.status.value,
            new_state=review.status.value,
            artifact_fingerprint=artifact.artifact_fingerprint,
            policy_version=review.policy_version,
            timestamp=now.isoformat(),
            payload={"export_id": export_id, "disclaimer": "GENERATED FOR REVIEW — NOT EXECUTED"},
            previous_event_hash=prev_hash,
        )
        review.audit_events.append(audit_event)

        if db_session is not None:
            ws_uuid = uuid.UUID(workspace_id)
            from dera_api.repositories.migration_governance import MigrationGovernanceRepository
            repo = MigrationGovernanceRepository(db_session)
            await repo.save_audit_event(
                workspace_id=ws_uuid,
                review_id=review_id,
                audit_event=audit_event,
                payload={"export_id": export_id, "disclaimer": "GENERATED FOR REVIEW — NOT EXECUTED"},
            )

        # Extract forward and rollback sql
        rollback_sql = "\n\n".join(r.sql for r in artifact.rollback_statements)

        return {
            "export_id": export_id,
            "review_id": review.review_id,
            "artifact_id": artifact.artifact_id,
            "artifact_fingerprint": artifact.artifact_fingerprint,
            "target_dialect": artifact.dialect.value
            if hasattr(artifact.dialect, "value")
            else str(artifact.dialect),
            "forward_sql": artifact.rendered_sql_script,
            "rollback_sql": rollback_sql,
            "exported_at": now,
            "exported_by": user_id,
            "governance_status": "APPROVED",
            "disclaimer": "GENERATED FOR REVIEW — NOT EXECUTED",
        }
