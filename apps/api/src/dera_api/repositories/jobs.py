"""DERA Repositories — Job and Outbox Repositories.

Provides strongly-typed, tenant-isolated async database operations for Job persistence,
atomic compare-and-swap (CAS) state transitions, and transactional outbox event management.
"""

import uuid
from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from dera_api.db.models.jobs import Job, JobOutboxEvent
from dera_api.jobs.enums import JobPriority, JobStatus, OutboxEventStatus, OutboxEventType
from dera_api.repositories.base import BaseRepository


class JobRepository(BaseRepository[Job]):
    """Authoritative repository for background job persistence."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Job)

    async def create_job(
        self,
        workspace_id: uuid.UUID,
        job_type: str,
        payload: dict[str, Any],
        priority: JobPriority | str = JobPriority.NORMAL,
        max_attempts: int = 3,
        timeout_seconds: int = 300,
        idempotency_key: str | None = None,
        created_by_user_id: uuid.UUID | None = None,
    ) -> Job:
        """Create a new job record with initial PENDING status within tenant workspace."""
        now = datetime.now(UTC)
        job = Job(
            id=uuid.uuid4(),
            workspace_id=workspace_id,
            created_by_user_id=created_by_user_id,
            job_type=job_type,
            status=JobStatus.PENDING.value,
            priority=priority.value if isinstance(priority, JobPriority) else priority,
            payload=payload,
            result=None,
            error_code=None,
            error_message=None,
            attempt_count=0,
            max_attempts=max_attempts,
            idempotency_key=idempotency_key,
            timeout_seconds=timeout_seconds,
            worker_id=None,
            created_at=now,
            queued_at=None,
            started_at=None,
            finished_at=None,
            next_retry_at=None,
        )
        self.session.add(job)
        await self.session.flush()
        return job

    async def get_by_id(
        self,
        workspace_id: uuid.UUID,
        job_id: uuid.UUID,
    ) -> Job | None:
        """Retrieve a job by UUID enforcing workspace boundary isolation."""
        stmt = select(Job).where(
            Job.id == job_id,
            Job.workspace_id == workspace_id,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id_global(self, job_id: uuid.UUID) -> Job | None:
        """Retrieve a job by UUID across workspaces for trusted internal worker dispatch."""
        stmt = select(Job).where(Job.id == job_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_idempotency_key(
        self,
        workspace_id: uuid.UUID,
        idempotency_key: str,
    ) -> Job | None:
        """Retrieve an existing job by client idempotency key scoped to workspace."""
        stmt = select(Job).where(
            Job.workspace_id == workspace_id,
            Job.idempotency_key == idempotency_key,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_jobs(
        self,
        workspace_id: uuid.UUID,
        status: JobStatus | str | None = None,
        job_type: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[Sequence[Job], int]:
        """List jobs in a workspace with optional status/type filtering and pagination."""
        base_query = select(Job).where(Job.workspace_id == workspace_id)
        count_query = select(func.count()).select_from(Job).where(Job.workspace_id == workspace_id)

        if status is not None:
            status_val = status.value if isinstance(status, JobStatus) else status
            base_query = base_query.where(Job.status == status_val)
            count_query = count_query.where(Job.status == status_val)

        if job_type is not None:
            base_query = base_query.where(Job.job_type == job_type)
            count_query = count_query.where(Job.job_type == job_type)

        total_res = await self.session.execute(count_query)
        total = total_res.scalar_one() or 0

        paged_query = base_query.order_by(Job.created_at.desc()).limit(limit).offset(offset)
        items_res = await self.session.execute(paged_query)
        items = items_res.scalars().all()

        return items, total

    async def claim_job(
        self,
        job_id: uuid.UUID,
        worker_id: str,
    ) -> Job | None:
        """Atomic Compare-And-Swap claiming a job from QUEUED/RETRY_SCHEDULED to RUNNING.

        Increments attempt_count and records worker_id and started_at.
        """
        now = datetime.now(UTC)
        stmt = (
            update(Job)
            .where(
                Job.id == job_id,
                Job.status.in_([JobStatus.QUEUED.value, JobStatus.RETRY_SCHEDULED.value]),
            )
            .values(
                status=JobStatus.RUNNING.value,
                worker_id=worker_id,
                started_at=now,
                attempt_count=Job.attempt_count + 1,
            )
            .returning(Job)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def mark_queued(self, job_id: uuid.UUID) -> bool:
        """Transition a job from PENDING or RETRY_SCHEDULED to QUEUED."""
        now = datetime.now(UTC)
        stmt = (
            update(Job)
            .where(
                Job.id == job_id,
                Job.status.in_([JobStatus.PENDING.value, JobStatus.RETRY_SCHEDULED.value]),
            )
            .values(
                status=JobStatus.QUEUED.value,
                queued_at=now,
            )
        )
        result = await self.session.execute(stmt)
        return bool(result.rowcount and result.rowcount > 0)

    async def mark_succeeded(
        self,
        job_id: uuid.UUID,
        result: dict[str, Any],
    ) -> bool:
        """Transition a job from RUNNING or CANCEL_REQUESTED to SUCCEEDED."""
        now = datetime.now(UTC)
        stmt = (
            update(Job)
            .where(
                Job.id == job_id,
                Job.status.in_([JobStatus.RUNNING.value, JobStatus.CANCEL_REQUESTED.value]),
            )
            .values(
                status=JobStatus.SUCCEEDED.value,
                result=result,
                finished_at=now,
            )
        )
        res = await self.session.execute(stmt)
        return bool(res.rowcount and res.rowcount > 0)

    async def mark_failed(
        self,
        job_id: uuid.UUID,
        error_code: str,
        error_message: str,
        next_retry_at: datetime | None = None,
    ) -> bool:
        """Record execution failure.

        If next_retry_at is provided, transitions to RETRY_SCHEDULED.
        Otherwise, transitions to terminal FAILED state.
        """
        now = datetime.now(UTC)
        target_status = (
            JobStatus.RETRY_SCHEDULED.value if next_retry_at is not None else JobStatus.FAILED.value
        )
        stmt = (
            update(Job)
            .where(
                Job.id == job_id,
                Job.status.in_([JobStatus.RUNNING.value, JobStatus.CANCEL_REQUESTED.value]),
            )
            .values(
                status=target_status,
                error_code=error_code,
                error_message=error_message[:2048],
                finished_at=now if next_retry_at is None else None,
                next_retry_at=next_retry_at,
            )
        )
        res = await self.session.execute(stmt)
        return bool(res.rowcount and res.rowcount > 0)

    async def request_cancellation(
        self,
        workspace_id: uuid.UUID,
        job_id: uuid.UUID,
    ) -> tuple[JobStatus, bool]:
        """Request cooperative or immediate cancellation of a job.

        If PENDING, QUEUED, or RETRY_SCHEDULED: immediately transitions to CANCELLED.
        If RUNNING: transitions to CANCEL_REQUESTED.
        Returns (new_status, success).
        """
        now = datetime.now(UTC)

        # 1. Try immediate cancellation for inactive/queued states
        stmt_imm = (
            update(Job)
            .where(
                Job.id == job_id,
                Job.workspace_id == workspace_id,
                Job.status.in_(
                    [
                        JobStatus.PENDING.value,
                        JobStatus.QUEUED.value,
                        JobStatus.RETRY_SCHEDULED.value,
                    ]
                ),
            )
            .values(
                status=JobStatus.CANCELLED.value,
                finished_at=now,
            )
        )
        res_imm = await self.session.execute(stmt_imm)
        if res_imm.rowcount and res_imm.rowcount > 0:
            return JobStatus.CANCELLED, True

        # 2. Try cooperative cancellation if running
        stmt_run = (
            update(Job)
            .where(
                Job.id == job_id,
                Job.workspace_id == workspace_id,
                Job.status == JobStatus.RUNNING.value,
            )
            .values(
                status=JobStatus.CANCEL_REQUESTED.value,
            )
        )
        res_run = await self.session.execute(stmt_run)
        if res_run.rowcount and res_run.rowcount > 0:
            return JobStatus.CANCEL_REQUESTED, True

        # Could not transition (likely already terminal)
        job = await self.get_by_id(workspace_id, job_id)
        current = JobStatus(job.status) if job else JobStatus.FAILED
        return current, False


class JobOutboxRepository(BaseRepository[JobOutboxEvent]):
    """Repository managing transactional outbox events for background jobs."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, JobOutboxEvent)

    async def create_event(
        self,
        job_id: uuid.UUID,
        workspace_id: uuid.UUID,
        event_type: str = OutboxEventType.JOB_QUEUED.value,
    ) -> JobOutboxEvent:
        """Create a pending outbox event for a job within the transaction scope."""
        event = JobOutboxEvent(
            id=uuid.uuid4(),
            job_id=job_id,
            workspace_id=workspace_id,
            event_type=event_type,
            status=OutboxEventStatus.PENDING.value,
            retry_count=0,
            created_at=datetime.now(UTC),
            dispatched_at=None,
        )
        self.session.add(event)
        await self.session.flush()
        return event

    async def get_pending_events(
        self,
        limit: int = 50,
    ) -> Sequence[JobOutboxEvent]:
        """Fetch pending outbox events ordered by creation timestamp."""
        stmt = (
            select(JobOutboxEvent)
            .where(JobOutboxEvent.status == OutboxEventStatus.PENDING.value)
            .order_by(JobOutboxEvent.created_at.asc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def mark_dispatched(self, event_id: uuid.UUID) -> bool:
        """Mark an outbox event as dispatched to the broker."""
        now = datetime.now(UTC)
        stmt = (
            update(JobOutboxEvent)
            .where(JobOutboxEvent.id == event_id)
            .values(
                status=OutboxEventStatus.DISPATCHED.value,
                dispatched_at=now,
            )
        )
        res = await self.session.execute(stmt)
        return bool(res.rowcount and res.rowcount > 0)

    async def record_dispatch_failure(self, event_id: uuid.UUID) -> bool:
        """Increment dispatch retry count upon broker failure."""
        stmt = (
            update(JobOutboxEvent)
            .where(JobOutboxEvent.id == event_id)
            .values(retry_count=JobOutboxEvent.retry_count + 1)
        )
        res = await self.session.execute(stmt)
        return bool(res.rowcount and res.rowcount > 0)
