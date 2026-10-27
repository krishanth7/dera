"""Conformance and adapter unit tests for SqliteConnector.

Verifies that SqliteConnector satisfies BaseConnectorConformanceTests and Phase 5.1 standards.
"""

from __future__ import annotations

import os
import sqlite3
import tempfile
import unittest

from dera_connectors.configuration import ConnectorConfig
from dera_connectors.context import ConnectorContext
from dera_connectors.protocol import DatabaseConnector
from dera_connectors.sqlite.adapter import SqliteConnector
from dera_connectors.sqlite.configuration import SqliteConnectorConfig
from dera_connectors.testing.conformance import BaseConnectorConformanceTests


class TestSqliteAdapterConformance(BaseConnectorConformanceTests, unittest.IsolatedAsyncioTestCase):
    """Run full Phase 5.1 connector conformance suite against SqliteConnector."""

    @classmethod
    def setUpClass(cls) -> None:
        """Create a disposable SQLite database file with representative objects."""
        cls.temp_dir = tempfile.TemporaryDirectory()
        cls.db_path = os.path.join(cls.temp_dir.name, "conformance_test.db")

        # Initialize test schema
        conn = sqlite3.connect(cls.db_path)
        cur = conn.cursor()
        cur.executescript(
            """
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                email TEXT UNIQUE,
                bio TEXT DEFAULT 'Hello'
            );

            CREATE TABLE orders (
                order_id INTEGER PRIMARY KEY,
                user_id INTEGER,
                amount REAL NOT NULL,
                status TEXT CHECK (status IN ('pending', 'completed', 'cancelled')),
                FOREIGN KEY (user_id) REFERENCES users(id) ON UPDATE CASCADE ON DELETE RESTRICT
            );

            CREATE INDEX idx_orders_user ON orders(user_id);

            CREATE VIEW user_order_summary AS
            SELECT u.username, count(o.order_id) as total_orders
            FROM users u LEFT JOIN orders o ON u.id = o.user_id
            GROUP BY u.username;

            CREATE TRIGGER trg_user_order_insert
            AFTER INSERT ON orders
            BEGIN
                SELECT 1;
            END;
            """
        )
        conn.commit()
        conn.close()

    @classmethod
    def tearDownClass(cls) -> None:
        """Clean up disposable test directory."""
        cls.temp_dir.cleanup()

    def create_valid_config(self) -> SqliteConnectorConfig:
        """Provide a valid test configuration pointing to the approved test database."""
        return SqliteConnectorConfig(
            database=self.db_path,
            approved_storage_roots=[self.temp_dir.name],
            allow_memory_databases=False,
        )

    def create_connector(
        self,
        config: ConnectorConfig | None = None,
        context: ConnectorContext | None = None,
    ) -> DatabaseConnector:
        """Construct an unconnected SqliteConnector instance for testing."""
        cfg = config or self.create_valid_config()
        ctx = context or self.create_valid_context()
        if not isinstance(cfg, SqliteConnectorConfig):
            cfg = SqliteConnectorConfig(
                database=cfg.database,
                approved_storage_roots=[self.temp_dir.name],
            )
        return SqliteConnector(config=cfg, context=ctx)

    async def test_test_connection_probe(self) -> None:
        """Verify test_connection lightweight probe returns ConnectionTestResult."""
        connector = self.create_connector()
        result = await connector.test_connection()
        self.assertTrue(result.success)
        self.assertIsNotNone(result.identity)
        self.assertGreaterEqual(result.latency_ms, 0.0)
        self.assertIn("3.", result.identity.server_version if result.identity else "")
        await connector.close()

    async def test_foreign_keys_introspection(self) -> None:
        """Verify foreign key discovery on orders table."""
        async with self.create_connector() as conn:
            fks = await conn.list_foreign_keys("main", "orders")
            self.assertEqual(len(fks), 1)
            fk = fks[0]
            self.assertEqual(fk.table_name, "orders")
            self.assertEqual(fk.column_names, ["user_id"])
            self.assertEqual(fk.referenced_table, "users")
            self.assertEqual(fk.referenced_columns, ["id"])
            self.assertEqual(fk.on_update, "CASCADE")
            self.assertEqual(fk.on_delete, "RESTRICT")

    async def test_unique_constraints_introspection(self) -> None:
        """Verify unique constraint discovery on users table."""
        async with self.create_connector() as conn:
            uqs = await conn.list_unique_constraints("main", "users")
            self.assertGreaterEqual(len(uqs), 1)
            emails = [u for u in uqs if "email" in u.column_names]
            self.assertEqual(len(emails), 1)

    async def test_check_constraints_introspection(self) -> None:
        """Verify check constraint extraction from orders table DDL."""
        async with self.create_connector() as conn:
            checks = await conn.list_check_constraints("main", "orders")
            self.assertEqual(len(checks), 1)
            self.assertIn("status IN", checks[0].check_clause)

    async def test_indexes_introspection(self) -> None:
        """Verify secondary index discovery on orders table."""
        async with self.create_connector() as conn:
            idxs = await conn.list_indexes("main", "orders")
            idx_names = [i.index_name for i in idxs]
            self.assertIn("idx_orders_user", idx_names)

    async def test_views_introspection(self) -> None:
        """Verify view discovery without executing view query."""
        async with self.create_connector() as conn:
            views = await conn.list_views("main")
            view_names = [v.view_name for v in views]
            self.assertIn("user_order_summary", view_names)

    async def test_triggers_introspection(self) -> None:
        """Verify trigger discovery without invoking trigger body."""
        async with self.create_connector() as conn:
            triggers = await conn.list_triggers("orders", "main")
            self.assertEqual(len(triggers), 1)
            self.assertEqual(triggers[0].trigger_name, "trg_user_order_insert")
            self.assertEqual(triggers[0].table_name, "orders")
