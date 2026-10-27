"""DERA PostgreSQL Connector — Production Database Connector Adapter.

Implements the universal DatabaseConnector protocol for standard PostgreSQL
and Supabase-hosted PostgreSQL instances with deterministic catalog introspection,
strict read-only session enforcement, and comprehensive error taxonomy.
"""

from __future__ import annotations

import time
import uuid
from typing import Any

from dera_connectors.capabilities import ConnectorCapabilities
from dera_connectors.configuration import ConnectorConfig
from dera_connectors.context import ConnectorContext
from dera_connectors.engine import DatabaseEngine, DatabaseIdentity
from dera_connectors.lifecycle import ConnectionLifecycle, ConnectionState
from dera_connectors.metadata import (
    CheckConstraintInfo,
    ColumnInfo,
    ForeignKeyInfo,
    IndexInfo,
    PartitionInfo,
    PrimaryKeyInfo,
    SchemaInfo,
    SequenceInfo,
    TableInfo,
    UniqueConstraintInfo,
    ViewInfo,
)
from dera_connectors.postgresql.capabilities import get_postgres_capabilities
from dera_connectors.postgresql.catalog import (
    inspect_check_constraints,
    inspect_columns,
    inspect_foreign_keys,
    inspect_identity,
    inspect_indexes,
    inspect_partitions,
    inspect_primary_key,
    inspect_schemas,
    inspect_sequences,
    inspect_tables,
    inspect_unique_constraints,
    inspect_views,
)
from dera_connectors.postgresql.configuration import PostgresConnectorConfig
from dera_connectors.postgresql.connection import PostgresConnectionManager
from dera_connectors.protocol import DatabaseConnector
from dera_connectors.results import ConnectionTestResult


