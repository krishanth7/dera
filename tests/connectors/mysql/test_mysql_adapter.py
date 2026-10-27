"""Conformance and Unit Tests for MySqlConnector.

Verifies:
- MySqlConnector satisfies BaseConnectorConformanceTests
- Schema, table, column, constraint, index, view, and trigger catalog introspection
- Read-only session hardening and timeout handling
- Connection cancellation via CancellationToken
"""

from __future__ import annotations

import unittest
from typing import Any

from dera_connectors.configuration import ConnectorConfig
from dera_connectors.context import CancellationToken, ConnectorContext
from dera_connectors.errors import ConnectorCancelledError
from dera_connectors.lifecycle import ConnectionState
from dera_connectors.mysql.adapter import MySqlConnector
from dera_connectors.mysql.configuration import MySqlConnectorConfig
from dera_connectors.mysql_family.queries import (
    QUERY_CHECK_CONSTRAINTS_FALLBACK,
    QUERY_CHECK_CONSTRAINTS_MYSQL8,
    QUERY_COLUMNS,
    QUERY_FOREIGN_KEYS,
    QUERY_IDENTITY,
    QUERY_INDEXES,
    QUERY_INDEXES_MYSQL8,
    QUERY_PRIMARY_KEY,
    QUERY_SCHEMAS,
    QUERY_TABLES,
    QUERY_TRIGGERS,
    QUERY_UNIQUE_CONSTRAINTS,
    QUERY_VIEWS,
)
from dera_connectors.protocol import DatabaseConnector
from dera_connectors.testing.conformance import BaseConnectorConformanceTests


