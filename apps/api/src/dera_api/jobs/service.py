"""DERA Jobs — Application Service Layer.

Coordinates background job submission, validation, idempotency resolution,
cooperative cancellation, and status querying within strict tenant boundaries.
"""

from __future__ import annotations

from collections.abc import Sequence
import logging
from typing import TYPE_CHECKING
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from dera_api.core.config import get_settings
from dera_api.db.models.jobs import Job
from dera_api.jobs.dispatcher import JobOutboxDispatcher
from dera_api.jobs.enums import JobPriority, JobStatus
from dera_api.jobs.exceptions import (
    IdempotencyConflictError,
    JobAlreadyCompletedError,
    JobNotFoundError,
    JobTypeUnsupportedError,
)
from dera_api.jobs.registry import default_task_registry
from dera_api.jobs.schemas import JobCreateRequest

if TYPE_CHECKING:
    from dera_api.repositories.audit import AuditRepository
    from dera_api.repositories.jobs import JobOutboxRepository, JobRepository

logger = logging.getLogger(__name__)


class JobService:
    """Service orchestrating background job lifecycle and state transitions."""

    def __init__(self, session: AsyncSession) -> None:
        from dera_api.repositories.audit import AuditRepository
        from dera_api.repositories.jobs import JobOutboxRepository, JobRepository

        self.session = session
        self.job_repo = JobRepository(session)
        self.outbox_repo = JobOutboxRepository(session)
        self.audit_repo = AuditRepository(session)
        self.dispatcher = JobOutboxDispatcher(session)
        self.settings = get_settings()

    async def submit_job(
        self,
        workspace_id: uuid.UUID,
        request: JobCreateRequest,
        user_id: uuid.UUID | None = None,
        request_id: str | None = None,
        client_ip: str | None = None,
    ) -> Job:
        """Submit a background job within a tenant workspace.

        Validates task allowlisting, checks client idempotency, persists durable
        job and outbox records in the current transaction, and dispatches the task.
        """
        # 1. Allowlist verification
        if not default_task_registry.is_registered(request.job_type):
            raise JobTypeUnsupportedError(request.job_type)

        task_def = default_task_registry.get(request.job_type)

        # 2. Typed payload validation
        validated_payload = task_def.validate_payload(request.payload)

        # 3. Idempotency token evaluation
        if request.idempotency_key:
            existing = await self.job_repo.get_by_idempotency_key(
                workspace_id=workspace_id,
                idempotency_key=request.idempotency_key,
            )
            if existing is not None:
                # Compare payloads to detect conflicting submissions
                if existing.payload == validated_payload and existing.job_type == request.job_type:
                    logger.info(
                        "Returning existing job %s for idempotency key '%s'.",
                        existing.id,
                        request.idempotency_key,
                    )
                    return existing
                raise IdempotencyConflictError(request.idempotency_key)

        # 4. Resolve timeout and parameters
        timeout = request.timeout_seconds or self.settings.job_default_timeout_seconds
        priority = request.priority or JobPriority.NORMAL

        # 5. Persist durable Job entity
        job = await self.job_repo.create_job(
            workspace_id=workspace_id,
            job_type=request.job_type,
            payload=validated_payload,
            priority=priority,
            max_attempts=self.settings.job_max_attempts,
            timeout_seconds=timeout,
            idempotency_key=request.idempotency_key,
            created_by_user_id=user_id,
        )

        # 6. Persist transactional outbox event
        outbox_event = await self.outbox_repo.create_event(
            job_id=job.id,
            workspace_id=workspace_id,
        )

        # 7. Record security audit event
        await self.audit_repo.record_event(
            event_type="job:submitted",
            actor_user_id=user_id,
            workspace_id=workspace_id,
            target_type="job",
            target_id=str(job.id),
            request_id=request_id,
            ip_address=client_ip,
            metadata={
                "job_type": job.job_type,
                "priority": job.priority,
                "timeout_seconds": job.timeout_seconds,
                "idempotency_key": job.idempotency_key,
            },
        )

        # 8. Attempt immediate dispatch from outbox
        await self.dispatcher.dispatch_single(
            event_id=outbox_event.id,
            job_id=job.id,
            workspace_id=workspace_id,
        )

        return job

    async def get_job(
        self,
        workspace_id: uuid.UUID,
        job_id: uuid.UUID,
    ) -> Job:
        """Retrieve a specific job enforcing workspace tenant isolation."""
        job = await self.job_repo.get_by_id(workspace_id=workspace_id, job_id=job_id)
        if job is None:
            raise JobNotFoundError(f"Job '{job_id}' not found in workspace.")
        return job

    async def list_jobs(
        self,
        workspace_id: uuid.UUID,
        status: JobStatus | None = None,
        job_type: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[Sequence[Job], int]:
        """List jobs in a workspace with optional status/type filtering and pagination."""
        return await self.job_repo.list_jobs(
            workspace_id=workspace_id,
            status=status,
            job_type=job_type,
            limit=limit,
            offset=offset,
        )

    async def cancel_job(
        self,
        workspace_id: uuid.UUID,
        job_id: uuid.UUID,
        user_id: uuid.UUID | None = None,
        request_id: str | None = None,
        client_ip: str | None = None,
    ) -> tuple[Job, str]:
        """Request cooperative or immediate cancellation of a job.

        Returns the refreshed job and a descriptive status message.
        """
        job = await self.get_job(workspace_id=workspace_id, job_id=job_id)

        if job.is_terminal():
            raise JobAlreadyCompletedError(job.status)

        new_status, success = await self.job_repo.request_cancellation(
            workspace_id=workspace_id,
            job_id=job_id,
        )

        if not success and new_status.is_terminal:
            raise JobAlreadyCompletedError(new_status.value)

        # Record security audit event
        await self.audit_repo.record_event(
            event_type="job:cancelled",
            actor_user_id=user_id,
            workspace_id=workspace_id,
            target_type="job",
            target_id=str(job.id),
            request_id=request_id,
            ip_address=client_ip,
            metadata={
                "previous_status": job.status,
                "new_status": new_status.value,
            },
        )

        # Refresh job instance
        refreshed = await self.get_job(workspace_id=workspace_id, job_id=job_id)
        if new_status == JobStatus.CANCELLED:
            message = "Job cancelled successfully."
        else:
            message = "Cancellation requested. Worker will abort task cooperatively."

        return refreshed, message
