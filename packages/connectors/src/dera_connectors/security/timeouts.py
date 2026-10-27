"""DERA Connectors — Centralized Timeout Budgets & Deadline Propagation.

Provides centralized timeout policies and monotonic deadline tracking to prevent
infinite connection attempts, query hangs, and unbounded multi-step schema inspections.
"""

from __future__ import annotations

import time
from dataclasses import dataclass

from dera_connectors.security.errors import TimeoutExceededViolationError


@dataclass(frozen=True)
class TimeoutBudget:
    """Centralized timeout policy configuration for database connectors."""

    connect_timeout_seconds: float = 10.0
    dns_timeout_seconds: float = 3.0
    tls_handshake_timeout_seconds: float = 5.0
    query_timeout_seconds: float = 30.0
    overall_inspection_deadline_seconds: float = 120.0
    normalization_timeout_seconds: float = 15.0
    cleanup_timeout_seconds: float = 5.0

    def __post_init__(self) -> None:
        """Validate timeout values fall within acceptable safety bounds."""
        if self.connect_timeout_seconds <= 0 or self.connect_timeout_seconds > 60:
            raise ValueError("connect_timeout_seconds must be between 0.1 and 60.0s")
        if self.query_timeout_seconds <= 0 or self.query_timeout_seconds > 180:
            raise ValueError("query_timeout_seconds must be between 0.1 and 180.0s")
        if (
            self.overall_inspection_deadline_seconds <= 0
            or self.overall_inspection_deadline_seconds > 600
        ):
            raise ValueError("overall_inspection_deadline_seconds must be between 1.0 and 600.0s")


class DeadlineTracker:
    """Monotonic deadline tracker propagating overall deadlines across nested operations."""

    def __init__(self, deadline_seconds: float, operation_name: str = "inspection") -> None:
        self.operation_name = operation_name
        self.deadline_seconds = float(deadline_seconds)
        self.start_time = time.monotonic()

    @property
    def elapsed_seconds(self) -> float:
        """Elapsed time since tracker initialization."""
        return time.monotonic() - self.start_time

    @property
    def remaining_seconds(self) -> float:
        """Remaining seconds before deadline is reached, bounded at 0.0."""
        rem = self.deadline_seconds - self.elapsed_seconds
        return max(0.0, rem)

    @property
    def is_expired(self) -> bool:
        """Return True if elapsed time has met or exceeded the allocated deadline."""
        return self.elapsed_seconds >= self.deadline_seconds

    def check_deadline(self) -> None:
        """Verify that the deadline has not expired.

        Raises
        ------
        TimeoutExceededViolationError
            If elapsed time has met or exceeded deadline.
        """
        if self.is_expired:
            raise TimeoutExceededViolationError(
                operation=self.operation_name,
                deadline_seconds=self.deadline_seconds,
                elapsed_seconds=self.elapsed_seconds,
            )

    def allocate_sub_budget(self, proposed_seconds: float) -> float:
        """Calculate a safe timeout for a sub-query, clamped by the overall remaining deadline."""
        self.check_deadline()
        return min(proposed_seconds, self.remaining_seconds)
