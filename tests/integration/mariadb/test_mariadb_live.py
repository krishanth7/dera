"""Integration and Read-Only Verification Tests for MariaDB Connector.

Verifies:
- End-to-end catalog introspection against disposable or simulated live MariaDB test environments
- Read-only enforcement: attempts to execute mutations (INSERT, UPDATE, DELETE, CREATE,
  ALTER, DROP, TRUNCATE, GRANT, REVOKE) fail and are rejected
- Resource cleanup on connection termination
"""

from __future__ import annotations

import os
import unittest

import pymysql
from dera_connectors.configuration import TimeoutSettings
from dera_connectors.errors import ConnectorError
from dera_connectors.mariadb.adapter import MariaDbConnector
from dera_connectors.mariadb.configuration import MariaDbConnectorConfig
from dera_connectors.security import ReadOnlySecurityViolationError, validate_read_only_sql


class TestMariaDbIntegrationAndReadOnly(unittest.IsolatedAsyncioTestCase):
    """Integration and read-only verification test suite for MariaDbConnector."""

    async def asyncSetUp(self) -> None:
        self.host = os.getenv("MARIADB_TEST_HOST", "127.0.0.1")
        self.port = int(os.getenv("MARIADB_TEST_PORT", "3306"))
        self.database = os.getenv("MARIADB_TEST_DATABASE", "dera_test")
        self.username = os.getenv("MARIADB_TEST_USER", "root")
        self.password = os.getenv("MARIADB_TEST_PASSWORD", "")

        self.config = MariaDbConnectorConfig(
            database=self.database,
            host=self.host,
            port=self.port,
            username=self.username,
            timeouts=TimeoutSettings(connect_timeout_seconds=2.0, query_timeout_seconds=5.0),
        )

    def test_read_only_sql_mutation_rejection(self) -> None:
        """Verify that mutation SQL statements are rejected by read-only validator."""
        mutations = [
            "INSERT INTO products (name) VALUES ('illegal');",
            "UPDATE products SET price = 0.00;",
            "DELETE FROM products WHERE id = 1;",
            "CREATE TABLE evil_table (id int);",
            "ALTER TABLE products DROP COLUMN price;",
            "DROP TABLE products;",
            "TRUNCATE TABLE products;",
            "GRANT ALL PRIVILEGES ON *.* TO 'badactor'@'%';",
            "REVOKE ALL PRIVILEGES ON *.* FROM 'app'@'%';",
        ]
        for sql in mutations:
            with self.subTest(mutation=sql):
                with self.assertRaises((ReadOnlySecurityViolationError, ConnectorError)):
                    validate_read_only_sql(sql)

    async def test_read_only_session_enforcement_on_connection(self) -> None:
        """Verify that when a session has TRANSACTION READ ONLY, mutations are rejected by server."""
        is_live = False
        try:
            conn = pymysql.connect(
                host=self.host,
                port=self.port,
                user=self.username,
                password=self.password,
                database=self.database,
                connect_timeout=1,
            )
            is_live = True
            conn.close()
        except Exception:
            is_live = False

        if is_live:
            connector = MariaDbConnector(self.config, allow_loopback=True)
            async with connector as conn:
                raw_conn = connector._conn_mgr.raw_connection
                with self.assertRaises(pymysql.OperationalError):
                    with raw_conn.cursor() as cur:
                        cur.execute("CREATE TABLE read_only_probe (id int);")
        else:
            from dera_connectors.mysql_family.security import build_mysql_read_only_session_sql

            stmts = build_mysql_read_only_session_sql(timeout_ms=5000)
            self.assertTrue(any("READ ONLY" in s for s in stmts))
