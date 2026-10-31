"""DERA Diagnostics — Finding Lifecycle State Machine.

Manages explicit lifecycle progression for diagnostic findings across evaluations,
preventing premature or unverified automated closures.
"""

from __future__ import annotations

from enum import StrEnum

from dera.diagnostics.exceptions import DiagnosticEngineError


class InvalidLifecycleTransitionError(DiagnosticEngineError):
    """Raised when an invalid finding lifecycle transition is requested."""

    def __init__(self, current: str, requested: str, reason: str = "") -> None:
        super().__init__(
            f"Cannot transition finding from '{current}' to '{requested}': {reason or 'invalid state transition.'}"
        )
        self.current = current
        self.requested = requested


class FindingLifecycleState(StrEnum):
    """Explicit lifecycle states for tracking findings across evaluations."""

    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    SUPPRESSED = "suppressed"
    RESOLVED = "resolved"
    REOPENED = "reopened"


_VALID_TRANSITIONS: dict[FindingLifecycleState, set[FindingLifecycleState]] = {
    FindingLifecycleState.OPEN: {
        FindingLifecycleState.ACKNOWLEDGED,
        FindingLifecycleState.SUPPRESSED,
        FindingLifecycleState.RESOLVED,
    },
    FindingLifecycleState.ACKNOWLEDGED: {
        FindingLifecycleState.SUPPRESSED,
        FindingLifecycleState.RESOLVED,
    },
    FindingLifecycleState.SUPPRESSED: {
        FindingLifecycleState.REOPENED,
        FindingLifecycleState.RESOLVED,
    },
    FindingLifecycleState.RESOLVED: {
        FindingLifecycleState.REOPENED,
    },
    FindingLifecycleState.REOPENED: {
        FindingLifecycleState.ACKNOWLEDGED,
        FindingLifecycleState.SUPPRESSED,
        FindingLifecycleState.RESOLVED,
    },
}


def transition_lifecycle_state(
    current: FindingLifecycleState,
    target: FindingLifecycleState,
    actor: str,
    reason: str,
) -> FindingLifecycleState:
    """Validates and executes a lifecycle transition."""
    if not actor or not actor.strip():
        raise InvalidLifecycleTransitionError(
            current.value, target.value, "Actor must be specified."
        )
    if not reason or len(reason.strip()) < 3:
        raise InvalidLifecycleTransitionError(
            current.value, target.value, "A valid reason must be specified."
        )

    if target not in _VALID_TRANSITIONS.get(current, set()):
        raise InvalidLifecycleTransitionError(
            current.value,
            target.value,
            f"Permitted transitions from '{current.value}': {[s.value for s in _VALID_TRANSITIONS.get(current, set())]}",
        )

    return target
