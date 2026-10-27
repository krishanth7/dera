"""Conformance and Unit Tests for MariaDbConnector.

Verifies:
- MariaDbConnector satisfies BaseConnectorConformanceTests
- Engine detection accurately identifies MariaDB instead of generic MySQL
- MariaDB-specific catalog queries, check constraints, Aria/InnoDB storage engines
- Connection lifecycle, probe test, and error handling
"""

from __future__ import annotations

import unittest
from typing import Any

from dera_connectors.configuration import ConnectorConfig
from dera_connectors.context import CancellationToken, ConnectorContext
from dera_connectors.engine import DatabaseEngine
from dera_connectors.errors import ConnectorCancelledError
from dera_connectors.lifecycle import ConnectionState
from dera_connectors.mariadb.adapter import MariaDbConnector
from dera_connectors.mariadb.configuration import MariaDbConnectorConfig
from dera_connectors.mysql_family.queries import (
    QUERY_CHECK_CONSTRAINTS_FALLBACK,
    QUERY_COLUMNS,
    QUERY_FOREIGN_KEYS,
    QUERY_IDENTITY,
    QUERY_INDEXES,
    QUERY_PRIMARY_KEY,
    QUERY_SCHEMAS,
    QUERY_TABLES,
    QUERY_TRIGGERS,
    QUERY_UNIQUE_CONSTRAINTS,
    QUERY_VIEWS,
)
from dera_connectors.protocol import DatabaseConnector
from dera_connectors.testing.conformance import BaseConnectorConformanceTests


