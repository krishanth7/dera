"""Unit Tests for DERA MySQL-Family Error Mapping and Credential Masking.

Validates:
- Mapping of PyMySQL / MySQL error numbers to Phase 5.1 ConnectorError subclasses
- Credential masking in diagnostics and error representations
"""

import unittest

import pymysql
from dera_connectors.errors import (
    ConnectorAuthenticationFailedError,
    ConnectorCancelledError,
    ConnectorMetadataError,
    ConnectorPermissionDeniedError,
    ConnectorTimeoutError,
    ConnectorTLSError,
    ConnectorUnavailableError,
)
from dera_connectors.mysql_family.errors import map_mysql_family_error


class TestMySqlFamilyErrors(unittest.TestCase):
    """Test suite verifying error taxonomy mapping and credential sanitization."""

    def test_authentication_failed_mapping(self) -> None:
        """Verify error code 1045 maps to ConnectorAuthenticationFailedError."""
        exc = pymysql.err.OperationalError(
            1045, "Access denied for user 'admin'@'localhost' (using password: YES)"
        )
        mapped = map_mysql_family_error(exc, database="mydb", host="localhost", port=3306)
        self.assertIsInstance(mapped, ConnectorAuthenticationFailedError)
        self.assertIn("Authentication failed", mapped.message)

    def test_permission_denied_mapping(self) -> None:
        """Verify error code 1044 / 1142 maps to ConnectorPermissionDeniedError."""
        exc = pymysql.err.OperationalError(
            1044, "Access denied for user 'user'@'%' to database 'production'"
        )
        mapped = map_mysql_family_error(exc, database="production", host="db.local")
        self.assertIsInstance(mapped, ConnectorPermissionDeniedError)
        self.assertEqual(mapped.details["error_code"], 1044)

    def test_connection_unavailable_mapping(self) -> None:
        """Verify error code 2003 / 2002 maps to ConnectorUnavailableError."""
        exc = pymysql.err.OperationalError(
            2003, "Can't connect to MySQL server on '10.0.0.5' (timed out)"
        )
        mapped = map_mysql_family_error(exc, database="mydb", host="10.0.0.5")
        self.assertIsInstance(mapped, ConnectorUnavailableError)

    def test_tls_failure_mapping(self) -> None:
        """Verify error code 2026 maps to ConnectorTLSError."""
        exc = pymysql.err.OperationalError(2026, "SSL connection error: certificate verify failed")
        mapped = map_mysql_family_error(exc, database="mydb", host="db.secure")
        self.assertIsInstance(mapped, ConnectorTLSError)

    def test_query_timeout_mapping(self) -> None:
        """Verify error code 3024 and asyncio.TimeoutError map to ConnectorTimeoutError."""
        exc = pymysql.err.OperationalError(
            3024, "Query execution was interrupted, max_statement_time exceeded"
        )
        mapped = map_mysql_family_error(exc, database="mydb")
        self.assertIsInstance(mapped, ConnectorTimeoutError)

        timeout_exc = TimeoutError()
        mapped_timeout = map_mysql_family_error(timeout_exc, database="mydb")
        self.assertIsInstance(mapped_timeout, ConnectorTimeoutError)

    def test_query_interrupted_cancelled_mapping(self) -> None:
        """Verify error code 1317 maps to ConnectorCancelledError."""
        exc = pymysql.err.OperationalError(1317, "Query execution was interrupted")
        mapped = map_mysql_family_error(exc, database="mydb")
        self.assertIsInstance(mapped, ConnectorCancelledError)

    def test_generic_error_mapping(self) -> None:
        """Verify generic runtime errors map to ConnectorMetadataError."""
        exc = ValueError("Unexpected internal catalog format")
        mapped = map_mysql_family_error(exc, database="mydb")
        self.assertIsInstance(mapped, ConnectorMetadataError)
