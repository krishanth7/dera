"""DERA Jobs — Lifecycle State Machine.

Enforces deterministic state transitions for background jobs. Prohibits illegal transitions,
terminal state mutation, and duplicate completions.
"""

from dera_api.jobs.enums import JobStatus
from dera_api.jobs.exceptions import (
    JobAlreadyCompletedError,
    JobCancellationConflictError,
    JobError,
)


class InvalidStateTransitionError(JobError):
    """Raised when an illegal transition is attempted between non-terminal states."""

    def __init__(self, current_status: JobStatus, target_status: JobStatus) -> None:
        super().__init__(
            f"Invalid job state transition from '{current_status}' to '{target_status}'.",
            error_code="INVALID_STATE_TRANSITION",
        )
        self.current_status = current_status
        self.target_status = target_status


# Authoritative mapping of allowed source -> destination state transitions
ALLOWED_TRANSITIONS: dict[JobStatus, set[JobStatus]] = {
    JobStatus.PENDING: {
        JobStatus.QUEUED,
        JobStatus.CANCELLED,
    },
    JobStatus.QUEUED: {
        JobStatus.RUNNING,
        JobStatus.CANCELLED,
    },
    JobStatus.RUNNING: {
        JobStatus.SUCCEEDED,
        JobStatus.FAILED,
        JobStatus.RETRY_SCHEDULED,
        JobStatus.CANCEL_REQUESTED,
    },
    JobStatus.RETRY_SCHEDULED: {
        JobStatus.QUEUED,
        JobStatus.CANCELLED,
    },
    JobStatus.CANCEL_REQUESTED: {
        JobStatus.CANCELLED,
        JobStatus.SUCCEEDED,
        JobStatus.FAILED,
    },
    JobStatus.SUCCEEDED: set(),
    JobStatus.FAILED: set(),
    JobStatus.CANCELLED: set(),
}


def validate_transition(current: JobStatus | str, target: JobStatus | str) -> None:
    """Validate whether transitioning from current to target is legally permitted.

    Parameters
    ----------
    current : JobStatus | str
        Current status of the job.
    target : JobStatus | str
        Requested target status.

    Raises
    ------
    JobAlreadyCompletedError
        If the current status is an immutable terminal state.
    JobCancellationConflictError
        If cancellation is requested from an invalid state.
    InvalidStateTransitionError
        If the transition is illegal according to the state machine matrix.
    """
    current_status = JobStatus(current)
    target_status = JobStatus(target)

    # Transitioning to the same status is a no-op
    if current_status == target_status:
        return

    # Check terminal immutability
    if current_status.is_terminal:
        raise JobAlreadyCompletedError(current_status.value)

    allowed = ALLOWED_TRANSITIONS.get(current_status, set())
    if target_status not in allowed:
        if target_status in {JobStatus.CANCEL_REQUESTED, JobStatus.CANCELLED}:
            raise JobCancellationConflictError(current_status.value)
        raise InvalidStateTransitionError(current_status, target_status)


def can_transition(current: JobStatus | str, target: JobStatus | str) -> bool:
    """Check boolean feasibility of a state transition without raising exceptions."""
    try:
        validate_transition(current, target)
        return True
    except JobError:
        return False
