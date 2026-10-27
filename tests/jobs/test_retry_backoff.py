"""Unit Tests for Job Retry Policy and Exponential Backoff.

Validates deterministic backoff calculations, bounded jitter guarantees,
and error classification between retryable and non-retryable failures.
"""

import unittest
from datetime import UTC, datetime

from dera_api.jobs.exceptions import (
    IdempotencyConflictError,
    JobAlreadyCompletedError,
    JobExecutionError,
    JobPayloadInvalidError,
    JobTypeUnsupportedError,
)
from dera_api.jobs.retry import (
    calculate_backoff,
    calculate_next_retry_at,
    is_retryable_error,
)


class TestJobRetryPolicy(unittest.TestCase):
    """Test suite validating retry backoff formulas and failure classifications."""

    def test_deterministic_exponential_backoff(self) -> None:
        """Verify 2^(attempt-1) exponential backoff without jitter."""
        base = 2.0
        max_d = 300.0

        # Attempt 1 -> 2.0 * 2^0 = 2.0
        self.assertEqual(
            calculate_backoff(attempt=1, base_delay=base, max_delay=max_d, jitter=False), 2.0
        )
        # Attempt 2 -> 2.0 * 2^1 = 4.0
        self.assertEqual(
            calculate_backoff(attempt=2, base_delay=base, max_delay=max_d, jitter=False), 4.0
        )
        # Attempt 3 -> 2.0 * 2^2 = 8.0
        self.assertEqual(
            calculate_backoff(attempt=3, base_delay=base, max_delay=max_d, jitter=False), 8.0
        )
        # Attempt 4 -> 2.0 * 2^3 = 16.0
        self.assertEqual(
            calculate_backoff(attempt=4, base_delay=base, max_delay=max_d, jitter=False), 16.0
        )
        # Attempt 5 -> 2.0 * 2^4 = 32.0
        self.assertEqual(
            calculate_backoff(attempt=5, base_delay=base, max_delay=max_d, jitter=False), 32.0
        )

    def test_backoff_max_delay_cap(self) -> None:
        """Verify that backoff is bounded by max_delay."""
        cap = 50.0
        delay = calculate_backoff(attempt=10, base_delay=2.0, max_delay=cap, jitter=False)
        self.assertEqual(delay, cap)

    def test_backoff_with_jitter_within_bounds(self) -> None:
        """Verify backoff with jitter remains strictly within [0.8*delay, 1.2*delay] and <= max_delay."""
        base = 10.0
        max_d = 100.0

        for _ in range(20):
            delay = calculate_backoff(
                attempt=2, base_delay=base, max_delay=max_d, jitter=True, jitter_factor=0.2
            )
            # Expected uncapped target is 20.0; bounded within [16.0, 24.0]
            self.assertGreaterEqual(delay, 15.9)
            self.assertLessEqual(delay, 24.1)

    def test_calculate_next_retry_at(self) -> None:
        """Verify next_retry_at is in the future."""
        before = datetime.now(UTC)
        next_at = calculate_next_retry_at(attempt=1, base_delay=5.0, max_delay=300.0, jitter=False)
        after = datetime.now(UTC)

        self.assertGreater(next_at, before)
        self.assertGreater(next_at, after)
        # Ensure it is roughly 5 seconds ahead
        diff = (next_at - before).total_seconds()
        self.assertGreaterEqual(diff, 4.9)
        self.assertLessEqual(diff, 6.0)

    def test_error_classification(self) -> None:
        """Verify non-retryable vs retryable exception classifications."""
        # Non-retryable
        self.assertFalse(is_retryable_error(JobTypeUnsupportedError("test.invalid")))
        self.assertFalse(is_retryable_error(JobPayloadInvalidError("bad payload")))
        self.assertFalse(is_retryable_error(JobAlreadyCompletedError("succeeded")))
        self.assertFalse(is_retryable_error(IdempotencyConflictError("k1")))
        self.assertFalse(is_retryable_error(ValueError("Invalid argument")))
        self.assertFalse(is_retryable_error(TypeError("Type error")))

        # Custom non-retryable
        custom = Exception("Permanent error")
        custom.non_retryable = True
        self.assertFalse(is_retryable_error(custom))

        # Retryable
        self.assertTrue(is_retryable_error(JobExecutionError("Transient network timeout")))
        self.assertTrue(is_retryable_error(ConnectionError("Broker connection reset")))
        self.assertTrue(is_retryable_error(TimeoutError("Database query timed out")))


if __name__ == "__main__":
    unittest.main()
