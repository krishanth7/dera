"""DERA Connectors — Reusable Adapter Conformance Test Suite.

Provides an abstract test suite class that any database-specific adapter
(FakeConnector, PostgreSQLConnector, SQLiteConnector, MySQLConnector) must inherit
and satisfy to verify conformance with Phase 5 standards.
"""

import unittest
import uuid
from abc import ABC, abstractmethod

from dera_connectors.capabilities import ConnectorCapability
from dera_connectors.configuration import ConnectorConfig
from dera_connectors.context import CancellationToken, ConnectorContext
from dera_connectors.errors import ConnectorCancelledError
from dera_connectors.lifecycle import ConnectionState
from dera_connectors.protocol import DatabaseConnector


class BaseConnectorConformanceTests(ABC):
    """Reusable conformance test suite for verifying connector adapters against DERA Phase 5.1 specs."""

    @abstractmethod
    def create_connector(
        self,
        config: ConnectorConfig | None = None,
        context: ConnectorContext | None = None,
    ) -> DatabaseConnector:
        """Construct an unconnected connector instance for testing."""
        ...

    @abstractmethod
    def create_valid_config(self) -> ConnectorConfig:
        """Provide a valid test configuration."""
        ...

    def create_valid_context(self) -> ConnectorContext:
        """Provide a standard execution context bound to a test workspace."""
        return ConnectorContext(workspace_id=uuid.uuid4())

    async def test_protocol_conformance(self: unittest.TestCase) -> None:
        """Verify the adapter class satisfies the DatabaseConnector protocol."""
        connector = self.create_connector()
        self.assertIsInstance(connector, DatabaseConnector)
        self.assertIsNotNone(connector.config)
        self.assertIsNotNone(connector.context)
        self.assertEqual(connector.state, ConnectionState.CREATED)

    async def test_lifecycle_connect_and_close(self: unittest.TestCase) -> None:
        """Verify explicit lifecycle transitions: CREATED -> CONNECTED -> CLOSED."""
        connector = self.create_connector()
        self.assertEqual(connector.state, ConnectionState.CREATED)

        await connector.connect()
        self.assertEqual(connector.state, ConnectionState.CONNECTED)

        await connector.close()
        self.assertEqual(connector.state, ConnectionState.CLOSED)

        # Closing an already closed connector must be safely idempotent
        await connector.close()
        self.assertEqual(connector.state, ConnectionState.CLOSED)

    async def test_async_context_manager(self: unittest.TestCase) -> None:
        """Verify async with context manager automatically connects and closes."""
        connector = self.create_connector()

        async with connector as conn:
            self.assertEqual(conn.state, ConnectionState.CONNECTED)

        self.assertEqual(connector.state, ConnectionState.CLOSED)

    async def test_identity_and_capabilities(self: unittest.TestCase) -> None:
        """Verify get_identity and get_capabilities return valid structured models."""
        async with self.create_connector() as conn:
            identity = await conn.get_identity()
            self.assertIsNotNone(identity.engine)
            self.assertIsNotNone(identity.connector_version)

            caps = await conn.get_capabilities()
            self.assertEqual(caps.engine, identity.engine)
            # Must at least report table enumeration capability status
            self.assertIn(ConnectorCapability.TABLE_ENUMERATION, caps.capabilities)

    async def test_deterministic_table_ordering(self: unittest.TestCase) -> None:
        """Verify tables are listed in deterministic sorted order."""
        async with self.create_connector() as conn:
            tables = await conn.list_tables()
            self.assertIsInstance(tables, list)
            # Verify sorted by (schema_name, table_name)
            sorted_tables = sorted(tables, key=lambda t: (t.schema_name, t.table_name))
            self.assertEqual(tables, sorted_tables)

    async def test_deterministic_column_ordering(self: unittest.TestCase) -> None:
        """Verify columns are returned sorted by ordinal_position."""
        async with self.create_connector() as conn:
            tables = await conn.list_tables()
            if not tables:
                return

            table = tables[0]
            columns = await conn.list_columns(table.schema_name, table.table_name)
            self.assertIsInstance(columns, list)
            if columns:
                sorted_cols = sorted(columns, key=lambda c: c.ordinal_position)
                self.assertEqual(columns, sorted_cols)

    async def test_cancellation_responsiveness(self: unittest.TestCase) -> None:
        """Verify connector checks cancellation token and raises ConnectorCancelledError."""
        token = CancellationToken()
        token.cancel("User cancelled test.")
        ctx = ConnectorContext(workspace_id=uuid.uuid4(), cancellation_token=token)

        connector = self.create_connector(context=ctx)
        with self.assertRaises(ConnectorCancelledError):
            await connector.connect()

    async def test_no_mutation_apis_on_protocol(self: unittest.TestCase) -> None:
        """Verify the connector protocol strictly lacks any execute_sql, mutate, or ddl methods."""
        connector = self.create_connector()
        forbidden_attributes = [
            "execute",
            "execute_sql",
            "execute_mutation",
            "execute_ddl",
            "drop_table",
            "create_table",
            "insert",
            "update",
            "delete",
            "run_migration",
        ]
        for attr in forbidden_attributes:
            self.assertFalse(
                hasattr(connector, attr),
                f"Connector must not expose mutation method '{attr}'.",
            )
