"""DERA Workers — Background Job Execution Tasks.

Provides deterministic task execution routines, worker claiming, timeout enforcement,
and audit trail recording.
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
import logging
import socket
from typing import TYPE_CHECKING, Any
import uuid

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from dera_api.core.config import get_settings
from dera_api.db.engine import create_database_engine
from dera_api.db.session import create_session_factory, transaction_scope
from dera_api.jobs.enums import JobStatus
from dera_api.jobs.exceptions import JobError
from dera_api.jobs.registry import default_task_registry
from dera_api.jobs.retry import calculate_backoff, is_retryable_error
from dera_api.jobs.schemas import JobExecutionContext
from dera_api.workers.celery_app import celery_app

if TYPE_CHECKING:
    from dera_api.repositories.audit import AuditRepository
    from dera_api.repositories.jobs import JobRepository

logger = logging.getLogger(__name__)

# Cached worker engine & sessionmaker for standalone worker execution
_worker_session_factory: async_sessionmaker[AsyncSession] | None = None


def get_worker_session_factory() -> async_sessionmaker[AsyncSession]:
    """Obtain or lazily instantiate the worker async database session factory."""
    global _worker_session_factory
    if _worker_session_factory is None:
        settings = get_settings()
        engine = create_database_engine(settings)
        _worker_session_factory = create_session_factory(engine)
    return _worker_session_factory


def get_worker_id() -> str:
    """Generate a stable worker process identifier."""
    hostname = socket.gethostname()
    return f"worker@{hostname}"


async def execute_job_async(
    job_id: uuid.UUID,
    workspace_id: uuid.UUID,
    worker_id: str | None = None,
    correlation_id: str | None = None,
    session_factory: async_sessionmaker[AsyncSession] | None = None,
) -> dict[str, Any]:
    """Execute a single background job attempt asynchronously.

    Claims the job atomically, verifies tenant boundaries, checks for cooperative
    cancellation, invokes the allowlisted task handler, and persists the resulting
    state with transactional integrity.
    """
    worker_identity = worker_id or get_worker_id()
    factory = session_factory or get_worker_session_factory()
    settings = get_settings()

    from dera_api.repositories.audit import AuditRepository
    from dera_api.repositories.jobs import JobRepository

    async with factory() as session, transaction_scope(session):
        job_repo = JobRepository(session)
        audit_repo = AuditRepository(session)

        # 1. Atomic claim check
        job = await job_repo.claim_job(job_id=job_id, worker_id=worker_identity)
        if job is None:
            # Check if job exists and why it couldn't be claimed
            existing = await job_repo.get_by_id_global(job_id)
            if existing is None:
                logger.warning("Job %s not found during worker claim attempt.", job_id)
                return {"status": "not_found", "job_id": str(job_id)}
            logger.info(
                "Job %s could not be claimed (current status: %s). Exiting claim.",
                job_id,
                existing.status,
            )
            return {"status": "claim_failed", "current_status": existing.status}

        # 2. Strict tenant boundary assertion
        if job.workspace_id != workspace_id:
            logger.error(
                "Tenant boundary mismatch! Job %s belongs to workspace %s, not %s.",
                job_id,
                job.workspace_id,
                workspace_id,
            )
            await job_repo.mark_failed(
                job_id=job_id,
                error_code="JOB_TENANT_MISMATCH",
                error_message="Job tenant boundary assertion failed.",
            )
            return {"status": "tenant_mismatch", "job_id": str(job_id)}

        # 3. Check for cancellation request during queuing
        if job.status == JobStatus.CANCEL_REQUESTED.value:
            logger.info("Job %s was cancelled before execution started.", job_id)
            await job_repo.mark_failed(
                job_id=job_id,
                error_code="JOB_CANCELLED",
                error_message="Job cancelled by user before execution.",
            )
            return {"status": "cancelled", "job_id": str(job_id)}

        # 4. Allowlisted task resolution
        if not default_task_registry.is_registered(job.job_type):
            logger.error("Job %s requested unallowlisted task '%s'.", job_id, job.job_type)
            await job_repo.mark_failed(
                job_id=job_id,
                error_code="JOB_TYPE_UNSUPPORTED",
                error_message=f"Task type '{job.job_type}' is not registered in the task allowlist.",
            )
            return {"status": "unsupported_task", "job_type": job.job_type}

        task_def = default_task_registry.get(job.job_type)

        # 5. Build strongly-typed execution context
        ctx = JobExecutionContext(
            job_id=job.id,
            workspace_id=job.workspace_id,
            job_type=job.job_type,
            attempt_number=job.attempt_count,
            timeout_seconds=job.timeout_seconds,
            worker_id=worker_identity,
            correlation_id=correlation_id,
        )

        # 6. Execute task with timeout protection
        try:
            validated_payload = task_def.validate_payload(job.payload)

            # Enforce execution timeout
            result = await asyncio.wait_for(
                asyncio.to_thread(task_def.handler, ctx, validated_payload),
                timeout=float(job.timeout_seconds),
            )

            # Check if job was cancelled while the task was running
            reloaded = await job_repo.get_by_id_global(job_id)
            if reloaded and reloaded.status == JobStatus.CANCEL_REQUESTED.value:
                logger.info("Job %s completed but was marked CANCEL_REQUESTED.", job_id)
                await job_repo.mark_succeeded(job_id, result)
            else:
                await job_repo.mark_succeeded(job_id, result)

            # Record security audit event
            await audit_repo.record_event(
                event_type="job:completed",
                actor_user_id=job.created_by_user_id,
                workspace_id=job.workspace_id,
                target_type="job",
                target_id=str(job.id),
                request_id=correlation_id,
                metadata={
                    "job_type": job.job_type,
                    "attempt_count": job.attempt_count,
                    "worker_id": worker_identity,
                },
            )

            return {"status": "succeeded", "job_id": str(job_id), "result": result}

        except TimeoutError as exc:
            logger.warning("Job %s timed out after %d seconds.", job_id, job.timeout_seconds)
            await _handle_failure(
                job_repo=job_repo,
                audit_repo=audit_repo,
                job=job,
                error_code="JOB_TIMEOUT",
                error_message=f"Job exceeded execution timeout of {job.timeout_seconds}s.",
                exc=exc,
                settings=settings,
                correlation_id=correlation_id,
                worker_id=worker_identity,
            )
            return {"status": "timeout", "job_id": str(job_id)}

        except Exception as exc:
            error_code = getattr(exc, "error_code", "JOB_EXECUTION_FAILED")
            error_message = str(exc) or "Unexpected task execution error."
            logger.exception("Job %s failed with exception: %s", job_id, error_message)

            await _handle_failure(
                job_repo=job_repo,
                audit_repo=audit_repo,
                job=job,
                error_code=error_code,
                error_message=error_message,
                exc=exc,
                settings=settings,
                correlation_id=correlation_id,
                worker_id=worker_identity,
            )
            return {"status": "failed", "job_id": str(job_id), "error": error_message}


async def _handle_failure(
    job_repo: JobRepository,
    audit_repo: AuditRepository,
    job: Any,
    error_code: str,
    error_message: str,
    exc: Exception,
    settings: Any,
    correlation_id: str | None,
    worker_id: str,
) -> None:
    """Classify failure, compute exponential backoff, and update job status."""
    retryable = is_retryable_error(exc)
    has_attempts_left = job.attempt_count < job.max_attempts

    if retryable and has_attempts_left:
        # Schedule retry with bounded exponential backoff
        delay = calculate_backoff(
            attempt=job.attempt_count,
            base_delay=settings.job_default_retry_delay_seconds,
            max_delay=settings.job_max_retry_delay_seconds,
            jitter=True,
        )
        next_retry_at = datetime.now(UTC) + timedelta(seconds=delay)
        await job_repo.mark_failed(
            job_id=job.id,
            error_code=error_code,
            error_message=error_message,
            next_retry_at=next_retry_at,
        )

        await audit_repo.record_event(
            event_type="job:retry_scheduled",
            actor_user_id=job.created_by_user_id,
            workspace_id=job.workspace_id,
            target_type="job",
            target_id=str(job.id),
            request_id=correlation_id,
            metadata={
                "error_code": error_code,
                "attempt_count": job.attempt_count,
                "max_attempts": job.max_attempts,
                "next_retry_at": next_retry_at.isoformat(),
                "delay_seconds": delay,
            },
        )
    else:
        # Terminal failure
        await job_repo.mark_failed(
            job_id=job.id,
            error_code=error_code,
            error_message=error_message,
            next_retry_at=None,
        )

        await audit_repo.record_event(
            event_type="job:failed",
            actor_user_id=job.created_by_user_id,
            workspace_id=job.workspace_id,
            target_type="job",
            target_id=str(job.id),
            request_id=correlation_id,
            metadata={
                "error_code": error_code,
                "attempt_count": job.attempt_count,
                "max_attempts": job.max_attempts,
                "terminal": True,
            },
        )


@celery_app.task(
    name="dera_api.workers.tasks.execute_job_task",
    bind=True,
    max_retries=0,
)
def execute_job_task(
    self: Any,
    job_id_str: str,
    workspace_id_str: str,
    correlation_id: str | None = None,
) -> dict[str, Any]:
    """Celery worker entrypoint for background jobs.

    Translates stringified UUID parameters and delegates to execute_job_async.
    """
    job_id = uuid.UUID(job_id_str)
    workspace_id = uuid.UUID(workspace_id_str)

    try:
        return asyncio.run(
            execute_job_async(
                job_id=job_id,
                workspace_id=workspace_id,
                worker_id=f"celery@{self.request.hostname or 'unknown'}",
                correlation_id=correlation_id,
            )
        )
    except Exception as exc:
        logger.exception("Uncaught exception in Celery task wrapper: %s", exc)
        raise
