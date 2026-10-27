"""Unit Tests for DERA MySQL-Family Security & Isolation Policies.

Validates:
- SSRF prevention, cloud metadata endpoint blocking, and network restrictions
- TLS SSLContext construction across ssl_mode options
- Read-only session hardening statements
"""

import ssl
import unittest

from dera_connectors.configuration import TLSSettings
from dera_connectors.errors import (
    ConnectorSecurityViolationError,
)
from dera_connectors.mysql_family.security import (
    build_mysql_read_only_session_sql,
    build_mysql_ssl_context,
    validate_mysql_destination,
)


class TestMySqlFamilySecurity(unittest.TestCase):
    """Test suite validating network boundaries, TLS configuration, and read-only sessions."""

    def test_cloud_metadata_destination_blocked(self) -> None:
        """Verify connections to AWS/GCP cloud metadata IP 169.254.169.254 are strictly rejected."""
        with self.assertRaises(ConnectorSecurityViolationError):
            validate_mysql_destination(host="169.254.169.254", port=3306)

    def test_loopback_destination_blocked_by_default(self) -> None:
        """Verify localhost/127.0.0.1 is rejected unless explicitly authorized."""
        with self.assertRaises(ConnectorSecurityViolationError):
            validate_mysql_destination(host="127.0.0.1", port=3306, allow_loopback=False)

    def test_loopback_destination_permitted_when_explicitly_allowed(self) -> None:
        """Verify localhost is permitted for local integration testing when allow_loopback=True."""
        validate_mysql_destination(host="127.0.0.1", port=3306, allow_loopback=True)

    def test_invalid_ports_rejected(self) -> None:
        """Verify privileged system ports or out-of-range ports are rejected."""
        with self.assertRaises(ConnectorSecurityViolationError):
            validate_mysql_destination(host="db.example.com", port=0)

        with self.assertRaises(ConnectorSecurityViolationError):
            validate_mysql_destination(host="db.example.com", port=70000)

    def test_ssl_context_mode_disable(self) -> None:
        """Verify ssl_mode='disable' returns None."""
        tls = TLSSettings(ssl_mode="disable")
        ctx = build_mysql_ssl_context(tls)
        self.assertIsNone(ctx)

    def test_ssl_context_mode_require(self) -> None:
        """Verify ssl_mode='require' produces an SSLContext with CERT_NONE."""
        tls = TLSSettings(ssl_mode="require")
        ctx = build_mysql_ssl_context(tls)
        self.assertIsNotNone(ctx)
        self.assertIsInstance(ctx, ssl.SSLContext)
        self.assertEqual(ctx.verify_mode, ssl.CERT_NONE)
        self.assertFalse(ctx.check_hostname)

    def test_ssl_context_mode_verify_ca(self) -> None:
        """Verify ssl_mode='verify-ca' produces an SSLContext with CERT_REQUIRED and check_hostname=False."""
        tls = TLSSettings(ssl_mode="verify-ca")
        ctx = build_mysql_ssl_context(tls)
        self.assertIsNotNone(ctx)
        self.assertEqual(ctx.verify_mode, ssl.CERT_REQUIRED)
        self.assertFalse(ctx.check_hostname)

    def test_ssl_context_mode_verify_full(self) -> None:
        """Verify ssl_mode='verify-full' enforces CERT_REQUIRED and hostname checking."""
        tls = TLSSettings(ssl_mode="verify-full", verify_hostname=True)
        ctx = build_mysql_ssl_context(tls)
        self.assertIsNotNone(ctx)
        self.assertEqual(ctx.verify_mode, ssl.CERT_REQUIRED)
        self.assertTrue(ctx.check_hostname)

    def test_read_only_session_hardening_sql(self) -> None:
        """Verify session hardening statements contain read-only, timeout, and safe update controls."""
        stmts = build_mysql_read_only_session_sql(timeout_ms=15000)
        self.assertGreaterEqual(len(stmts), 3)

        sql_concat = " ".join(stmts)
        self.assertIn("SET SESSION TRANSACTION READ ONLY;", sql_concat)
        self.assertIn("15000", sql_concat)
        self.assertIn("SET SESSION sql_safe_updates = 1;", sql_concat)