class MockMariaDbConnectionManager:
    """Mock connection manager responding to MariaDB 10.11+ catalog queries."""

    def __init__(self, config: MariaDbConnectorConfig) -> None:
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
                    "schema_name": "inventory",
                    "character_set": "utf8mb4",
                    "collation_name": "utf8mb4_unicode_ci",
                },
                {
                    "schema_name": "tenant_1",
                    "character_set": "utf8mb4",
                    "collation_name": "utf8mb4_unicode_ci",
                },
            ]
        elif query == QUERY_TABLES:
            return [
                {
                    "schema_name": "inventory",
                    "table_name": "products",
                    "object_type": "BASE TABLE",
                    "storage_engine": "Aria",
                    "comment": "Product catalog",
                    "collation_name": "utf8mb4_unicode_ci",
                    "auto_increment_val": 10,
                },
                {
                    "schema_name": "inventory",
                    "table_name": "stock",
                    "object_type": "BASE TABLE",
                    "storage_engine": "InnoDB",
                    "comment": "Inventory levels",
                    "collation_name": "utf8mb4_unicode_ci",
                    "auto_increment_val": 100,
                },
            ]
        elif query == QUERY_COLUMNS:
            table = args[1] if args and len(args) > 1 else ""
            if table == "products":
                return [
                    {
                        "schema_name": "inventory",
                        "table_name": "products",
                        "column_name": "sku",
                        "ordinal_position": 1,
                        "data_type": "varchar",
                        "column_type": "varchar(32)",
                        "is_nullable": "NO",
                        "default_expression": None,
                        "extra": "",
                        "generation_expression": None,
                        "character_set": "utf8mb4",
                        "collation_name": "utf8mb4_unicode_ci",
                        "comment": "Stock Keeping Unit",
                    },
                    {
                        "schema_name": "inventory",
                        "table_name": "products",
                        "column_name": "price",
                        "ordinal_position": 2,
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
                    {
                        "schema_name": "inventory",
                        "table_name": "products",
                        "column_name": "price_with_tax",
                        "ordinal_position": 3,
                        "data_type": "decimal",
                        "column_type": "decimal(10,2)",
                        "is_nullable": "YES",
                        "default_expression": None,
                        "extra": "PERSISTENT GENERATED",
                        "generation_expression": "`price` * 1.20",
                        "character_set": None,
                        "collation_name": None,
                        "comment": "Price including 20% VAT",
                    },
                ]
            return []
        elif query == QUERY_PRIMARY_KEY:
            table = args[1] if args and len(args) > 1 else ""
            if table == "products":
                return [{"column_name": "sku", "ordinal_position": 1}]
            return []
        elif query == QUERY_FOREIGN_KEYS:
            return []
        elif query == QUERY_UNIQUE_CONSTRAINTS:
            return []
        elif query == QUERY_CHECK_CONSTRAINTS_FALLBACK:
            return [
                {
                    "constraint_name": "chk_products_price_positive",
                    "check_clause": "`price` >= 0",
                }
            ]
        elif query == QUERY_INDEXES:
            table = args[1] if args and len(args) > 1 else ""
            if table == "products":
                return [
                    {
                        "index_name": "PRIMARY",
                        "non_unique": 0,
                        "seq_in_index": 1,
                        "column_name": "sku",
                        "index_type": "BTREE",
                        "sub_part": None,
                        "collation": "A",
                        "comment": "",
                    }
                ]
            return []
        elif query == QUERY_VIEWS:
            return []
        elif query == QUERY_TRIGGERS:
            return []
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
            return {"probe": 1, "ver": "10.11.6-MariaDB-1:10.11.6+maria~ubu2204"}
        elif query == QUERY_IDENTITY:
            return {
                "server_version": "10.11.6-MariaDB-1:10.11.6+maria~ubu2204",
                "version_comment": "mariadb.org binary distribution",
                "current_database": "inventory",
                "current_user": "operator@localhost",
            }
        return None


class TestMariaDbAdapter(BaseConnectorConformanceTests, unittest.IsolatedAsyncioTestCase):
    """Run full Phase 5.1 connector conformance suite against MariaDbConnector."""

    def create_valid_config(self) -> MariaDbConnectorConfig:
        return MariaDbConnectorConfig(
            database="inventory",
            host="mariadb.internal",
            port=3306,
        )

    def create_connector(
        self,
        config: ConnectorConfig | None = None,
        context: ConnectorContext | None = None,
    ) -> DatabaseConnector:
        cfg = config or self.create_valid_config()
        if not isinstance(cfg, MariaDbConnectorConfig):
            cfg = MariaDbConnectorConfig(
                database=cfg.database,
                host=cfg.host,
                port=cfg.port or 3306,
            )
        ctx = context or self.create_valid_context()
        mock_mgr = MockMariaDbConnectionManager(cfg)
        return MariaDbConnector(
            config=cfg,
            context=ctx,
            allow_loopback=True,
            connection_manager=mock_mgr,
        )

    async def test_mariadb_engine_detection(self) -> None:
        """Verify that MariaDB version strings accurately produce DatabaseEngine.MARIADB."""
        async with self.create_connector() as conn:
            identity = await conn.get_identity()
            self.assertEqual(identity.engine, DatabaseEngine.MARIADB)
            self.assertIn("10.11.6-MariaDB", identity.server_version or "")
            self.assertTrue(identity.server_capability_hints.get("is_mariadb"))

            caps = await conn.get_capabilities()
            self.assertEqual(caps.engine, DatabaseEngine.MARIADB)

    async def test_mariadb_specific_catalog_inspection(self) -> None:
        """Verify MariaDB Aria/InnoDB storage engine and persistent generated column handling."""
        async with self.create_connector() as conn:
            # Tables with Aria engine
            tables = await conn.list_tables()
            self.assertEqual(len(tables), 2)
            self.assertEqual([t.table_name for t in tables], ["products", "stock"])
            product_tbl = next(t for t in tables if t.table_name == "products")
            self.assertEqual(product_tbl.engine_specific.get("storage_engine"), "Aria")

            # Persistent generated column
            cols = await conn.list_columns("inventory", "products")
            self.assertEqual(len(cols), 3)
            gen_col = cols[2]
            self.assertTrue(gen_col.is_generated)
            self.assertEqual(gen_col.generation_expression, "`price` * 1.20")
            self.assertEqual(gen_col.engine_specific.get("generation_type"), "STORED")

            # Check constraints via fallback
            checks = await conn.list_check_constraints("inventory", "products")
            self.assertEqual(len(checks), 1)
            self.assertEqual(checks[0].constraint_name, "chk_products_price_positive")

    async def test_connection_probe(self) -> None:
        """Verify test_connection returns success and latency without leaving connection open."""
        conn = self.create_connector()
        result = await conn.test_connection()
        self.assertTrue(result.success)
        self.assertGreaterEqual(result.latency_ms, 0.0)
        self.assertEqual(conn.state, ConnectionState.CLOSED)
