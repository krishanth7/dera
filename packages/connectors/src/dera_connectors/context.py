"""DERA Connectors — Connector Execution Context & Cancellation.

Provides execution boundaries, tenant identification, correlation tracing, and
cancellation signaling for database connector operations.
"""

import time
import uuid
from dataclasses import dataclass, field


class CancellationToken:
    """Cooperative cancellation token for connector operations."""

    def __init__(self) -> None:
        self._is_cancelled: bool = False
        self._reason: str | None = None

    @property
    def is_cancelled(self) -> bool:
        """Return True if cancellation has been signaled."""
        return self._is_cancelled

    @property
    def cancellation_reason(self) -> str | None:
        """Return the reason provided when cancelled."""
        return self._reason

    def cancel(self, reason: str = "Operation cancelled by user or caller.") -> None:
        """Trigger cancellation."""
        self._is_cancelled = True
        self._reason = reason

    def raise_if_cancelled(self) -> None:
        """Raise ConnectorCancelledError if cancellation was requested."""
        if self._is_cancelled:
            from dera_connectors.errors import ConnectorCancelledError

            raise ConnectorCancelledError(self._reason or "Operation was cancelled.")


@dataclass(frozen=True)
class ConnectorContext:
    """Execution context bound to every connector invocation and inspection."""

    workspace_id: uuid.UUID
    correlation_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    user_id: uuid.UUID | None = None
    cancellation_token: CancellationToken = field(default_factory=CancellationToken)
    deadline_seconds: float = 60.0
    created_at_epoch: float = field(default_factory=time.time)

    @property
    def is_expired(self) -> bool:
        """Return True if elapsed time exceeds deadline_seconds."""
        return (time.time() - self.created_at_epoch) > self.deadline_seconds

    def check_active(self) -> None:
        """Verify context is neither cancelled nor timed out.

        Raises
        ------
        ConnectorCancelledError
            If cancelled.
        ConnectorTimeoutError
            If deadline exceeded.
        """
        self.cancellation_token.raise_if_cancelled()
        if self.is_expired:
            from dera_connectors.errors import ConnectorTimeoutError

            raise ConnectorTimeoutError(
                f"Connector operation deadline of {self.deadline_seconds}s exceeded."
            )