class MockMySqlConnectionManager:
    """Mock connection manager responding to MySQL 8.0 catalog queries with realistic fixture data."""

    def __init__(self, config: MySqlConnectorConfig) -> None:
        self._config = config
        self._connected = False

    @property
    def is_connected(self) -> bool:
        return self._connected

    async def connect(
        self,
        cancellation_token: CancellationToken | None = None,
        allow_loopback: bool = False,
    ) -> None:
        if cancellation_token and cancellation_token.is_cancelled:
            raise ConnectorCancelledError("Connection cancelled by user.")
        self._connected = True

    async def close(self) -> None:
        self._connected = False

    async def fetch(
        self,
        query: str,
        args: tuple[Any, ...] | list[Any] | None = None,
        cancellation_token: CancellationToken | None = None,
        timeout: float | None = None,
    ) -> list[dict[str, Any]]:
        if cancellation_token and cancellation_token.is_cancelled:
            raise ConnectorCancelledError("Query cancelled.")

        if query == QUERY_SCHEMAS:
            return [
                {
                    "schema_name": "analytics",
                    "character_set": "utf8mb4",
                    "collation_name": "utf8mb4_0900_ai_ci",
                },
                {
                    "schema_name": "testdb",
                    "character_set": "utf8mb4",
                    "collation_name": "utf8mb4_0900_ai_ci",
                },
            ]
        elif query == QUERY_TABLES:
            return [
                {
                    "schema_name": "testdb",
                    "table_name": "orders",
                    "object_type": "BASE TABLE",
                    "storage_engine": "InnoDB",
                    "comment": "Customer orders",
                    "collation_name": "utf8mb4_0900_ai_ci",
                    "auto_increment_val": 100,
                },
                {
                    "schema_name": "testdb",
                    "table_name": "users",
                    "object_type": "BASE TABLE",
                    "storage_engine": "InnoDB",
                    "comment": "User accounts",
                    "collation_name": "utf8mb4_0900_ai_ci",
                    "auto_increment_val": 50,
                },
            ]
        elif query == QUERY_COLUMNS:
            table = args[1] if args and len(args) > 1 else ""
            if table == "users":
                return [
                    {
                        "schema_name": "testdb",
                        "table_name": "users",
                        "column_name": "id",
                        "ordinal_position": 1,
                        "data_type": "bigint",
                        "column_type": "bigint unsigned",
                        "is_nullable": "NO",
                        "default_expression": None,
                        "extra": "auto_increment",
                        "generation_expression": None,
                        "character_set": None,
                        "collation_name": None,
                        "comment": "Primary identifier",
                    },
                    {
                        "schema_name": "testdb",
                        "table_name": "users",
                        "column_name": "username",
                        "ordinal_position": 2,
                        "data_type": "varchar",
                        "column_type": "varchar(64)",
                        "is_nullable": "NO",
                        "default_expression": None,
                        "extra": "",
                        "generation_expression": None,
                        "character_set": "utf8mb4",
                        "collation_name": "utf8mb4_0900_ai_ci",
                        "comment": "Unique login handle",
                    },
                    {
                        "schema_name": "testdb",
                        "table_name": "users",
                        "column_name": "email",
                        "ordinal_position": 3,
                        "data_type": "varchar",
                        "column_type": "varchar(255)",
                        "is_nullable": "YES",
                        "default_expression": None,
                        "extra": "",
                        "generation_expression": None,
                        "character_set": "utf8mb4",
                        "collation_name": "utf8mb4_0900_ai_ci",
                        "comment": None,
                    },
                    {
                        "schema_name": "testdb",
                        "table_name": "users",
                        "column_name": "upper_username",
                        "ordinal_position": 4,
                        "data_type": "varchar",
                        "column_type": "varchar(64)",
                        "is_nullable": "YES",
                        "default_expression": None,
                        "extra": "STORED GENERATED",
                        "generation_expression": "upper(`username`)",
                        "character_set": "utf8mb4",
                        "collation_name": "utf8mb4_0900_ai_ci",
                        "comment": "Stored uppercase username",
                    },
                ]
            elif table == "orders":
                return [
                    {
                        "schema_name": "testdb",
                        "table_name": "orders",
                        "column_name": "order_id",
                        "ordinal_position": 1,
                        "data_type": "bigint",
                        "column_type": "bigint",
                        "is_nullable": "NO",
                        "default_expression": None,
                        "extra": "auto_increment",
                        "generation_expression": None,
                        "character_set": None,
                        "collation_name": None,
                        "comment": None,
                    },
                    {
                        "schema_name": "testdb",
                        "table_name": "orders",
                        "column_name": "user_id",
                        "ordinal_position": 2,
                        "data_type": "bigint",
                        "column_type": "bigint unsigned",
                        "is_nullable": "NO",
                        "default_expression": None,
                        "extra": "",
                        "generation_expression": None,
                        "character_set": None,
                        "collation_name": None,
                        "comment": None,
                    },
                    {
                        "schema_name": "testdb",
                        "table_name": "orders",
                        "column_name": "amount",
                        "ordinal_position": 3,
                        "data_type": "decimal",
                        "column_type": "decimal(10,2)",
                        "is_nullable": "NO",
                        "default_expression": "0.00",
                        "extra": "",
                        "generation_expression": None,
                        "character_set": None,
                        "collation_name": None,
                        "comment": None,
                    },
                ]
            return []
        elif query == QUERY_PRIMARY_KEY:
            table = args[1] if args and len(args) > 1 else ""
            if table == "users":
                return [{"column_name": "id", "ordinal_position": 1}]
            elif table == "orders":
                return [{"column_name": "order_id", "ordinal_position": 1}]
            return []
        elif query == QUERY_FOREIGN_KEYS:
            table = args[1] if args and len(args) > 1 else ""
            if table == "orders":
                return [
                    {
                        "constraint_name": "fk_orders_user_id",
                        "schema_name": "testdb",
                        "table_name": "orders",
                        "column_name": "user_id",
                        "referenced_schema": "testdb",
                        "referenced_table": "users",
                        "referenced_column": "id",
                        "update_rule": "CASCADE",
                        "delete_rule": "RESTRICT",
                    }
                ]
            return []
        elif query == QUERY_UNIQUE_CONSTRAINTS:
            table = args[1] if args and len(args) > 1 else ""
            if table == "users":
                return [
                    {
                        "constraint_name": "uq_users_email",
                        "column_name": "email",
                    }
                ]
            return []
        elif query in (QUERY_CHECK_CONSTRAINTS_MYSQL8, QUERY_CHECK_CONSTRAINTS_FALLBACK):
            table = args[1] if args and len(args) > 1 else ""
            if table == "orders":
                return [
                    {
                        "constraint_name": "chk_orders_amount_positive",
                        "check_clause": "(`amount` > 0)",
                    }
                ]
            return []
        elif query in (QUERY_INDEXES_MYSQL8, QUERY_INDEXES):
            table = args[1] if args and len(args) > 1 else ""
            if table == "users":
                return [
                    {
                        "index_name": "PRIMARY",
                        "non_unique": 0,
                        "seq_in_index": 1,
                        "column_name": "id",
                        "index_type": "BTREE",
                        "sub_part": None,
                        "collation": "A",
                        "expression": None,
                        "is_visible": "YES",
                        "comment": "",
                    },
                    {
                        "index_name": "idx_upper_username",
                        "non_unique": 1,
                        "seq_in_index": 1,
                        "column_name": None,
                        "index_type": "BTREE",
                        "sub_part": None,
                        "collation": "A",
                        "expression": "upper(`username`)",
                        "is_visible": "YES",
                        "comment": "Functional index",
                    },
                ]
            elif table == "orders":
                return [
                    {
                        "index_name": "PRIMARY",
                        "non_unique": 0,
                        "seq_in_index": 1,
                        "column_name": "order_id",
                        "index_type": "BTREE",
                        "sub_part": None,
                        "collation": "A",
                        "expression": None,
                        "is_visible": "YES",
                        "comment": "",
                    },
                    {
                        "index_name": "idx_orders_user_id",
                        "non_unique": 1,
                        "seq_in_index": 1,
                        "column_name": "user_id",
                        "index_type": "BTREE",
                        "sub_part": None,
                        "collation": "A",
                        "expression": None,
                        "is_visible": "YES",
                        "comment": "",
                    },
                ]
            return []
        elif query == QUERY_VIEWS:
            return [
                {
                    "schema_name": "testdb",
                    "view_name": "user_order_summary",
                    "view_definition": "select `u`.`username` AS `username`,count(`o`.`order_id`) AS `total_orders` from (`testdb`.`users` `u` left join `testdb`.`orders` `o` on((`u`.`id` = `o`.`user_id`))) group by `u`.`username`",
                    "check_option": "NONE",
                    "is_updatable": "NO",
                    "definer": "root@localhost",
                    "security_type": "DEFINER",
                }
            ]
        elif query == QUERY_TRIGGERS:
            return [
                {
                    "schema_name": "testdb",
                    "trigger_name": "trg_orders_audit",
                    "event_manipulation": "INSERT",
                    "table_name": "orders",
                    "action_timing": "AFTER",
                    "action_statement": "BEGIN SELECT 1; END",
                    "definer": "root@localhost",
                }
            ]
        return []

    async def fetchrow(
        self,
        query: str,
        args: tuple[Any, ...] | list[Any] | None = None,
        cancellation_token: CancellationToken | None = None,
        timeout: float | None = None,
    ) -> dict[str, Any] | None:
        if cancellation_token and cancellation_token.is_cancelled:
            raise ConnectorCancelledError("Query cancelled.")

        if "SELECT 1 AS probe" in query:
            return {"probe": 1, "ver": "8.0.36"}
        elif query == QUERY_IDENTITY:
            return {
                "server_version": "8.0.36",
                "version_comment": "MySQL Community Server - GPL",
                "current_database": "testdb",
                "current_user": "analyst@localhost",
            }
        return None


