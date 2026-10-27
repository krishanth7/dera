"""Security qualification tests for PostgreSQL connector."""

import unittest
from unittest.mock import AsyncMock, patch

from dera_connectors.postgresql.adapter import PostgresConnector
from dera_connectors.postgresql.configuration import PostgresConnectorConfig
from dera_connectors.postgresql.connection import (
    PostgresConnectionManager,
)
from dera_connectors.security import (
    ReadOnlySecurityViolationError,
    SSRFSecurityViolationError,
    sanitize_diagnostics,
    validate_read_only_sql,
)


class TestPostgresSecurity(unittest.IsolatedAsyncioTestCase):
    """Verify security controls, SSRF protections, and read-only invariants."""

    def test_ssrf_blocks_cloud_metadata_service(self) -> None:
        """Verify AWS/GCP/Azure link-local metadata IP 169.254.169.254 is blocked."""
        config = PostgresConnectorConfig(
            database="postgres",
            host="169.254.169.254",
            port=5432,
        )
        conn = PostgresConnector(config=config, allow_loopback=False)
        with self.assertRaises(SSRFSecurityViolationError):
            # Attempting connect must immediately fail SSRF pre-flight validation
            import asyncio

            asyncio.run(conn.connect())

    def test_ssrf_blocks_loopback_by_default(self) -> None:
        """Verify loopback 127.0.0.1 is blocked when allow_loopback=False."""
        config = PostgresConnectorConfig(
            database="postgres",
            host="127.0.0.1",
            port=5432,
        )
        conn = PostgresConnector(config=config, allow_loopback=False)
        with self.assertRaises(SSRFSecurityViolationError):
            import asyncio

            asyncio.run(conn.connect())

    async def test_session_read_only_lock_applied_on_connect(self) -> None:
        """Verify SET SESSION CHARACTERISTICS AS TRANSACTION READ ONLY is executed."""
        config = PostgresConnectorConfig(
            database="test_db",
            host="postgres.internal",
            port=5432,
            statement_timeout_ms=15000,
        )
        conn_mgr = PostgresConnectionManager(config)

        mock_asyncpg_conn = AsyncMock()
        mock_asyncpg_conn.is_closed.return_value = False
        with (
            patch("dera_connectors.postgresql.connection.validate_network_target"),
            patch("asyncpg.connect", return_value=mock_asyncpg_conn),
        ):
            await conn_mgr.connect(allow_loopback=True)

            # Check that read-only transaction command and statement_timeout were executed
            calls = [c.args[0] for c in mock_asyncpg_conn.execute.call_args_list]
            self.assertIn("SET SESSION CHARACTERISTICS AS TRANSACTION READ ONLY;", calls)
            self.assertIn("SET statement_timeout = 15000;", calls)

            await conn_mgr.close()

    def test_mutation_statements_rejected_by_query_validator(self) -> None:
        """Verify SQL mutation statements (INSERT, UPDATE, DELETE, DROP, etc.) are rejected."""
        mutations = [
            "INSERT INTO users (name) VALUES ('hacker');",
            "UPDATE accounts SET balance = 0;",
            "DELETE FROM logs WHERE true;",
            "DROP TABLE users CASCADE;",
            "ALTER TABLE users ADD COLUMN compromised boolean;",
            "TRUNCATE TABLE audit_log;",
            "CREATE TABLE backdoors (id serial);",
        ]
        for sql in mutations:
            with self.assertRaises(ReadOnlySecurityViolationError):
                validate_read_only_sql(sql)

    def test_credential_scrubbing_in_diagnostics(self) -> None:
        """Verify passwords and sensitive fields are scrubbed from diagnostic dictionaries."""
        raw_info = {
            "database": "prod_db",
            "username": "admin",
            "password": "cleartext_secret_123",
            "connection_string": "postgresql://admin:secret_pass@db.example.com/db",
            "auth_token": "bearer_secret_xyz",
        }
        sanitized = sanitize_diagnostics(raw_info)
        self.assertEqual(sanitized["password"], "***")
        self.assertNotIn("secret_pass", sanitized["connection_string"])
        self.assertEqual(sanitized["auth_token"], "***")


if __name__ == "__main__":
    unittest.main()
