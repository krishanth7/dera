"""DERA Repositories — Migration Governance Repository.

Provides transactional persistence and retrieval for migration reviews,
reviewer decisions, and append-only cryptographic audit event chains.
"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from dera.migration.governance.enums import ReviewDecisionType, ReviewLifecycleStatus
from dera.migration.governance.models import (
    AuditEvent,
    MigrationReviewRequest,
    ReviewDecision,
)
from dera_api.db.models.migration_governance import (
    MigrationAuditEventRecord,
    MigrationReviewDecisionRecord,
    MigrationReviewRecord,
)
from dera_api.repositories.base import BaseRepository


class MigrationGovernanceRepository(BaseRepository[MigrationReviewRecord]):
    """Repository managing durable persistence for migration reviews and audit logs."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, MigrationReviewRecord)

    async def get_by_review_id(
        self,
        workspace_id: uuid.UUID,
        review_id_str: str,
    ) -> MigrationReviewRecord | None:
        """Fetch review record scoped to workspace with eager-loaded decisions and audit events."""
        stmt = (
            select(MigrationReviewRecord)
            .where(
                MigrationReviewRecord.workspace_id == workspace_id,
                MigrationReviewRecord.review_id_str == review_id_str,
            )
            .options(
                selectinload(MigrationReviewRecord.decisions),
                selectinload(MigrationReviewRecord.audit_events),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def save_review(
        self,
        workspace_id: uuid.UUID,
        review: MigrationReviewRequest,
        title: str,
        description: str,
        required_approvals: int,
    ) -> MigrationReviewRecord:
        """Create or update a durable review record along with its initial audit events."""
        is_new = False
        record = await self.get_by_review_id(workspace_id, review.review_id)
        if not record:
            is_new = True
            record = MigrationReviewRecord(
                workspace_id=workspace_id,
                review_id_str=review.review_id,
                artifact_id=review.artifact_id,
                artifact_fingerprint=review.artifact_fingerprint,
                migration_plan_fingerprint=review.migration_plan_fingerprint,
                risk_report_fingerprint=review.risk_report_fingerprint,
                target_dialect=review.target_dialect,
                requester_id=review.requester_id,
                title=title,
                description=description,
                status=review.status.value,
                policy_version=review.policy_version,
                required_approvals=required_approvals,
            )
            self.session.add(record)
            await self.session.flush()

        # Sync audit events that are not yet persisted
        existing_event_ids = set() if is_new else {e.event_id_str for e in record.audit_events}
        for ev in review.audit_events:
            if ev.event_id not in existing_event_ids:
                event_record = MigrationAuditEventRecord(
                    review_record_id=record.id,
                    event_id_str=ev.event_id,
                    workspace_id=workspace_id,
                    actor_id=ev.actor_id,
                    event_type=ev.event_type,
                    previous_state=ev.previous_state,
                    new_state=ev.new_state,
                    artifact_fingerprint=ev.artifact_fingerprint,
                    policy_version=ev.policy_version,
                    payload_json={"event_digest": ev.event_payload_digest},
                    previous_event_hash=ev.previous_event_hash,
                    event_hash=ev.event_hash,
                )
                self.session.add(event_record)

        await self.session.flush()
        return record

    async def save_decision_and_audit(
        self,
        workspace_id: uuid.UUID,
        review: MigrationReviewRequest,
        decision: ReviewDecision,
        audit_event: AuditEvent,
    ) -> MigrationReviewRecord:
        """Persist a reviewer decision, updated review status, and new audit event atomically."""
        record = await self.get_by_review_id(workspace_id, review.review_id)
        if not record:
            raise ValueError(f"Review '{review.review_id}' does not exist in workspace.")

        record.status = review.status.value

        decision_record = MigrationReviewDecisionRecord(
            review_record_id=record.id,
            decision_id_str=decision.decision_id,
            reviewer_id=decision.reviewer_id,
            reviewer_role=decision.reviewer_role,
            decision_type=decision.decision_type.value,
            artifact_fingerprint=decision.artifact_fingerprint,
            rationale=decision.reason,
        )
        self.session.add(decision_record)

        event_record = MigrationAuditEventRecord(
            review_record_id=record.id,
            event_id_str=audit_event.event_id,
            workspace_id=workspace_id,
            actor_id=audit_event.actor_id,
            event_type=audit_event.event_type,
            previous_state=audit_event.previous_state,
            new_state=audit_event.new_state,
            artifact_fingerprint=audit_event.artifact_fingerprint,
            policy_version=audit_event.policy_version,
            payload_json={"decision": decision.decision_type.value, "reason": decision.reason},
            previous_event_hash=audit_event.previous_event_hash,
            event_hash=audit_event.event_hash,
        )
        self.session.add(event_record)

        await self.session.flush()
        return record

    async def save_audit_event(
        self,
        workspace_id: uuid.UUID,
        review_id: str,
        audit_event: AuditEvent,
        payload: dict[str, Any] | None = None,
    ) -> None:
        """Append an audit event to the review's audit trail."""
        record = await self.get_by_review_id(workspace_id, review_id)
        if not record:
            raise ValueError(f"Review '{review_id}' does not exist in workspace.")

        event_record = MigrationAuditEventRecord(
            review_record_id=record.id,
            event_id_str=audit_event.event_id,
            workspace_id=workspace_id,
            actor_id=audit_event.actor_id,
            event_type=audit_event.event_type,
            previous_state=audit_event.previous_state,
            new_state=audit_event.new_state,
            artifact_fingerprint=audit_event.artifact_fingerprint,
            policy_version=audit_event.policy_version,
            payload_json=payload or {},
            previous_event_hash=audit_event.previous_event_hash,
            event_hash=audit_event.event_hash,
        )
        self.session.add(event_record)
        await self.session.flush()

    def to_domain_model(self, record: MigrationReviewRecord) -> MigrationReviewRequest:
        """Convert a database record to the domain model."""
        decisions: list[ReviewDecision] = []
        for d in record.decisions:
            decisions.append(
                ReviewDecision(
                    decision_id=d.decision_id_str,
                    review_id=record.review_id_str,
                    reviewer_id=d.reviewer_id,
                    reviewer_role=d.reviewer_role,
                    decision_type=ReviewDecisionType(d.decision_type),
                    artifact_fingerprint=d.artifact_fingerprint,
                    policy_version=record.policy_version,
                    reason=d.rationale,
                    timestamp=d.created_at.isoformat(),
                )
            )

        audit_events: list[AuditEvent] = []
        for ev in record.audit_events:
            audit_events.append(
                AuditEvent(
                    event_id=ev.event_id_str,
                    review_id=record.review_id_str,
                    workspace_id=str(record.workspace_id),
                    actor_id=ev.actor_id,
                    event_type=ev.event_type,
                    previous_state=ev.previous_state,
                    new_state=ev.new_state,
                    artifact_fingerprint=ev.artifact_fingerprint,
                    policy_version=ev.policy_version,
                    timestamp=ev.created_at.isoformat(),
                    event_payload_digest=ev.payload_json.get("event_digest", ""),
                    previous_event_hash=ev.previous_event_hash or "",
                    event_hash=ev.event_hash,
                )
            )

        return MigrationReviewRequest(
            review_id=record.review_id_str,
            workspace_id=str(record.workspace_id),
            artifact_id=record.artifact_id,
            artifact_fingerprint=record.artifact_fingerprint,
            migration_plan_fingerprint=record.migration_plan_fingerprint,
            risk_report_fingerprint=record.risk_report_fingerprint,
            target_dialect=record.target_dialect,
            requester_id=record.requester_id,
            policy_version=record.policy_version,
            status=ReviewLifecycleStatus(record.status),
            created_at=record.created_at.isoformat(),
            decisions=decisions,
            audit_events=audit_events,
        )
