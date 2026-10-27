"""DERA Jobs — Domain Exceptions.

Defines domain-specific exceptions for job orchestration, lifecycle validation,
task registry allowlists, and idempotency conflicts. Emits RFC 9457-compatible details.
"""

from fastapi import status

from dera_api.contracts.errors import ErrorCode
from dera_api.core.exceptions import DeraError


class JobError(DeraError):
    """Base exception for all DERA background job errors."""

    def __init__(
        self,
        message: str,
        code: str | ErrorCode = ErrorCode.INTERNAL_ERROR,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        error_code: str | None = None,
    ) -> None:
        resolved_code = error_code or code
        super().__init__(
            message=message,
            code=resolved_code,
            status_code=status_code,
            detail=message,
        )
        self.error_code = str(resolved_code)


class JobNotFoundError(JobError):
    """Raised when a requested job does not exist within the workspace boundary."""

    def __init__(self, message: str = "Job not found in workspace.") -> None:
        super().__init__(
            message=message,
            code=ErrorCode.JOB_NOT_FOUND,
            status_code=status.HTTP_404_NOT_FOUND,
        )


class JobTypeUnsupportedError(JobError):
    """Raised when a task type is not allowlisted in the task registry."""

    def __init__(self, job_type: str) -> None:
        super().__init__(
            message=f"Unsupported or unallowlisted task type: '{job_type}'.",
            code=ErrorCode.JOB_TYPE_UNSUPPORTED,
            status_code=status.HTTP_400_BAD_REQUEST,
        )
        self.job_type = job_type


class JobPayloadInvalidError(JobError):
    """Raised when a job input payload violates typed schema contracts."""

    def __init__(self, detail: str) -> None:
        super().__init__(
            message=f"Job payload validation failed: {detail}",
            code=ErrorCode.JOB_PAYLOAD_INVALID,
            status_code=status.HTTP_400_BAD_REQUEST,
        )
        self.detail = detail


class JobAlreadyCompletedError(JobError):
    """Raised when an operation attempts to mutate a terminal job."""

    def __init__(self, current_status: str) -> None:
        super().__init__(
            message=f"Job is already in terminal state '{current_status}' and cannot be altered.",
            code=ErrorCode.JOB_ALREADY_COMPLETED,
            status_code=status.HTTP_409_CONFLICT,
        )
        self.current_status = current_status


class JobCancellationConflictError(JobError):
    """Raised when a cancellation request conflicts with current job state."""

    def __init__(self, current_status: str) -> None:
        super().__init__(
            message=f"Job cannot be cancelled from state '{current_status}'.",
            code=ErrorCode.JOB_CANCELLATION_CONFLICT,
            status_code=status.HTTP_409_CONFLICT,
        )
        self.current_status = current_status


class JobRetryNotAllowedError(JobError):
    """Raised when a manual or automatic retry is prohibited by policy."""

    def __init__(self, reason: str) -> None:
        super().__init__(
            message=f"Job retry rejected: {reason}",
            code=ErrorCode.JOB_RETRY_NOT_ALLOWED,
            status_code=status.HTTP_400_BAD_REQUEST,
        )
        self.reason = reason


class IdempotencyConflictError(JobError):
    """Raised when an idempotency key is reused with a conflicting payload."""

    def __init__(self, key: str) -> None:
        super().__init__(
            message=f"Idempotency key '{key}' was previously used with different parameters.",
            code=ErrorCode.IDEMPOTENCY_CONFLICT,
            status_code=status.HTTP_409_CONFLICT,
        )
        self.key = key


class JobExecutionError(JobError):
    """Raised when a task fails during worker execution."""

    def __init__(
        self,
        message: str,
        code: str | ErrorCode = ErrorCode.JOB_EXECUTION_FAILED,
    ) -> None:
        super().__init__(
            message=message,
            code=code,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


class JobTimeoutError(JobError):
    """Raised when a job exceeds its configured execution timeout."""

    def __init__(self, timeout_seconds: int) -> None:
        super().__init__(
            message=f"Job exceeded execution deadline of {timeout_seconds} seconds.",
            code=ErrorCode.JOB_TIMEOUT,
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
        )
        self.timeout_seconds = timeout_seconds


class JobQueueUnavailableError(JobError):
    """Raised when the message broker or dispatch transport is unreachable."""

    def __init__(self, message: str = "Background queue broker is unavailable.") -> None:
        super().__init__(
            message=message,
            code=ErrorCode.JOB_QUEUE_UNAVAILABLE,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        )
