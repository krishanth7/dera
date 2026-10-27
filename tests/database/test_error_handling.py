"""Tests for Database Exception Mapping & Credential Sanitization.

Validates that raw database and driver exceptions are mapped to safe RFC 9457
domain errors without leaking internal connection credentials or SQL parameters.
"""

import unittest

from dera_api.contracts.errors import ErrorCode
from dera_api.core.exceptions import ConflictError, DependencyUnavailableError
from dera_api.db.exceptions import (
    DatabaseConnectionError,
    DatabaseConstraintViolationError,
    DatabaseTimeoutError,
    map_database_exception,
    raise_mapped_database_exception,
    sanitize_database_error_message,
)
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.exc import TimeoutError as SATimeoutError


class TestDatabaseErrorHandling(unittest.TestCase):
    """Test suite for database exception sanitization and error taxonomy mapping."""

    def test_sanitize_database_error_message_masks_passwords(self) -> None:
        """Verify that password components in URIs are masked with asterisks."""
        raw = "could not connect to postgresql+asyncpg://admin:super_secret_password@db-host:5432/dera"
        sanitized = sanitize_database_error_message(raw)
        self.assertNotIn("super_secret_password", sanitized)
        self.assertIn("postgresql+asyncpg://admin:***@db-host:5432/dera", sanitized)

    def test_sanitize_database_error_message_redacts_sql_parameters(self) -> None:
        """Verify that parameter dumps are redacted in error messages."""
        raw = "INSERT INTO users (email) VALUES ($1) [parameters: ('secret@email.com',)]"
        sanitized = sanitize_database_error_message(raw)
        self.assertNotIn("secret@email.com", sanitized)
        self.assertIn("[parameters: <redacted>]", sanitized)

    def test_map_integrity_error_unique_to_conflict(self) -> None:
        """Verify that unique constraint IntegrityError maps to DatabaseConstraintViolationError."""
        orig_err = Exception(
            "duplicate key value violates unique constraint pk_dera_platform_metadata"
        )
        sa_err = IntegrityError("INSERT...", [], orig_err)
        mapped = map_database_exception(sa_err)

        self.assertIsInstance(mapped, DatabaseConstraintViolationError)
        self.assertIsInstance(mapped, ConflictError)
        self.assertEqual(mapped.code, ErrorCode.CONFLICT)
        self.assertEqual(mapped.status_code, 409)

    def test_map_integrity_error_foreign_key(self) -> None:
        """Verify that foreign key IntegrityError maps to DatabaseConstraintViolationError."""
        orig_err = Exception("insert or update on table violates foreign key constraint fk_users")
        sa_err = IntegrityError("INSERT...", [], orig_err)
        mapped = map_database_exception(sa_err)

        self.assertIsInstance(mapped, DatabaseConstraintViolationError)
        self.assertIn("Referenced relation constraint failed", mapped.message)

    def test_map_operational_error_to_dependency_unavailable(self) -> None:
        """Verify that connection OperationalError maps to DatabaseConnectionError."""
        sa_err = OperationalError("connection refused", [], Exception("connect failed"))
        mapped = map_database_exception(sa_err)

        self.assertIsInstance(mapped, DatabaseConnectionError)
        self.assertIsInstance(mapped, DependencyUnavailableError)
        self.assertEqual(mapped.code, ErrorCode.DEPENDENCY_UNAVAILABLE)
        self.assertEqual(mapped.status_code, 503)

    def test_map_timeout_error_to_database_timeout(self) -> None:
        """Verify that TimeoutError maps to DatabaseTimeoutError."""
        sa_err = SATimeoutError("QueuePool limit of size 10 overflow 5 reached")
        mapped = map_database_exception(sa_err)

        self.assertIsInstance(mapped, DatabaseTimeoutError)
        self.assertIsInstance(mapped, DependencyUnavailableError)
        self.assertEqual(mapped.status_code, 503)

    def test_raise_mapped_database_exception(self) -> None:
        """Verify that raise_mapped_database_exception raises the mapped error."""
        with self.assertRaises(DatabaseConstraintViolationError):
            raise_mapped_database_exception(
                IntegrityError("INSERT...", [], Exception("unique violation"))
            )


if __name__ == "__main__":
    unittest.main()
