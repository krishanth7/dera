"""DERA Connectors — Connection Lifecycle State Machine.

Manages connection states, transitions, resource allocation, and teardown invariants.
"""

import logging
from enum import StrEnum

logger = logging.getLogger(__name__)


class ConnectionState(StrEnum):
    """Finite connection lifecycle states."""

    CREATED = "created"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    FAILED = "failed"
    CLOSING = "closing"
    CLOSED = "closed"


# Allowed state transitions matrix
_ALLOWED_TRANSITIONS: dict[ConnectionState, set[ConnectionState]] = {
    ConnectionState.CREATED: {ConnectionState.CONNECTING, ConnectionState.CLOSED},
    ConnectionState.CONNECTING: {
        ConnectionState.CONNECTED,
        ConnectionState.FAILED,
        ConnectionState.CLOSING,
    },
    ConnectionState.CONNECTED: {ConnectionState.CLOSING, ConnectionState.FAILED},
    ConnectionState.FAILED: {ConnectionState.CLOSING, ConnectionState.CLOSED},
    ConnectionState.CLOSING: {ConnectionState.CLOSED},
    ConnectionState.CLOSED: set(),  # Terminal state; closed connections cannot be resurrected
}


class InvalidLifecycleTransitionError(Exception):
    """Raised when an illegal lifecycle transition is attempted."""

    def __init__(self, current_state: ConnectionState, target_state: ConnectionState) -> None:
        super().__init__(
            f"Cannot transition connector from '{current_state.value}' to '{target_state.value}'."
        )
        self.current_state = current_state
        self.target_state = target_state


class ConnectionLifecycle:
    """Tracks and enforces the explicit connection state machine for a connector instance."""

    def __init__(self) -> None:
        self._state: ConnectionState = ConnectionState.CREATED
        self._failure_reason: str | None = None

    @property
    def state(self) -> ConnectionState:
        """Return the current connection lifecycle state."""
        return self._state

    @property
    def is_active(self) -> bool:
        """Return True if connector holds an open, usable connection."""
        return self._state == ConnectionState.CONNECTED

    @property
    def is_terminal(self) -> bool:
        """Return True if connector has reached the terminal CLOSED state."""
        return self._state == ConnectionState.CLOSED

    @property
    def failure_reason(self) -> str | None:
        """Return recorded failure reason if connection transitioned to FAILED."""
        return self._failure_reason

    def can_transition_to(self, target: ConnectionState) -> bool:
        """Return True if transitioning to target state is permissible."""
        return target in _ALLOWED_TRANSITIONS.get(self._state, set())

    def transition_to(self, target: ConnectionState, reason: str | None = None) -> None:
        """Transition lifecycle state or raise InvalidLifecycleTransitionError.

        Parameters
        ----------
        target : ConnectionState
            The target state to transition to.
        reason : str | None
            Optional diagnostic explanation (e.g. failure reason or cancellation).
        """
        if self._state == target:
            # Idempotent no-op for repeated identical transitions (e.g. repeated close())
            return

        if not self.can_transition_to(target):
            raise InvalidLifecycleTransitionError(self._state, target)

        prev = self._state
        self._state = target
        if target == ConnectionState.FAILED and reason:
            self._failure_reason = reason

        logger.debug(
            "Connector lifecycle transition: %s -> %s (reason=%s)",
            prev.value,
            target.value,
            reason or "normal",
        )
