"""DERA Jobs — Domain Enumerations.

Defines authoritative enum types for job status lifecycle states, scheduling priorities,
and transactional outbox event lifecycle tracking.
"""

from enum import StrEnum


class JobStatus(StrEnum):
    """Authoritative lifecycle states for background jobs."""

    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    RETRY_SCHEDULED = "retry_scheduled"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCEL_REQUESTED = "cancel_requested"
    CANCELLED = "cancelled"

    @property
    def is_terminal(self) -> bool:
        """Return True if this state is permanently immutable."""
        return self in {JobStatus.SUCCEEDED, JobStatus.FAILED, JobStatus.CANCELLED}

    @property
    def is_active(self) -> bool:
        """Return True if this job is currently in progress or awaiting worker execution."""
        return self in {
            JobStatus.PENDING,
            JobStatus.QUEUED,
            JobStatus.RUNNING,
            JobStatus.RETRY_SCHEDULED,
            JobStatus.CANCEL_REQUESTED,
        }


class JobPriority(StrEnum):
    """Job scheduling priority tiers."""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class OutboxEventStatus(StrEnum):
    """Dispatch status for transactional outbox records."""

    PENDING = "pending"
    DISPATCHED = "dispatched"
    FAILED = "failed"


class OutboxEventType(StrEnum):
    """Categorized event types dispatched through the outbox."""

    JOB_QUEUED = "job.queued"
    JOB_CANCELLED = "job.cancelled"
