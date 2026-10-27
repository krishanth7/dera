"""DERA Jobs — Retry Policy and Exponential Backoff.

Implements bounded exponential backoff with configurable jitter, error classification,
and retry schedule determination.
"""

from datetime import UTC, datetime, timedelta
import random

from dera_api.jobs.exceptions import (
    IdempotencyConflictError,
    JobAlreadyCompletedError,
    JobCancellationConflictError,
    JobNotFoundError,
    JobPayloadInvalidError,
    JobRetryNotAllowedError,
    JobTypeUnsupportedError,
)

NON_RETRYABLE_EXCEPTIONS: tuple[type[Exception], ...] = (
    JobTypeUnsupportedError,
    JobPayloadInvalidError,
    JobAlreadyCompletedError,
    JobCancellationConflictError,
    JobRetryNotAllowedError,
    IdempotencyConflictError,
    JobNotFoundError,
    ValueError,
    TypeError,
    KeyError,
)


def calculate_backoff(
    attempt: int,
    base_delay: float = 2.0,
    max_delay: float = 300.0,
    jitter: bool = True,
    jitter_factor: float = 0.2,
) -> float:
    """Calculate exponential backoff delay in seconds for a given attempt.

    Parameters
    ----------
    attempt : int
        1-indexed attempt number (1 for first retry, 2 for second retry, etc.).
    base_delay : float
        Base delay in seconds (default 2.0s).
    max_delay : float
        Upper ceiling in seconds (default 300.0s = 5 minutes).
    jitter : bool
        Whether to apply bounded pseudo-random jitter.
    jitter_factor : float
        Fractional bounds for jitter (e.g. 0.2 means +/- 20%).

    Returns
    -------
    float
        Calculated delay in seconds, guaranteed >= 0.1 and <= max_delay.
    """
    if attempt <= 0:
        attempt = 1

    # Exponential formula: base * 2^(attempt - 1)
    raw_delay = base_delay * (2 ** (attempt - 1))
    capped_delay = min(max_delay, raw_delay)

    if not jitter or jitter_factor <= 0:
        return round(capped_delay, 3)

    # Apply symmetric bounded jitter around capped_delay
    min_jitter = max(0.1, capped_delay * (1.0 - jitter_factor))
    max_jitter = min(max_delay, capped_delay * (1.0 + jitter_factor))
    jittered = random.uniform(min_jitter, max_jitter)  # noqa: S311

    return round(min(max_delay, max(0.1, jittered)), 3)


def calculate_next_retry_at(
    attempt: int,
    base_delay: float = 2.0,
    max_delay: float = 300.0,
    jitter: bool = True,
) -> datetime:
    """Compute the UTC timestamp for the next retry attempt."""
    delay = calculate_backoff(attempt, base_delay, max_delay, jitter=jitter)
    return datetime.now(UTC) + timedelta(seconds=delay)


def is_retryable_error(exc: Exception) -> bool:
    """Determine whether an execution failure is transient and eligible for retry.

    Parameters
    ----------
    exc : Exception
        Exception raised during task execution.

    Returns
    -------
    bool
        True if the failure is retryable, False if terminal.
    """
    if isinstance(exc, NON_RETRYABLE_EXCEPTIONS):
        return False

    # Check explicit non_retryable attribute if set on custom exception
    if getattr(exc, "non_retryable", False) is True:
        return False

    return True
