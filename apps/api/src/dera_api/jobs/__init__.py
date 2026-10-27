"""DERA Jobs Subsystem.

Provides durable background job orchestration, transactional outbox dispatching,
allowlisted task execution, and cooperative cancellation for DERA.
"""

from dera_api.jobs.dispatcher import JobOutboxDispatcher
from dera_api.jobs.enums import JobPriority, JobStatus, OutboxEventStatus, OutboxEventType
from dera_api.jobs.exceptions import (
    IdempotencyConflictError,
    JobAlreadyCompletedError,
    JobCancellationConflictError,
    JobError,
    JobExecutionError,
    JobNotFoundError,
    JobPayloadInvalidError,
    JobQueueUnavailableError,
    JobRetryNotAllowedError,
    JobTimeoutError,
    JobTypeUnsupportedError,
)
from dera_api.jobs.lifecycle import ALLOWED_TRANSITIONS, can_transition, validate_transition
from dera_api.jobs.registry import TaskDefinition, TaskRegistry, default_task_registry
from dera_api.jobs.retry import calculate_backoff, calculate_next_retry_at, is_retryable_error
from dera_api.jobs.schemas import (
    JobCancelResponse,
    JobCreateRequest,
    JobExecutionContext,
    JobExecutionResult,
    JobListResponse,
    JobResponse,
)
from dera_api.jobs.service import JobService

__all__ = [
    "ALLOWED_TRANSITIONS",
    "IdempotencyConflictError",
    "JobAlreadyCompletedError",
    "JobCancelResponse",
    "JobCancellationConflictError",
    "JobCreateRequest",
    "JobError",
    "JobExecutionContext",
    "JobExecutionError",
    "JobExecutionResult",
    "JobListResponse",
    "JobNotFoundError",
    "JobOutboxDispatcher",
    "JobPayloadInvalidError",
    "JobPriority",
    "JobQueueUnavailableError",
    "JobResponse",
    "JobRetryNotAllowedError",
    "JobService",
    "JobStatus",
    "JobTimeoutError",
    "JobTypeUnsupportedError",
    "OutboxEventStatus",
    "OutboxEventType",
    "TaskDefinition",
    "TaskRegistry",
    "calculate_backoff",
    "calculate_next_retry_at",
    "can_transition",
    "default_task_registry",
    "is_retryable_error",
    "validate_transition",
]
