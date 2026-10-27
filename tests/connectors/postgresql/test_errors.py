"""Tests for PostgreSQL error taxonomy and SQLSTATE classification."""

import asyncio
import ssl
import unittest

from dera_connectors.errors import (
    ConnectorAuthenticationFailedError,
    ConnectorCancelledError,
    ConnectorConnectionLostError,
    ConnectorPermissionDeniedError,
    ConnectorSecurityViolationError,
    ConnectorTimeoutError,
    ConnectorTLSError,
    ConnectorUnavailableError,
)
from dera_connectors.postgresql.errors import map_postgres_error


class DummySQLError(Exception):
    """Mock exception containing a SQLSTATE code."""

    def __init__(self, message: str, sqlstate: str) -> None:
        super().__init__(message)
        self.sqlstate = sqlstate


class TestPostgresErrorMapping(unittest.TestCase):
    """Verify conversion of database exceptions into DERA domain errors."""

    def test_map_authentication_failed(self) -> None:
        """Verify SQLSTATE 28P01 / 28000 maps to ConnectorAuthenticationFailedError."""
        exc = DummySQLError("password authentication failed for user 'dera'", "28P01")
        mapped = map_postgres_error(exc, operation="connect")
        self.assertIsInstance(mapped, ConnectorAuthenticationFailedError)
        self.assertIn("authentication failed", str(mapped))

    def test_map_permission_denied(self) -> None:
        """Verify SQLSTATE 42501 maps to ConnectorPermissionDeniedError."""
        exc = DummySQLError("permission denied for table pg_shadow", "42501")
        mapped = map_postgres_error(exc, operation="list_tables", details={"resource": "pg_shadow"})
        self.assertIsInstance(mapped, ConnectorPermissionDeniedError)
        self.assertIn("permission denied", str(mapped))
        self.assertEqual(mapped.details.get("permission"), "CATALOG_READ")

    def test_map_statement_timeout(self) -> None:
        """Verify SQLSTATE 57014 maps to ConnectorTimeoutError."""
        exc = DummySQLError("canceling statement due to statement timeout", "57014")
        mapped = map_postgres_error(exc, operation="list_columns")
        self.assertIsInstance(mapped, ConnectorTimeoutError)
        self.assertIn("timed out", str(mapped))

    def test_map_read_only_transaction_violation(self) -> None:
        """Verify SQLSTATE 25006 maps to ConnectorSecurityViolationError."""
        exc = DummySQLError("cannot execute INSERT in a read-only transaction", "25006")
        mapped = map_postgres_error(exc, operation="query")
        self.assertIsInstance(mapped, ConnectorSecurityViolationError)
        self.assertIn("read-only", str(mapped))

    def test_map_connection_lost(self) -> None:
        """Verify SQLSTATE 08006 maps to ConnectorConnectionLostError."""
        exc = DummySQLError("connection failure during transaction", "08006")
        mapped = map_postgres_error(exc, operation="fetch")
        self.assertIsInstance(mapped, ConnectorConnectionLostError)

    def test_map_tls_error(self) -> None:
        """Verify ssl.SSLError maps to ConnectorTLSError."""
        exc = ssl.SSLError("certificate verify failed")
        mapped = map_postgres_error(exc, operation="connect", details={"ssl_mode": "verify-full"})
        self.assertIsInstance(mapped, ConnectorTLSError)
        self.assertIn("TLS handshake failed", str(mapped))

    def test_map_cancelled_error(self) -> None:
        """Verify asyncio.CancelledError maps to ConnectorCancelledError."""
        exc = asyncio.CancelledError()
        mapped = map_postgres_error(exc, operation="list_schemas")
        self.assertIsInstance(mapped, ConnectorCancelledError)

    def test_map_network_unavailable(self) -> None:
        """Verify ConnectionRefusedError maps to ConnectorUnavailableError."""
        exc = ConnectionRefusedError("Connection refused by peer")
        mapped = map_postgres_error(exc, operation="connect")
        self.assertIsInstance(mapped, ConnectorUnavailableError)

    def test_credential_masking_in_error_message(self) -> None:
        """Verify password string is masked if embedded in exception text."""
        exc = Exception("Failed connecting with password=super_secret_cleartext_pw to host")
        mapped = map_postgres_error(exc, operation="connect")
        self.assertNotIn("super_secret_cleartext_pw", str(mapped))


if __name__ == "__main__":
    unittest.main()
