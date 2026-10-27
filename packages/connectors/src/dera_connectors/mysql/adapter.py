"""DERA MySQL Connector — Adapter Implementation.

Implements the DERA Phase 5.1 DatabaseConnector protocol for MySQL 8.0+ and 8.4 LTS
instances with deterministic catalog introspection, least-privilege information_schema
queries, and strict read-only session enforcement.
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
    PrimaryKeyInfo,
    SchemaInfo,
    TableInfo,
    TriggerInfo,
    UniqueConstraintInfo,
    ViewInfo,
)
from dera_connectors.mysql.capabilities import get_mysql_capabilities
from dera_connectors.mysql.configuration import MySqlConnectorConfig
from dera_connectors.mysql_family.catalog import (
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
from dera_connectors.mysql_family.connection import MySqlFamilyConnectionManager
from dera_connectors.protocol import DatabaseConnector
from dera_connectors.results import ConnectionTestResult


class MySqlConnector(DatabaseConnector):
    """Production asynchronous database connector for MySQL 8.0+ and 8.4 LTS."""

    def __init__(
        self,
        config: ConnectorConfig | MySqlConnectorConfig,
        context: ConnectorContext | None = None,
        allow_loopback: bool = False,
        connection_manager: MySqlFamilyConnectionManager | None = None,
    ) -> None:
        """Initialize MySQL connector instance.

        Parameters
        ----------
        config : ConnectorConfig | MySqlConnectorConfig
            Validated connection configuration.
        context : ConnectorContext | None
            Execution and tenant isolation context.
        allow_loopback : bool
            Allow loopback connections (intended for local testing).
        connection_manager : MySqlFamilyConnectionManager | None
            Optional pre-configured connection manager (for test injection).
        """
        if isinstance(config, MySqlConnectorConfig):
            self._mysql_config = config
        else:
            self._mysql_config = MySqlConnectorConfig(
                engine=DatabaseEngine.MYSQL,
                database=config.database,
                host=config.host,
                port=config.port or 3306,
                username=config.username,
                password=config.password,
                credential_reference=config.credential_reference,
                tls=config.tls,
                timeouts=config.timeouts,
            )

        self._context = context or ConnectorContext(workspace_id=uuid.uuid4())
        self._allow_loopback = allow_loopback
        self._lifecycle = ConnectionLifecycle()
        self._conn_mgr = connection_manager or MySqlFamilyConnectionManager(self._mysql_config)

    @property
    def config(self) -> MySqlConnectorConfig:
        """Return connector configuration."""
        return self._mysql_config

    @property
    def context(self) -> ConnectorContext:
        """Return tenant and operation context."""
        return self._context

    @property
    def state(self) -> ConnectionState:
        """Return current connection lifecycle state."""
        return self._lifecycle.state

    @property
    def is_connected(self) -> bool:
        """Return True if connection is actively open and ready."""
        return self._lifecycle.state == ConnectionState.CONNECTED and self._conn_mgr.is_connected

    async def connect(self) -> None:
        """Establish network connection, validate TLS, and enforce read-only session mode."""
        if self._lifecycle.state == ConnectionState.CONNECTED and self._conn_mgr.is_connected:
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
                "SELECT 1 AS probe, VERSION() AS ver;",
                cancellation_token=self._context.cancellation_token,
                timeout=self._mysql_config.timeouts.connect_timeout_seconds,
            )
            latency_ms = (time.perf_counter() - start_time) * 1000.0
            identity = await self.get_identity()

            return ConnectionTestResult(
                success=True,
                latency_ms=round(latency_ms, 2),
                identity=identity,
                capabilities_summary=[
                    "table_enumeration",
                    "column_inspection",
                    "primary_key_inspection",
                    "foreign_key_inspection",
                    "check_constraint_inspection",
                    "index_inspection",
                    "view_inspection",
                    "trigger_inspection",
                ],
            )
        except Exception as exc:
            latency_ms = (time.perf_counter() - start_time) * 1000.0
            error_code = getattr(exc, "error_code", None) or type(exc).__name__
            return ConnectionTestResult(
                success=False,
                latency_ms=round(latency_ms, 2),
                identity=None,
                error_code=str(error_code),
                error_message=str(exc),
            )
        finally:
            if not was_connected and self.is_connected:
                await self.close()

    async def get_identity(self) -> DatabaseIdentity:
        """Return identified MySQL engine fingerprint and version."""
        if not self.is_connected:
            await self.connect()
        return await introspect_identity(
            self._conn_mgr,
            default_engine=DatabaseEngine.MYSQL,
            cancellation_token=self._context.cancellation_token,
            timeout=self._mysql_config.timeouts.query_timeout_seconds,
        )

    async def get_capabilities(self) -> ConnectorCapabilities:
        """Return reported capability matrix for MySQL 8.0+."""
        return get_mysql_capabilities()

    async def list_schemas(self) -> list[SchemaInfo]:
        """Enumerate user database schemas in deterministic alphabetical order."""
        if not self.is_connected:
            await self.connect()
        return await introspect_schemas(
            self._conn_mgr,
            cancellation_token=self._context.cancellation_token,
            timeout=self._mysql_config.timeouts.query_timeout_seconds,
        )

    async def list_tables(self, schema: str | None = None) -> list[TableInfo]:
        """Enumerate tables in deterministic order for a given schema."""
        if not self.is_connected:
            await self.connect()
        target_schema = schema or self._mysql_config.database
        return await introspect_tables(
            self._conn_mgr,
            schema_name=target_schema,
            cancellation_token=self._context.cancellation_token,
            timeout=self._mysql_config.timeouts.query_timeout_seconds,
        )

    async def list_columns(self, schema: str | None, table: str) -> list[ColumnInfo]:
        """Inspect table columns in deterministic ordinal position order."""
        if not self.is_connected:
            await self.connect()
        target_schema = schema or self._mysql_config.database
        return await introspect_columns(
            self._conn_mgr,
            schema_name=target_schema,
            table_name=table,
            cancellation_token=self._context.cancellation_token,
            timeout=self._mysql_config.timeouts.query_timeout_seconds,
        )

    async def get_primary_key(self, schema: str | None, table: str) -> PrimaryKeyInfo | None:
        """Inspect primary key constraint and participating columns."""
        if not self.is_connected:
            await self.connect()
        target_schema = schema or self._mysql_config.database
        return await introspect_primary_key(
            self._conn_mgr,
            schema_name=target_schema,
            table_name=table,
            cancellation_token=self._context.cancellation_token,
            timeout=self._mysql_config.timeouts.query_timeout_seconds,
        )

    async def list_foreign_keys(self, schema: str | None, table: str) -> list[ForeignKeyInfo]:
        """Inspect foreign key constraints for a table in deterministic order."""
        if not self.is_connected:
            await self.connect()
        target_schema = schema or self._mysql_config.database
        return await introspect_foreign_keys(
            self._conn_mgr,
            schema_name=target_schema,
            table_name=table,
            cancellation_token=self._context.cancellation_token,
            timeout=self._mysql_config.timeouts.query_timeout_seconds,
        )

    async def list_unique_constraints(
        self, schema: str | None, table: str
    ) -> list[UniqueConstraintInfo]:
        """Inspect unique constraints for a table in deterministic order."""
        if not self.is_connected:
            await self.connect()
        target_schema = schema or self._mysql_config.database
        return await introspect_unique_constraints(
            self._conn_mgr,
            schema_name=target_schema,
            table_name=table,
            cancellation_token=self._context.cancellation_token,
            timeout=self._mysql_config.timeouts.query_timeout_seconds,
        )

    async def list_check_constraints(
        self, schema: str | None, table: str
    ) -> list[CheckConstraintInfo]:
        """Inspect check constraints for a table in deterministic order."""
        if not self.is_connected:
            await self.connect()
        target_schema = schema or self._mysql_config.database
        return await introspect_check_constraints(
            self._conn_mgr,
            schema_name=target_schema,
            table_name=table,
            is_mariadb=False,
            cancellation_token=self._context.cancellation_token,
            timeout=self._mysql_config.timeouts.query_timeout_seconds,
        )

    async def list_indexes(self, schema: str | None, table: str) -> list[IndexInfo]:
        """Inspect indexes for a table including functional expressions."""
        if not self.is_connected:
            await self.connect()
        target_schema = schema or self._mysql_config.database
        return await introspect_indexes(
            self._conn_mgr,
            schema_name=target_schema,
            table_name=table,
            is_mysql8=True,
            cancellation_token=self._context.cancellation_token,
            timeout=self._mysql_config.timeouts.query_timeout_seconds,
        )

    async def list_views(self, schema: str | None = None) -> list[ViewInfo]:
        """Inspect view definitions in deterministic order without executing view bodies."""
        if not self.is_connected:
            await self.connect()
        target_schema = schema or self._mysql_config.database
        return await introspect_views(
            self._conn_mgr,
            schema_name=target_schema,
            cancellation_token=self._context.cancellation_token,
            timeout=self._mysql_config.timeouts.query_timeout_seconds,
        )

    async def list_triggers(
        self, table: str | None = None, schema: str | None = None
    ) -> list[TriggerInfo]:
        """Inspect trigger definitions in deterministic order without executing triggers."""
        if not self.is_connected:
            await self.connect()
        target_schema = schema or self._mysql_config.database
        return await introspect_triggers(
            self._conn_mgr,
            schema_name=target_schema,
            table_name=table,
            cancellation_token=self._context.cancellation_token,
            timeout=self._mysql_config.timeouts.query_timeout_seconds,
        )

    async def __aenter__(self) -> MySqlConnector:
        """Enter asynchronous context; guarantees connection."""
        await self.connect()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> None:
        """Exit asynchronous context; guarantees connection teardown."""
        await self.close()
