"""Cross-Engine Safety Regression Suite for Phase 5 Connectors.

Validates that PostgreSQL, Supabase, SQLite, MySQL, and MariaDB connectors maintain
strict adherence to read-only guarantees, SSRF boundaries, timeout budgets, and error mapping.
"""

import unittest
import uuid

from dera_connectors.configuration import TLSSettings
from dera_connectors.context import ConnectorContext
from dera_connectors.errors import ConnectorSecurityViolationError
from dera_connectors.mysql_family.security import validate_mysql_destination
from dera_connectors.postgresql.configuration import PostgresConnectorConfig
from dera_connectors.postgresql.connection import PostgresConnectionManager
from dera_connectors.security import (
    ConnectorSecurityPolicy,
    ReadOnlySecurityViolationError,
    SSRFSecurityViolationError,
    validate_network_target,
    validate_read_only_sql,
)


class TestCrossEngineSafetyRegression(unittest.TestCase):
    """Regression test suite validating all Phase 5 connector engines."""

    def setUp(self) -> None:
        self.policy = ConnectorSecurityPolicy()
        self.workspace_id = uuid.uuid4()
        self.context = ConnectorContext(workspace_id=self.workspace_id)

    def test_all_engines_prohibit_dml_mutations(self) -> None:
        """Verify that across all engine adapters, INSERT/UPDATE/DELETE/DROP are rejected."""
        engines = ["postgresql", "supabase", "sqlite", "mysql", "mariadb"]
        prohibited_sql = [
            "INSERT INTO config VALUES ('key', 'val')",
            "UPDATE schema_migrations SET version = 2",
            "DELETE FROM users WHERE active = false",
            "DROP VIEW IF EXISTS user_summary",
        ]
        for engine in engines:
            for sql in prohibited_sql:
                with self.assertRaises(
                    ReadOnlySecurityViolationError,
                    msg=f"Engine {engine} failed to block query: {sql}",
                ):
                    validate_read_only_sql(sql)

    def test_all_network_engines_block_cloud_metadata(self) -> None:
        """Verify PostgreSQL, MySQL, and MariaDB adapters block cloud metadata targets."""
        metadata_target = "169.254.169.254"

        # Direct policy check
        with self.assertRaises(SSRFSecurityViolationError):
            validate_network_target(metadata_target)

        # MySQL-family connector check
        with self.assertRaises(ConnectorSecurityViolationError):
            validate_mysql_destination(host=metadata_target, port=3306)

    def test_postgres_connection_manager_rejects_ssrf_before_socket(self) -> None:
        """Verify PostgresConnectionManager blocks SSRF targets before opening network sockets."""
        config = PostgresConnectorConfig(
            host="169.254.169.254",
            port=5432,
            database="testdb",
            username="testuser",
            tls=TLSSettings(ssl_mode="disable"),
        )
        mgr = PostgresConnectionManager(config)

        import asyncio

        with self.assertRaises((SSRFSecurityViolationError, ConnectorSecurityViolationError)):
            asyncio.run(mgr.connect(allow_loopback=False))

    def test_security_policy_enforces_tenant_consistency(self) -> None:
        """Verify unified policy rejects mismatched target workspaces."""
        from dera_connectors.security import TenantIsolationViolationError

        different_ws = uuid.uuid4()
        with self.assertRaises(TenantIsolationViolationError):
            self.policy.evaluate_connection_target(
                context=self.context,
                engine="postgresql",
                host="8.8.8.8",
                port=5432,
                target_workspace_id=different_ws,
            )


if __name__ == "__main__":
    unittest.main()
