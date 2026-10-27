"""Tests for In-Memory Authentication Rate Limiter.

Validates sliding-window failure counting, temporary lockout triggering,
attempt pruning, and successful login reset behavior.
"""

import time
import unittest

from dera_api.auth.rate_limiter import AuthRateLimiter


class TestAuthRateLimiter(unittest.TestCase):
    """Test suite for authentication attempt throttling."""

    def setUp(self) -> None:
        self.limiter = AuthRateLimiter()

    def test_failure_accumulation_and_lockout(self) -> None:
        """Verify that reaching max_attempts triggers rate limiting."""
        key = "127.0.0.1:user@example.com"
        max_attempts = 3
        window = 10

        self.assertFalse(self.limiter.is_rate_limited(key, max_attempts, window))

        # Record 2 failures
        self.assertEqual(self.limiter.record_failure(key, window), 1)
        self.assertEqual(self.limiter.record_failure(key, window), 2)
        self.assertFalse(self.limiter.is_rate_limited(key, max_attempts, window))

        # 3rd failure reaches limit
        self.assertEqual(self.limiter.record_failure(key, window), 3)
        self.assertTrue(self.limiter.is_rate_limited(key, max_attempts, window))

    def test_reset_clears_failures(self) -> None:
        """Verify that reset clears lockout state upon successful login."""
        key = "192.168.1.1:admin@example.com"
        for _ in range(5):
            self.limiter.record_failure(key, window_seconds=60)

        self.assertTrue(self.limiter.is_rate_limited(key, max_attempts=5, window_seconds=60))
        self.limiter.reset(key)
        self.assertFalse(self.limiter.is_rate_limited(key, max_attempts=5, window_seconds=60))

    def test_window_expiration(self) -> None:
        """Verify that failures outside the window expire cleanly."""
        key = "10.0.0.1:test@example.com"
        # 1-second window
        self.limiter.record_failure(key, window_seconds=1)
        self.limiter.record_failure(key, window_seconds=1)
        self.assertTrue(self.limiter.is_rate_limited(key, max_attempts=2, window_seconds=1))

        # Wait for window to elapse
        time.sleep(1.1)
        self.assertFalse(self.limiter.is_rate_limited(key, max_attempts=2, window_seconds=1))


if __name__ == "__main__":
    unittest.main()
