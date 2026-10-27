"""DERA SQLite Connector — Adapter Implementation.

Implements the DERA Phase 5.1 DatabaseConnector protocol for local SQLite 3.x embedded
databases with deterministic metadata introspection, read-only guarantees, and
filesystem isolation.
"""

from __future__ import annotations

import time
import uuid
from typing import Any

from dera_connectors.capabilities import ConnectorCapabilities
from dera_connectors.context import ConnectorContext
from dera_connectors.engine import DatabaseEngine, DatabaseIdentity
from dera_connectors.lifecycle import ConnectionLifecycle, ConnectionState
from dera_connectors.metadata import (
    CheckConstraintInfo,
    ColumnInfo,
    ForeignKeyInfo,
    IndexInfo,
    PrimaryKeyInfo,
    SchemaInfo,
    TableInfo,
    TriggerInfo,
    UniqueConstraintInfo,
    ViewInfo,
)
from dera_connectors.protocol import DatabaseConnector
from dera_connectors.results import ConnectionTestResult
from dera_connectors.sqlite.capabilities import get_sqlite_capabilities
from dera_connectors.sqlite.catalog import (
    introspect_check_constraints,
    introspect_columns,
    introspect_foreign_keys,
    introspect_identity,
    introspect_indexes,
    introspect_primary_key,
    introspect_schemas,
    introspect_tables,
    introspect_triggers,
    introspect_unique_constraints,
    introspect_views,
)
from dera_connectors.sqlite.configuration import SqliteConnectorConfig
from dera_connectors.sqlite.connection import SqliteConnectionManager


