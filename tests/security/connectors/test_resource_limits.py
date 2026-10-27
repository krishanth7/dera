"""Tests for Connector Resource Bounds & Denial-of-Service Defense.

Validates that result row counts, identifier lengths, definition sizes, and object counts
are bounded by configured thresholds, and security errors are strictly non-retryable.
"""

import unittest

from dera_connectors.security import (
    ConnectorResourceLimits,
    ReadOnlySecurityViolationError,
    ResourceLimitExceededViolationError,
    SSRFSecurityViolationError,
    TenantIsolationViolationError,
)


class TestResourceLimits(unittest.TestCase):
    """Test suite verifying resource safety thresholds."""

    def setUp(self) -> None:
        self.limits = ConnectorResourceLimits(
            max_result_rows=100,
            max_identifier_length=50,
            max_definition_size_bytes=200,
            max_metadata_objects=500,
        )

    def test_result_rows_threshold(self) -> None:
        """Verify row count caps."""
        # 100 is within limit
        self.limits.check_result_rows(100)

        # 101 exceeds limit
        with self.assertRaises(ResourceLimitExceededViolationError) as ctx:
            self.limits.check_result_rows(101)
        self.assertIn("result_rows", ctx.exception.message)
        self.assertEqual(ctx.exception.details["current_value"], 101)

    def test_identifier_length_threshold(self) -> None:
        """Verify identifier length caps."""
        # 50 chars passes
        self.limits.check_identifier_length("a" * 50)

        # 51 chars fails
        with self.assertRaises(ResourceLimitExceededViolationError) as ctx:
            self.limits.check_identifier_length("a" * 51)
        self.assertIn("identifier_length", ctx.exception.message)

    def test_definition_size_threshold(self) -> None:
        """Verify SQL definition size caps."""
        self.limits.check_definition_size("SELECT 1")

        with self.assertRaises(ResourceLimitExceededViolationError) as ctx:
            self.limits.check_definition_size("x" * 201)
        self.assertIn("definition_size_bytes", ctx.exception.message)

    def test_metadata_object_count_threshold(self) -> None:
        """Verify total schema objects cap."""
        self.limits.check_metadata_object_count(500)

        with self.assertRaises(ResourceLimitExceededViolationError) as ctx:
            self.limits.check_metadata_object_count(501)
        self.assertIn("metadata_objects", ctx.exception.message)

    def test_security_errors_are_never_retryable(self) -> None:
        """Verify security violations, SSRF, read-only, and tenant errors are rejected for retry."""
        self.assertFalse(self.limits.is_error_retryable(ReadOnlySecurityViolationError("DROP")))
        self.assertFalse(
            self.limits.is_error_retryable(SSRFSecurityViolationError("169.254.169.254", "meta"))
        )
        self.assertFalse(
            self.limits.is_error_retryable(TenantIsolationViolationError("ws1", "ws2"))
        )
        self.assertFalse(self.limits.is_error_retryable(PermissionError("Access denied")))

        # Transient network / timeout errors can be retryable
        self.assertTrue(self.limits.is_error_retryable(ConnectionResetError("Socket reset")))
        self.assertTrue(self.limits.is_error_retryable(TimeoutError("TCP timeout")))


if __name__ == "__main__":
    unittest.main()
