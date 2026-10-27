"""DERA Connectors — Cooperative & Asynchronous Cancellation Management.

Coordinates cooperative cancellation across socket reads, driver executions,
connection pool acquisitions, and multi-query schema inspection workflows.
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable

from dera_connectors.security.errors import CancellationRequestedViolationError


class EnhancedCancellationToken:
    """Cooperative cancellation token supporting callbacks and parent-child hierarchy."""

    def __init__(self, parent: EnhancedCancellationToken | None = None) -> None:
        self._is_cancelled: bool = False
        self._reason: str | None = None
        self._callbacks: list[Callable[[], None]] = []
        self._async_event: asyncio.Event | None = None

        if parent is not None:
            parent.register_callback(
                lambda: self.cancel(f"Inherited from parent: {parent.cancellation_reason}")
            )
            if parent.is_cancelled:
                self.cancel(f"Inherited from parent: {parent.cancellation_reason}")

    @property
    def is_cancelled(self) -> bool:
        """Return True if cancellation has been signaled."""
        return self._is_cancelled

    @property
    def cancellation_reason(self) -> str | None:
        """Return the cancellation explanation if cancelled."""
        return self._reason

    def register_callback(self, callback: Callable[[], None]) -> None:
        """Register a cleanup or interrupt callback to be invoked upon cancellation."""
        if self._is_cancelled:
            try:
                callback()
            except Exception:
                pass
            return
        self._callbacks.append(callback)

    def cancel(self, reason: str = "Operation cancelled by user or caller.") -> None:
        """Trigger cancellation and execute all registered cleanup handlers."""
        if self._is_cancelled:
            return
        self._is_cancelled = True
        self._reason = reason

        # Fire registered callbacks
        for cb in self._callbacks:
            try:
                cb()
            except Exception:
                pass

        # Set asyncio event if initialized
        if self._async_event is not None and not self._async_event.is_set():
            self._async_event.set()

    def raise_if_cancelled(self) -> None:
        """Raise CancellationRequestedViolationError if cancellation was triggered."""
        if self._is_cancelled:
            raise CancellationRequestedViolationError(self._reason or "Operation was cancelled.")

    def create_child(self) -> EnhancedCancellationToken:
        """Create a linked child cancellation token."""
        return EnhancedCancellationToken(parent=self)
