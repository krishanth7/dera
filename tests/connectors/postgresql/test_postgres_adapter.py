"""Conformance and adapter tests for PostgresConnector."""

import unittest
from typing import Any

from dera_connectors.configuration import ConnectorConfig
from dera_connectors.context import CancellationToken, ConnectorContext
from dera_connectors.errors import ConnectorCancelledError
from dera_connectors.postgresql.adapter import PostgresConnector
from dera_connectors.postgresql.configuration import PostgresConnectorConfig
from dera_connectors.postgresql.queries import (
    QUERY_CHECK_CONSTRAINTS,
    QUERY_COLUMNS,
    QUERY_FOREIGN_KEYS,
    QUERY_IDENTITY,
    QUERY_INDEXES,
    QUERY_PRIMARY_KEY,
    QUERY_SCHEMAS,
    QUERY_TABLES,
    QUERY_UNIQUE_CONSTRAINTS,
    QUERY_VIEWS,
)
from dera_connectors.protocol import DatabaseConnector
from dera_connectors.testing.conformance import BaseConnectorConformanceTests


class MockPostgresConnectionManager:
    """Mock connection manager responding to system catalog queries with realistic fixture data."""

    def __init__(self, config: PostgresConnectorConfig) -> None:
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
        *args: Any,
        cancellation_token: CancellationToken | None = None,
        timeout: float | None = None,
    ) -> list[dict[str, Any]]:
        if cancellation_token and cancellation_token.is_cancelled:
            raise ConnectorCancelledError("Operation cancelled.")

        if query == QUERY_SCHEMAS:
            return [
                {"schema_name": "public", "comment": "Standard public schema"},
                {"schema_name": "analytics", "comment": "Data warehouse analytics schema"},
            ]
        elif query == QUERY_TABLES:
            return [
                {
                    "schema_name": "public",
                    "table_name": "users",
                    "object_type": "TABLE",
                    "comment": "User accounts",
                    "is_unlogged": False,
                    "is_partitioned": False,
                },
                {
                    "schema_name": "public",
                    "table_name": "orders",
                    "object_type": "TABLE",
                    "comment": "Orders table",
                    "is_unlogged": False,
                    "is_partitioned": False,
                },
            ]
        elif query == QUERY_COLUMNS:
            return [
                {
                    "schema_name": "public",
                    "table_name": "users",
                    "column_name": "id",
                    "ordinal_position": 1,
                    "data_type": "bigint",
                    "is_nullable": False,
                    "default_expression": None,
                    "is_identity": True,
                    "is_generated": False,
                    "generation_expression": None,
                    "comment": "ID",
                    "collation_name": None,
                },
                {
                    "schema_name": "public",
                    "table_name": "users",
                    "column_name": "email",
                    "ordinal_position": 2,
                    "data_type": "character varying(255)",
                    "is_nullable": False,
                    "default_expression": None,
                    "is_identity": False,
                    "is_generated": False,
                    "generation_expression": None,
                    "comment": None,
                    "collation_name": None,
                },
            ]
        elif query == QUERY_FOREIGN_KEYS:
            return []
        elif query == QUERY_UNIQUE_CONSTRAINTS:
            return [
                {
                    "constraint_name": "uq_users_email",
                    "schema_name": "public",
                    "table_name": "users",
                    "column_names": ["email"],
                }
            ]
        elif query == QUERY_CHECK_CONSTRAINTS:
            return []
        elif query == QUERY_INDEXES:
            return [
                {
                    "index_name": "users_pkey",
                    "schema_name": "public",
                    "table_name": "users",
                    "column_names": ["id"],
                    "is_unique": True,
                    "is_primary": True,
                    "index_type": "btree",
                    "predicate": None,
                }
            ]
        elif query == QUERY_VIEWS:
            return []

        return []

    async def fetchrow(
        self,
        query: str,
        *args: Any,
        cancellation_token: CancellationToken | None = None,
        timeout: float | None = None,
    ) -> dict[str, Any] | None:
        if cancellation_token and cancellation_token.is_cancelled:
            raise ConnectorCancelledError("Operation cancelled.")

        if query == QUERY_IDENTITY:
            return {
                "full_version": "PostgreSQL 16.2 on x86_64-pc-linux-gnu",
                "version_num": 160002,
                "current_database": "test_db",
                "current_user": "test_user",
            }
        elif query == QUERY_PRIMARY_KEY:
            return {
                "constraint_name": "users_pkey",
                "schema_name": "public",
                "table_name": "users",
                "column_names": ["id"],
            }
        elif "SELECT 1" in query:
            return {"probe": 1, "ver": "PostgreSQL 16.2 on x86_64-pc-linux-gnu"}

        return None


class TestPostgresAdapterConformance(
    BaseConnectorConformanceTests, unittest.IsolatedAsyncioTestCase
):
    """Run full Phase 5.1 connector conformance suite against PostgresConnector."""

    def create_valid_config(self) -> PostgresConnectorConfig:
        return PostgresConnectorConfig(
            database="test_db",
            host="127.0.0.1",
            port=5432,
            username="analyst",
        )

    def create_connector(
        self,
        config: ConnectorConfig | None = None,
        context: ConnectorContext | None = None,
    ) -> DatabaseConnector:
        cfg = config or self.create_valid_config()
        ctx = context or self.create_valid_context()
        mock_mgr = MockPostgresConnectionManager(cfg)  # type: ignore
        return PostgresConnector(
            config=cfg,
            context=ctx,
            connection_manager=mock_mgr,  # type: ignore
            allow_loopback=True,
        )

    async def test_test_connection_probe(self) -> None:
        """Verify test_connection lightweight probe returns ConnectionTestResult."""
        connector = self.create_connector()
        result = await connector.test_connection()
        self.assertTrue(result.success)
        self.assertIsNotNone(result.identity)
        self.assertIn("16.2", result.identity.server_version if result.identity else "")
        self.assertGreaterEqual(result.latency_ms, 0.0)


if __name__ == "__main__":
    unittest.main()