class SqliteConnector(DatabaseConnector):
    """Production read-only SQLite 3 connector adapter adhering to Phase 5.1 protocol."""

    def __init__(
        self,
        config: SqliteConnectorConfig,
        context: ConnectorContext | None = None,
        connection_manager: SqliteConnectionManager | None = None,
    ) -> None:
        """Initialize SQLite connector adapter.

        Parameters
        ----------
        config : SqliteConnectorConfig
            Strongly-typed SQLite connection and filesystem configuration.
        context : ConnectorContext | None
            Execution and tenant context (generates default context if None).
        connection_manager : SqliteConnectionManager | None
            Optional connection manager instance (for test injection).
        """
        if not isinstance(config, SqliteConnectorConfig):
            # Convert generic ConnectorConfig if necessary
            config = SqliteConnectorConfig(
                database=config.database,
                timeouts=config.timeouts,
                driver_options=config.driver_options,
            )

        self._config = config
        self._context = context or ConnectorContext(workspace_id=uuid.uuid4())
        self._lifecycle = ConnectionLifecycle()
        self._conn_mgr = connection_manager or SqliteConnectionManager(config)

    @property
    def config(self) -> SqliteConnectorConfig:
        """Return the connector configuration."""
        return self._config

    @property
    def context(self) -> ConnectorContext:
        """Return the execution and tenant context."""
        return self._context

    @property
    def state(self) -> ConnectionState:
        """Return current connection lifecycle state."""
        return self._lifecycle.state

    @property
    def is_connected(self) -> bool:
        """Return True if connection is established and healthy."""
        return self._lifecycle.state == ConnectionState.CONNECTED and self._conn_mgr.is_connected

    async def connect(self) -> None:
        """Establish read-only connection to SQLite database."""
        if self._lifecycle.state == ConnectionState.CONNECTED:
            return

        if self._context.cancellation_token and self._context.cancellation_token.is_cancelled:
            from dera_connectors.errors import ConnectorCancelledError

            raise ConnectorCancelledError("Connection cancelled by user.")

        self._lifecycle.transition_to(ConnectionState.CONNECTING)
        try:
            await self._conn_mgr.connect(cancellation_token=self._context.cancellation_token)
            self._lifecycle.transition_to(ConnectionState.CONNECTED)
        except Exception:
            self._lifecycle.transition_to(ConnectionState.FAILED)
            raise

    async def close(self) -> None:
        """Close connection and release underlying filesystem resources."""
        if self._lifecycle.state == ConnectionState.CLOSED:
            return

        self._lifecycle.transition_to(ConnectionState.CLOSING)
        try:
            await self._conn_mgr.close()
        finally:
            self._lifecycle.transition_to(ConnectionState.CLOSED)

    async def test_connection(self) -> ConnectionTestResult:
        """Execute a lightweight non-intrusive probe to verify readability."""
        start_time = time.perf_counter()
        try:
            if not self.is_connected:
                await self.connect()

            # Execute lightweight version query
            identity = await self.get_identity()
            latency_ms = (time.perf_counter() - start_time) * 1000.0

            return ConnectionTestResult(
                success=True,
                latency_ms=latency_ms,
                identity=identity,
                details={
                    "engine": DatabaseEngine.SQLITE.value,
                    "canonical_path": self._conn_mgr.canonical_path,
                },
            )
        except Exception as exc:
            latency_ms = (time.perf_counter() - start_time) * 1000.0
            return ConnectionTestResult(
                success=False,
                latency_ms=latency_ms,
                error_message=str(exc),
                details={"engine": DatabaseEngine.SQLITE.value},
            )

    async def get_identity(self) -> DatabaseIdentity:
        """Discover SQLite engine version and metadata fingerprint."""
        if not self.is_connected:
            await self.connect()
        return await introspect_identity(self._conn_mgr, self._config.database)

    async def get_capabilities(self) -> ConnectorCapabilities:
        """Return SQLite capability matrix."""
        return get_sqlite_capabilities()

    async def list_schemas(self) -> list[SchemaInfo]:
        """Enumerate database namespaces from PRAGMA database_list."""
        if not self.is_connected:
            await self.connect()
        return await introspect_schemas(self._conn_mgr)

    async def list_tables(self, schema: str | None = None) -> list[TableInfo]:
        """Enumerate user tables and virtual tables in deterministic alphabetical order."""
        if not self.is_connected:
            await self.connect()
        return await introspect_tables(self._conn_mgr, schema=schema)

    async def list_columns(self, schema: str | None, table: str) -> list[ColumnInfo]:
        """Inspect table columns in deterministic ordinal order."""
        if not self.is_connected:
            await self.connect()
        return await introspect_columns(self._conn_mgr, table=table, schema=schema)

    async def get_primary_key(self, schema: str | None, table: str) -> PrimaryKeyInfo | None:
        """Inspect primary key constraint for a table."""
        if not self.is_connected:
            await self.connect()
        return await introspect_primary_key(self._conn_mgr, table=table, schema=schema)

    async def list_foreign_keys(self, schema: str | None, table: str) -> list[ForeignKeyInfo]:
        """Inspect foreign key constraints for a table."""
        if not self.is_connected:
            await self.connect()
        return await introspect_foreign_keys(self._conn_mgr, table=table, schema=schema)

    async def list_unique_constraints(
        self, schema: str | None, table: str
    ) -> list[UniqueConstraintInfo]:
        """Inspect unique constraints for a table."""
        if not self.is_connected:
            await self.connect()
        return await introspect_unique_constraints(self._conn_mgr, table=table, schema=schema)

    async def list_check_constraints(
        self, schema: str | None, table: str
    ) -> list[CheckConstraintInfo]:
        """Inspect check constraints for a table."""
        if not self.is_connected:
            await self.connect()
        return await introspect_check_constraints(self._conn_mgr, table=table, schema=schema)

    async def list_indexes(self, schema: str | None, table: str) -> list[IndexInfo]:
        """Inspect secondary indexes for a table."""
        if not self.is_connected:
            await self.connect()
        return await introspect_indexes(self._conn_mgr, table=table, schema=schema)

    async def list_views(self, schema: str | None = None) -> list[ViewInfo]:
        """Inspect views from sqlite_schema without executing view definitions."""
        if not self.is_connected:
            await self.connect()
        return await introspect_views(self._conn_mgr, schema=schema)

    async def list_triggers(
        self, table: str | None = None, schema: str | None = None
    ) -> list[TriggerInfo]:
        """Inspect triggers from sqlite_schema without executing trigger bodies."""
        if not self.is_connected:
            await self.connect()
        return await introspect_triggers(self._conn_mgr, table=table, schema=schema)

    async def __aenter__(self) -> SqliteConnector:
        """Enter asynchronous resource context; establishes connection."""
        await self.connect()
        return self

    async def __aexit__(
        self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: Any
    ) -> None:
        """Exit asynchronous resource context; guarantees connection teardown."""
        await self.close()
