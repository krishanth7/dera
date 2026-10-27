"""Security and Safety Tests for DERA Connector Foundation.

Validates:
- Read-only SQL query validation and mutation rejection
- SSRF target validation, blocking cloud metadata endpoints and private networks
- Credential masking and diagnostics sanitization
"""

import unittest

from dera_connectors.security import (
    ReadOnlySecurityViolationError,
    SSRFSecurityViolationError,
    mask_sensitive_strings,
    sanitize_diagnostics,
    validate_network_target,
    validate_read_only_sql,
)


class TestConnectorSecurity(unittest.TestCase):
    """Test suite verifying security invariants for the connector layer."""

    def test_validate_read_only_sql_permits_safe_queries(self) -> None:
        """Verify standard introspection SELECT queries are permitted."""
        safe_queries = [
            "SELECT table_name, table_schema FROM information_schema.tables WHERE table_schema = 'public'",
            "SELECT column_name, data_type, is_nullable FROM information_schema.columns",
            "SELECT name, sql FROM sqlite_master WHERE type = 'table'",
            "SHOW TABLES",
            "DESCRIBE users",
        ]
        for query in safe_queries:
            try:
                validate_read_only_sql(query)
            except ReadOnlySecurityViolationError:
                self.fail(f"Legitimate query '{query}' was incorrectly rejected as mutation.")

    def test_validate_read_only_sql_rejects_mutations(self) -> None:
        """Verify DDL and DML statements raise ReadOnlySecurityViolationError."""
        mutation_queries = [
            "DROP TABLE users;",
            "TRUNCATE TABLE audit_logs;",
            "ALTER TABLE orders ADD COLUMN test INT;",
            "CREATE TABLE injected (id INT);",
            "INSERT INTO users (id, email) VALUES (1, 'bad@evil.com');",
            "UPDATE accounts SET balance = 1000000;",
            "DELETE FROM orders WHERE id = 1;",
            "GRANT ALL PRIVILEGES ON DATABASE prod TO evil;",
            "REVOKE SELECT ON users FROM analyst;",
            "EXECUTE sp_delete_customer;",
            "REPLACE INTO settings VALUES ('key', 'val');",
        ]
        for query in mutation_queries:
            with self.assertRaises(
                ReadOnlySecurityViolationError,
                msg=f"Mutation query '{query}' was not blocked by read-only validator.",
            ):
                validate_read_only_sql(query)

    def test_ssrf_validation_blocks_cloud_metadata_and_loopback(self) -> None:
        """Verify known cloud metadata endpoints and loopback addresses are blocked unconditionally."""
        blocked_targets = [
            "localhost",
            "metadata.google.internal",
            "metadata.google",
            "169.254.169.254",  # AWS / GCP metadata
            "127.0.0.1",
            "::1",
        ]
        for host in blocked_targets:
            with self.assertRaises(
                SSRFSecurityViolationError,
                msg=f"Target '{host}' was not blocked by SSRF policy.",
            ):
                validate_network_target(host, allow_private_networks=True)

    def test_ssrf_validation_blocks_private_networks_by_default(self) -> None:
        """Verify RFC 1918 private IPs are blocked when allow_private_networks=False."""
        private_ips = [
            "10.0.0.5",
            "172.16.10.20",
            "192.168.1.100",
        ]
        for ip in private_ips:
            with self.assertRaises(
                SSRFSecurityViolationError,
                msg=f"Private IP '{ip}' was not blocked when allow_private_networks=False.",
            ):
                validate_network_target(ip, allow_private_networks=False)

        # Public IPs should pass
        try:
            validate_network_target("8.8.8.8", allow_private_networks=False)
            validate_network_target("1.1.1.1", allow_private_networks=False)
        except SSRFSecurityViolationError:
            self.fail("Public IP was incorrectly rejected by SSRF validator.")

    def test_mask_sensitive_strings_scrubs_secrets(self) -> None:
        """Verify credentials and URIs are stripped of cleartext passwords."""
        sample_uri = "postgresql://dbuser:ConfidentialPassword123@db.prod.internal:5432/main"
        masked = mask_sensitive_strings(sample_uri)
        self.assertNotIn("ConfidentialPassword123", masked)
        self.assertIn("postgresql://dbuser:***@db.prod.internal:5432/main", masked)

        sample_kv = "User connection failed: password = 'super_secret_token_abc' on host"
        masked_kv = mask_sensitive_strings(sample_kv)
        self.assertNotIn("super_secret_token_abc", masked_kv)
        self.assertIn("password=***", masked_kv)

    def test_sanitize_diagnostics_scrubs_nested_dicts(self) -> None:
        """Verify recursive dictionary scrubbing of sensitive keys."""
        diagnostics = {
            "driver": "asyncpg",
            "host": "postgres.internal",
            "database": "primary",
            "credentials": {
                "username": "svc_dera",
                "password": "CleartextPassword!",
                "api_key": "secret-key-xyz",
            },
            "token": "top-secret-token",
        }
        sanitized = sanitize_diagnostics(diagnostics)

        self.assertEqual(sanitized["driver"], "asyncpg")
        self.assertEqual(sanitized["credentials"]["username"], "svc_dera")
        self.assertEqual(sanitized["credentials"]["password"], "***")
        self.assertEqual(sanitized["credentials"]["api_key"], "***")
        self.assertEqual(sanitized["token"], "***")
