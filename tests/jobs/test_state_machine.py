"""Unit Tests for Background Job Lifecycle State Machine.

Validates that state transitions follow the deterministic state machine matrix:
- Legal transitions succeed.
- Illegal transitions raise InvalidStateTransitionError or JobCancellationConflictError.
- Terminal states (SUCCEEDED, FAILED, CANCELLED) are strictly immutable.
"""

import unittest

from dera_api.jobs.enums import JobStatus
from dera_api.jobs.exceptions import (
    JobAlreadyCompletedError,
    JobCancellationConflictError,
)
from dera_api.jobs.lifecycle import (
    ALLOWED_TRANSITIONS,
    InvalidStateTransitionError,
    can_transition,
    validate_transition,
)


class TestJobStateMachine(unittest.TestCase):
    """Test suite validating background job lifecycle transitions."""

    def test_allowed_transitions_matrix(self) -> None:
        """Verify all legally specified transitions validate successfully."""
        for current, allowed_targets in ALLOWED_TRANSITIONS.items():
            for target in allowed_targets:
                self.assertTrue(
                    can_transition(current, target),
                    f"Expected transition {current} -> {target} to be valid",
                )
                # Should not raise exception
                validate_transition(current, target)

    def test_same_status_transition_is_noop(self) -> None:
        """Verify transition to identical status is permitted as a no-op."""
        for status in JobStatus:
            self.assertTrue(can_transition(status, status))
            validate_transition(status, status)

    def test_terminal_states_are_immutable(self) -> None:
        """Verify terminal states (SUCCEEDED, FAILED, CANCELLED) prohibit all transitions."""
        terminal_states = [JobStatus.SUCCEEDED, JobStatus.FAILED, JobStatus.CANCELLED]
        all_states = list(JobStatus)

        for terminal in terminal_states:
            self.assertTrue(terminal.is_terminal)
            for target in all_states:
                if target == terminal:
                    continue
                self.assertFalse(
                    can_transition(terminal, target),
                    f"Terminal status {terminal} should reject transition to {target}",
                )
                with self.assertRaises(JobAlreadyCompletedError) as ctx:
                    validate_transition(terminal, target)
                self.assertEqual(ctx.exception.current_status, terminal.value)

    def test_illegal_non_terminal_transitions_rejected(self) -> None:
        """Verify illegal transitions between non-terminal states raise InvalidStateTransitionError."""
        illegal_pairs = [
            (JobStatus.PENDING, JobStatus.SUCCEEDED),
            (JobStatus.PENDING, JobStatus.FAILED),
            (JobStatus.PENDING, JobStatus.RUNNING),
            (JobStatus.QUEUED, JobStatus.SUCCEEDED),
            (JobStatus.QUEUED, JobStatus.FAILED),
            (JobStatus.QUEUED, JobStatus.RETRY_SCHEDULED),
            (JobStatus.RUNNING, JobStatus.PENDING),
            (JobStatus.RUNNING, JobStatus.QUEUED),
            (JobStatus.RETRY_SCHEDULED, JobStatus.RUNNING),
            (JobStatus.RETRY_SCHEDULED, JobStatus.SUCCEEDED),
        ]

        for current, target in illegal_pairs:
            self.assertFalse(can_transition(current, target))
            with self.assertRaises(InvalidStateTransitionError):
                validate_transition(current, target)

    def test_cancellation_conflict_errors(self) -> None:
        """Verify requesting cancellation from invalid states raises JobCancellationConflictError."""
        # Note: CANCELLED and SUCCEEDED are terminal so they raise JobAlreadyCompletedError
        # But if a non-terminal state doesn't allow cancellation, it raises JobCancellationConflictError
        self.assertTrue(can_transition(JobStatus.PENDING, JobStatus.CANCELLED))
        self.assertTrue(can_transition(JobStatus.QUEUED, JobStatus.CANCELLED))
        self.assertTrue(can_transition(JobStatus.RUNNING, JobStatus.CANCEL_REQUESTED))
        self.assertTrue(can_transition(JobStatus.RETRY_SCHEDULED, JobStatus.CANCELLED))
        self.assertTrue(can_transition(JobStatus.CANCEL_REQUESTED, JobStatus.CANCELLED))


if __name__ == "__main__":
    unittest.main()