class TestMySqlAdapter(BaseConnectorConformanceTests, unittest.IsolatedAsyncioTestCase):
    """Run full Phase 5.1 connector conformance suite against MySqlConnector."""

    def create_valid_config(self) -> MySqlConnectorConfig:
        return MySqlConnectorConfig(
            database="testdb",
            host="mysql.internal",
            port=3306,
        )

    def create_connector(
        self,
        config: ConnectorConfig | None = None,
        context: ConnectorContext | None = None,
    ) -> DatabaseConnector:
        cfg = config or self.create_valid_config()
        if not isinstance(cfg, MySqlConnectorConfig):
            cfg = MySqlConnectorConfig(
                database=cfg.database,
                host=cfg.host,
                port=cfg.port or 3306,
            )
        ctx = context or self.create_valid_context()
        mock_mgr = MockMySqlConnectionManager(cfg)
        return MySqlConnector(
            config=cfg,
            context=ctx,
            allow_loopback=True,
            connection_manager=mock_mgr,
        )

    async def test_mysql_specific_catalog_inspection(self) -> None:
        """Verify detailed MySQL catalog inspection for functional indexes, views, and generated columns."""
        async with self.create_connector() as conn:
            # Schemas
            schemas = await conn.list_schemas()
            self.assertEqual(len(schemas), 2)
            self.assertEqual([s.schema_name for s in schemas], ["analytics", "testdb"])

            # Tables
            tables = await conn.list_tables()
            self.assertEqual(len(tables), 2)
            self.assertEqual([t.table_name for t in tables], ["orders", "users"])

            # Columns
            user_cols = await conn.list_columns("testdb", "users")
            self.assertEqual(len(user_cols), 4)
            self.assertTrue(user_cols[0].is_identity)
            self.assertEqual(user_cols[0].engine_specific["is_unsigned"], True)
            self.assertTrue(user_cols[3].is_generated)
            self.assertEqual(user_cols[3].generation_expression, "upper(`username`)")

            # Primary Key
            pk = await conn.get_primary_key("testdb", "users")
            self.assertIsNotNone(pk)
            self.assertEqual(pk.column_names, ["id"])

            # Foreign Keys
            fks = await conn.list_foreign_keys("testdb", "orders")
            self.assertEqual(len(fks), 1)
            self.assertEqual(fks[0].constraint_name, "fk_orders_user_id")
            self.assertEqual(fks[0].column_names, ["user_id"])
            self.assertEqual(fks[0].referenced_table, "users")

            # Unique Constraints
            uqs = await conn.list_unique_constraints("testdb", "users")
            self.assertEqual(len(uqs), 1)
            self.assertEqual(uqs[0].column_names, ["email"])

            # Check Constraints
            checks = await conn.list_check_constraints("testdb", "orders")
            self.assertEqual(len(checks), 1)
            self.assertEqual(checks[0].constraint_name, "chk_orders_amount_positive")

            # Indexes (including functional expression index)
            indexes = await conn.list_indexes("testdb", "users")
            self.assertEqual(len(indexes), 2)
            idx_names = [i.index_name for i in indexes]
            self.assertIn("PRIMARY", idx_names)
            self.assertIn("idx_upper_username", idx_names)
            func_idx = next(i for i in indexes if i.index_name == "idx_upper_username")
            self.assertIn("upper(`username`)", func_idx.column_names)

            # Views
            views = await conn.list_views("testdb")
            self.assertEqual(len(views), 1)
            self.assertEqual(views[0].view_name, "user_order_summary")
            self.assertIn("left join", views[0].view_definition.lower())

            # Triggers
            triggers = await conn.list_triggers("orders", "testdb")
            self.assertEqual(len(triggers), 1)
            self.assertEqual(triggers[0].trigger_name, "trg_orders_audit")
            self.assertEqual(triggers[0].timing, "AFTER")
            self.assertEqual(triggers[0].event, "INSERT")

    async def test_connection_probe(self) -> None:
        """Verify test_connection returns success and latency without leaving connection open."""
        conn = self.create_connector()
        result = await conn.test_connection()
        self.assertTrue(result.success)
        self.assertGreaterEqual(result.latency_ms, 0.0)
        self.assertEqual(conn.state, ConnectionState.CLOSED)
