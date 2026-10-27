"""Integration Tests for Timeout Budgets, Deadlines & Cooperative Cancellation.

Validates monotonic deadline propagation across multi-step operations and cancellation
triggers aborting active or queued connector tasks.
"""

import time
import unittest
import uuid

from dera_connectors.context import ConnectorContext
from dera_connectors.security import (
    CancellationRequestedViolationError,
    ConnectorSecurityPolicy,
    DeadlineTracker,
    EnhancedCancellationToken,
    TimeoutBudget,
    TimeoutExceededViolationError,
)


class TestTimeoutsAndCancellation(unittest.TestCase):
    """Test suite verifying timeouts, deadlines, and cancellation mechanisms."""

    def test_timeout_budget_validation(self) -> None:
        """Verify TimeoutBudget validates safety ranges."""
        budget = TimeoutBudget(
            connect_timeout_seconds=15.0,
            query_timeout_seconds=45.0,
            overall_inspection_deadline_seconds=180.0,
        )
        self.assertEqual(budget.connect_timeout_seconds, 15.0)

        with self.assertRaises(ValueError):
            TimeoutBudget(connect_timeout_seconds=0.0)

        with self.assertRaises(ValueError):
            TimeoutBudget(overall_inspection_deadline_seconds=700.0)

    def test_deadline_tracker_detects_expiry(self) -> None:
        """Verify DeadlineTracker tracks elapsed monotonic time and raises on expiry."""
        tracker = DeadlineTracker(deadline_seconds=0.05, operation_name="test_fast_op")
        self.assertFalse(tracker.is_expired)
        self.assertGreater(tracker.remaining_seconds, 0.0)

        # Wait past deadline
        time.sleep(0.06)
        self.assertTrue(tracker.is_expired)
        self.assertEqual(tracker.remaining_seconds, 0.0)

        with self.assertRaises(TimeoutExceededViolationError) as ctx:
            tracker.check_deadline()
        self.assertIn("test_fast_op", ctx.exception.message)
        self.assertIn("exceeded deadline budget", ctx.exception.message)

    def test_deadline_tracker_sub_budget_allocation(self) -> None:
        """Verify sub-budgets are clamped by the overall remaining deadline."""
        tracker = DeadlineTracker(deadline_seconds=5.0)
        # Requesting a 10s sub-query when 5s remains clamps to <= 5s
        allocated = tracker.allocate_sub_budget(10.0)
        self.assertLessEqual(allocated, 5.0)
        self.assertGreater(allocated, 4.0)

    def test_enhanced_cancellation_token_callbacks_and_hierarchy(self) -> None:
        """Verify EnhancedCancellationToken propagates cancellation and fires callbacks."""
        parent_token = EnhancedCancellationToken()
        child_token = parent_token.create_child()

        callback_fired = []
        child_token.register_callback(lambda: callback_fired.append("child_cleaned"))

        self.assertFalse(parent_token.is_cancelled)
        self.assertFalse(child_token.is_cancelled)

        # Cancel parent
        parent_token.cancel("User clicked abort.")
        self.assertTrue(parent_token.is_cancelled)
        self.assertTrue(child_token.is_cancelled)
        self.assertIn("User clicked abort", str(child_token.cancellation_reason))
        self.assertEqual(callback_fired, ["child_cleaned"])

        with self.assertRaises(CancellationRequestedViolationError) as ctx:
            child_token.raise_if_cancelled()
        self.assertIn("User clicked abort", ctx.exception.message)

    def test_connector_security_policy_enforces_active_context(self) -> None:
        """Verify ConnectorSecurityPolicy aborts if context deadline is expired or cancelled."""
        policy = ConnectorSecurityPolicy()
        ws_id = uuid.uuid4()

        # Expired context
        expired_ctx = ConnectorContext(
            workspace_id=ws_id,
            deadline_seconds=0.01,
            created_at_epoch=time.time() - 10.0,
        )

        from dera_connectors.errors import ConnectorTimeoutError

        with self.assertRaises(ConnectorTimeoutError):
            policy.evaluate_query(
                context=expired_ctx,
                engine="postgresql",
                operation_id="postgres.catalog.tables",
                sql="SELECT 1",
            )


if __name__ == "__main__":
    unittest.main()