class PostgresConnector(DatabaseConnector):
    """Production asynchronous database connector for PostgreSQL and Supabase."""

    def __init__(
        self,
        config: ConnectorConfig | PostgresConnectorConfig,
        context: ConnectorContext | None = None,
        allow_loopback: bool = False,
        connection_manager: PostgresConnectionManager | None = None,
    ) -> None:
        """Initialize PostgreSQL connector instance.

        Parameters
        ----------
        config : ConnectorConfig | PostgresConnectorConfig
            Validated connection configuration.
        context : ConnectorContext | None
            Execution and tenant isolation context.
        allow_loopback : bool
            Allow loopback connections (intended for local testing).
        connection_manager : PostgresConnectionManager | None
            Optional pre-configured connection manager (for test injection).
        """
        if isinstance(config, PostgresConnectorConfig):
            self._pg_config = config
        else:
            # Upgrade general ConnectorConfig to PostgresConnectorConfig
            self._pg_config = PostgresConnectorConfig(
                engine=DatabaseEngine.POSTGRESQL,
                database=config.database,
                host=config.host,
                port=config.port,
                username=config.username,
                password=config.password,
                credential_reference=config.credential_reference,
                tls=config.tls,
                timeouts=config.timeouts,
            )

        self._context = context or ConnectorContext(workspace_id=uuid.uuid4())
        self._allow_loopback = allow_loopback
        self._lifecycle = ConnectionLifecycle()
        self._conn_mgr = connection_manager or PostgresConnectionManager(self._pg_config)

    @property
    def config(self) -> PostgresConnectorConfig:
        """Return connector configuration."""
        return self._pg_config

    @property
    def context(self) -> ConnectorContext:
        """Return bound tenant and execution context."""
        return self._context

    @property
    def state(self) -> ConnectionState:
        """Return current connection lifecycle state."""
        return self._lifecycle.state

    @property
    def connection_manager(self) -> PostgresConnectionManager:
        """Return underlying PostgresConnectionManager."""
        return self._conn_mgr

    async def connect(self) -> None:
        """Establish network connection and initialize read-only session."""
        if self._lifecycle.state == ConnectionState.CONNECTED:
            return

        self._lifecycle.transition_to(ConnectionState.CONNECTING)

        try:
            await self._conn_mgr.connect(
                cancellation_token=self._context.cancellation_token,
                allow_loopback=self._allow_loopback,
            )
            self._lifecycle.transition_to(ConnectionState.CONNECTED)
        except Exception:
            self._lifecycle.transition_to(ConnectionState.FAILED)
            raise

    async def close(self) -> None:
        """Safely and idempotently terminate connection and release resources."""
        if self._lifecycle.state == ConnectionState.CLOSED:
            return

        self._lifecycle.transition_to(ConnectionState.CLOSING)
        try:
            await self._conn_mgr.close()
        finally:
            self._lifecycle.transition_to(ConnectionState.CLOSED)

    async def test_connection(self) -> ConnectionTestResult:
        """Verify network reachability and authentication via lightweight ping."""
        start_time = time.perf_counter()
        was_connected = self._lifecycle.state == ConnectionState.CONNECTED

        try:
            if not was_connected:
                await self.connect()

            await self._conn_mgr.fetchrow(
                "SELECT 1 AS probe, version() AS ver;",
                cancellation_token=self._context.cancellation_token,
                timeout=self._pg_config.timeouts.connect_timeout_seconds,
            )
            latency_ms = (time.perf_counter() - start_time) * 1000.0

            identity = await self.get_identity()

            return ConnectionTestResult(
                success=True,
                latency_ms=round(latency_ms, 2),
                identity=identity,
                capabilities_summary=[
                    "schema_enumeration",
                    "table_enumeration",
                    "column_inspection",
                    "view_inspection",
                ],
            )
        except Exception as exc:
            latency_ms = (time.perf_counter() - start_time) * 1000.0
            return ConnectionTestResult(
                success=False,
                latency_ms=round(latency_ms, 2),
                error_code="CONNECTOR_UNAVAILABLE",
                error_message=f"PostgreSQL connection verification failed: {exc}",
            )
        finally:
            if not was_connected and self._lifecycle.state == ConnectionState.CONNECTED:
                await self.close()

    async def get_identity(self) -> DatabaseIdentity:
        """Return the database engine fingerprint, server version, and driver info."""
        return await inspect_identity(
            self._conn_mgr,
            provider=self._pg_config.provider,
            cancellation_token=self._context.cancellation_token,
            timeout=self._pg_config.timeouts.query_timeout_seconds,
        )

    async def get_capabilities(self) -> ConnectorCapabilities:
        """Discover and return supported metadata inspection capabilities."""
        return get_postgres_capabilities(self._pg_config.provider)

    async def list_schemas(self) -> list[SchemaInfo]:
        """Enumerate user schemas in deterministic alphabetical order."""
        return await inspect_schemas(
            self._conn_mgr,
            cancellation_token=self._context.cancellation_token,
            timeout=self._pg_config.timeouts.query_timeout_seconds,
        )

    async def list_tables(self, schema: str | None = None) -> list[TableInfo]:
        """Enumerate tables in deterministic order (by schema and table name)."""
        return await inspect_tables(
            self._conn_mgr,
            schema=schema,
            cancellation_token=self._context.cancellation_token,
            timeout=self._pg_config.timeouts.query_timeout_seconds,
        )

    async def list_columns(self, schema: str | None, table: str) -> list[ColumnInfo]:
        """Inspect table columns in deterministic ordinal order."""
        return await inspect_columns(
            self._conn_mgr,
            schema=schema,
            table=table,
            cancellation_token=self._context.cancellation_token,
            timeout=self._pg_config.timeouts.query_timeout_seconds,
        )

    async def get_primary_key(self, schema: str | None, table: str) -> PrimaryKeyInfo | None:
        """Inspect primary key constraint for a table."""
        return await inspect_primary_key(
            self._conn_mgr,
            schema=schema,
            table=table,
            cancellation_token=self._context.cancellation_token,
            timeout=self._pg_config.timeouts.query_timeout_seconds,
        )

    async def list_foreign_keys(self, schema: str | None, table: str) -> list[ForeignKeyInfo]:
        """Inspect foreign key constraints for a table in deterministic order."""
        return await inspect_foreign_keys(
            self._conn_mgr,
            schema=schema,
            table=table,
            cancellation_token=self._context.cancellation_token,
            timeout=self._pg_config.timeouts.query_timeout_seconds,
        )

    async def list_unique_constraints(
        self, schema: str | None, table: str
    ) -> list[UniqueConstraintInfo]:
        """Inspect unique constraints for a table in deterministic order."""
        return await inspect_unique_constraints(
            self._conn_mgr,
            schema=schema,
            table=table,
            cancellation_token=self._context.cancellation_token,
            timeout=self._pg_config.timeouts.query_timeout_seconds,
        )

    async def list_check_constraints(
        self, schema: str | None, table: str
    ) -> list[CheckConstraintInfo]:
        """Inspect check constraints for a table in deterministic order."""
        return await inspect_check_constraints(
            self._conn_mgr,
            schema=schema,
            table=table,
            cancellation_token=self._context.cancellation_token,
            timeout=self._pg_config.timeouts.query_timeout_seconds,
        )

    async def list_indexes(self, schema: str | None, table: str) -> list[IndexInfo]:
        """Inspect secondary indexes for a table in deterministic order."""
        return await inspect_indexes(
            self._conn_mgr,
            schema=schema,
            table=table,
            cancellation_token=self._context.cancellation_token,
            timeout=self._pg_config.timeouts.query_timeout_seconds,
        )

    async def list_views(self, schema: str | None = None) -> list[ViewInfo]:
        """Inspect views and materialized views in deterministic order."""
        return await inspect_views(
            self._conn_mgr,
            schema=schema,
            cancellation_token=self._context.cancellation_token,
            timeout=self._pg_config.timeouts.query_timeout_seconds,
        )

    async def list_sequences(self, schema: str | None = None) -> list[SequenceInfo]:
        """Inspect sequence objects in deterministic order."""
        return await inspect_sequences(
            self._conn_mgr,
            schema=schema,
            cancellation_token=self._context.cancellation_token,
            timeout=self._pg_config.timeouts.query_timeout_seconds,
        )

    async def list_partitions(
        self, schema: str | None = None, table: str | None = None
    ) -> list[PartitionInfo]:
        """Inspect partition metadata in deterministic order."""
        return await inspect_partitions(
            self._conn_mgr,
            schema=schema,
            table=table,
            cancellation_token=self._context.cancellation_token,
            timeout=self._pg_config.timeouts.query_timeout_seconds,
        )

    async def __aenter__(self) -> DatabaseConnector:
        """Enter asynchronous resource context; establishes connection."""
        await self.connect()
        return self

    async def __aexit__(
        self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: Any
    ) -> None:
        """Exit asynchronous resource context; guarantees connection teardown."""
        await self.close()
