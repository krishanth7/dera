"""DERA Connectors — Deterministic Fake Connector for Testing.

Provides a fully compliant, configurable mock database connector implementing
the DatabaseConnector protocol. Supports controlled simulations of connection failures,
timeouts, permission denials, cooperative cancellation, and resource tracking.
"""

from __future__ import annotations

import asyncio
from typing import Any

from dera_connectors.capabilities import (
    CapabilityStatus,
    CapabilitySupport,
    ConnectorCapabilities,
    ConnectorCapability,
)
from dera_connectors.configuration import ConnectorConfig
from dera_connectors.context import ConnectorContext
from dera_connectors.engine import DatabaseIdentity, DatabaseProvider
from dera_connectors.errors import (
    ConnectorAuthenticationFailedError,
    ConnectorPermissionDeniedError,
    ConnectorTimeoutError,
    ConnectorUnavailableError,
)
from dera_connectors.lifecycle import ConnectionLifecycle, ConnectionState
from dera_connectors.metadata import (
    CheckConstraintInfo,
    ColumnInfo,
    ForeignKeyInfo,
    IndexInfo,
    PrimaryKeyInfo,
    SchemaInfo,
    TableInfo,
    UniqueConstraintInfo,
    ViewInfo,
)
from dera_connectors.results import ConnectionTestResult


class FakeDatabaseConnector:
    """Deterministic fake connector implementing the DatabaseConnector protocol."""

    def __init__(
        self,
        config: ConnectorConfig,
        context: ConnectorContext,
        simulate_connect_failure: bool = False,
        simulate_auth_failure: bool = False,
        simulate_permission_denial: bool = False,
        simulate_timeout: bool = False,
        simulate_latency_seconds: float = 0.0,
        unsupported_capabilities: set[ConnectorCapability] | None = None,
        custom_schemas: list[SchemaInfo] | None = None,
        custom_tables: list[TableInfo] | None = None,
        custom_columns: dict[str, list[ColumnInfo]] | None = None,
        custom_pks: dict[str, PrimaryKeyInfo] | None = None,
        custom_fks: dict[str, list[ForeignKeyInfo]] | None = None,
        custom_unique_constraints: dict[str, list[UniqueConstraintInfo]] | None = None,
        custom_check_constraints: dict[str, list[CheckConstraintInfo]] | None = None,
        custom_indexes: dict[str, list[IndexInfo]] | None = None,
        custom_views: list[ViewInfo] | None = None,
    ) -> None:
        self._config = config
        self._context = context
        self._lifecycle = ConnectionLifecycle()

        # Simulation behavior flags
        self.simulate_connect_failure = simulate_connect_failure
        self.simulate_auth_failure = simulate_auth_failure
        self.simulate_permission_denial = simulate_permission_denial
        self.simulate_timeout = simulate_timeout
        self.simulate_latency_seconds = simulate_latency_seconds
        self.unsupported_caps = unsupported_capabilities or set()

        # Telemetry and call tracking
        self.connect_calls: int = 0
        self.close_calls: int = 0
        self.test_connection_calls: int = 0
        self.inspected_tables_calls: int = 0

        # Deterministic fixtures
        self.schemas = custom_schemas or [
            SchemaInfo(schema_name="public", comment="Standard public schema"),
            SchemaInfo(schema_name="analytics", comment="Analytics data mart"),
        ]
        self.tables = custom_tables or [
            TableInfo(
                schema_name="public",
                table_name="users",
                object_type="TABLE",
                comment="User accounts",
            ),
            TableInfo(
                schema_name="public",
                table_name="orders",
                object_type="TABLE",
                comment="Order records",
            ),
            TableInfo(schema_name="analytics", table_name="monthly_revenue", object_type="TABLE"),
        ]
        self.columns = custom_columns or {
            "public.users": [
                ColumnInfo(
                    schema_name="public",
                    table_name="users",
                    column_name="id",
                    ordinal_position=1,
                    data_type="BIGINT",
                    is_nullable=False,
                    is_identity=True,
                ),
                ColumnInfo(
                    schema_name="public",
                    table_name="users",
                    column_name="email",
                    ordinal_position=2,
                    data_type="VARCHAR(255)",
                    is_nullable=False,
                ),
                ColumnInfo(
                    schema_name="public",
                    table_name="users",
                    column_name="created_at",
                    ordinal_position=3,
                    data_type="TIMESTAMP WITH TIME ZONE",
                    is_nullable=False,
                    default_expression="CURRENT_TIMESTAMP",
                ),
            ],
            "public.orders": [
                ColumnInfo(
                    schema_name="public",
                    table_name="orders",
                    column_name="id",
                    ordinal_position=1,
                    data_type="BIGINT",
                    is_nullable=False,
                    is_identity=True,
                ),
                ColumnInfo(
                    schema_name="public",
                    table_name="orders",
                    column_name="user_id",
                    ordinal_position=2,
                    data_type="BIGINT",
                    is_nullable=False,
                ),
                ColumnInfo(
                    schema_name="public",
                    table_name="orders",
                    column_name="amount_cents",
                    ordinal_position=3,
                    data_type="INTEGER",
                    is_nullable=False,
                ),
            ],
        }
        self.pks = custom_pks or {
            "public.users": PrimaryKeyInfo(
                constraint_name="pk_users",
                schema_name="public",
                table_name="users",
                column_names=["id"],
            ),
            "public.orders": PrimaryKeyInfo(
                constraint_name="pk_orders",
                schema_name="public",
                table_name="orders",
                column_names=["id"],
            ),
        }
        self.fks = custom_fks or {
            "public.orders": [
                ForeignKeyInfo(
                    constraint_name="fk_orders_users",
                    schema_name="public",
                    table_name="orders",
                    column_names=["user_id"],
                    referenced_schema="public",
                    referenced_table="users",
                    referenced_columns=["id"],
                    on_delete="CASCADE",
                )
            ]
        }
        self.unique_constraints = custom_unique_constraints or {
            "public.users": [
                UniqueConstraintInfo(
                    constraint_name="uq_users_email",
                    schema_name="public",
                    table_name="users",
                    column_names=["email"],
                )
            ]
        }
        self.check_constraints = custom_check_constraints or {
            "public.orders": [
                CheckConstraintInfo(
                    constraint_name="ck_orders_positive_amount",
                    schema_name="public",
                    table_name="orders",
                    check_clause="amount_cents > 0",
                )
            ]
        }
        self.indexes = custom_indexes or {
            "public.users": [
                IndexInfo(
                    index_name="idx_users_email",
                    schema_name="public",
                    table_name="users",
                    column_names=["email"],
                    is_unique=True,
                    index_type="BTREE",
                )
            ]
        }
        self.views = custom_views or [
            ViewInfo(
                schema_name="public",
                view_name="v_active_users",
                is_materialized=False,
                view_definition="SELECT id, email FROM users WHERE active = true",
            )
        ]

    @property
    def config(self) -> ConnectorConfig:
        return self._config

    @property
    def context(self) -> ConnectorContext:
        return self._context

    @property
    def state(self) -> ConnectionState:
        return self._lifecycle.state

    async def connect(self) -> None:
        self.connect_calls += 1
        self._context.check_active()
        self._lifecycle.transition_to(ConnectionState.CONNECTING)

        if self.simulate_latency_seconds > 0:
            await asyncio.sleep(self.simulate_latency_seconds)

        if self.simulate_timeout:
            self._lifecycle.transition_to(ConnectionState.FAILED, reason="Connection timed out")
            raise ConnectorTimeoutError("Simulated connection timeout.")

        if self.simulate_connect_failure:
            self._lifecycle.transition_to(ConnectionState.FAILED, reason="Unreachable host")
            raise ConnectorUnavailableError("Simulated connection failure.")

        if self.simulate_auth_failure:
            self._lifecycle.transition_to(ConnectionState.FAILED, reason="Auth rejected")
            raise ConnectorAuthenticationFailedError("Simulated authentication failure.")

        self._lifecycle.transition_to(ConnectionState.CONNECTED)

    async def close(self) -> None:
        self.close_calls += 1
        if self._lifecycle.state == ConnectionState.CLOSED:
            return

        self._lifecycle.transition_to(ConnectionState.CLOSING)
        self._lifecycle.transition_to(ConnectionState.CLOSED)

    async def test_connection(self) -> ConnectionTestResult:
        self.test_connection_calls += 1
        self._context.check_active()

        try:
            await self.connect()
            identity = await self.get_identity()
            caps = await self.get_capabilities()
            await self.close()
            return ConnectionTestResult(
                success=True,
                latency_ms=1.5,
                identity=identity,
                capabilities_summary=[c.value for c in caps.supported_capabilities()],
            )
        except Exception as exc:
            return ConnectionTestResult(
                success=False,
                latency_ms=0.5,
                error_code=getattr(exc, "error_code", "UNKNOWN_ERROR"),
                error_message=str(exc),
            )

    async def get_identity(self) -> DatabaseIdentity:
        self._context.check_active()
        return DatabaseIdentity(
            engine=self._config.engine,
            server_version="16.2 (Fake Test Server)",
            driver_version="fake-driver-1.0",
            provider=DatabaseProvider.GENERIC,
            database_name=self._config.database,
            connector_version="0.1.0-dev",
            server_capability_hints={"deterministic_mock": True},
        )

    async def get_capabilities(self) -> ConnectorCapabilities:
        self._context.check_active()
        caps_dict: dict[ConnectorCapability, CapabilitySupport] = {}

        for cap in ConnectorCapability:
            if cap in self.unsupported_caps:
                caps_dict[cap] = CapabilitySupport(
                    capability=cap,
                    status=CapabilityStatus.UNSUPPORTED,
                    reason="Mocked as unsupported for test scenario.",
                )
            else:
                caps_dict[cap] = CapabilitySupport(
                    capability=cap,
                    status=CapabilityStatus.SUPPORTED,
                )

        return ConnectorCapabilities(
            engine=self._config.engine,
            capabilities=caps_dict,
        )

    def _verify_connected(self) -> None:
        self._context.check_active()
        if self.simulate_permission_denial:
            raise ConnectorPermissionDeniedError(
                "Simulated permission denied for catalog inspection."
            )
        if self.state != ConnectionState.CONNECTED:
            raise RuntimeError(f"Cannot inspect metadata while in state '{self.state.value}'.")

    async def list_schemas(self) -> list[SchemaInfo]:
        self._verify_connected()
        return sorted(self.schemas, key=lambda s: s.schema_name)

    async def list_tables(self, schema: str | None = None) -> list[TableInfo]:
        self._verify_connected()
        self.inspected_tables_calls += 1
        filtered = self.tables
        if schema:
            filtered = [t for t in filtered if t.schema_name == schema]
        return sorted(filtered, key=lambda t: (t.schema_name, t.table_name))

    async def list_columns(self, schema: str | None, table: str) -> list[ColumnInfo]:
        self._verify_connected()
        key = f"{schema or 'public'}.{table}"
        cols = self.columns.get(key, [])
        return sorted(cols, key=lambda c: c.ordinal_position)

    async def get_primary_key(self, schema: str | None, table: str) -> PrimaryKeyInfo | None:
        self._verify_connected()
        key = f"{schema or 'public'}.{table}"
        return self.pks.get(key)

    async def list_foreign_keys(self, schema: str | None, table: str) -> list[ForeignKeyInfo]:
        self._verify_connected()
        key = f"{schema or 'public'}.{table}"
        return self.fks.get(key, [])

    async def list_unique_constraints(
        self, schema: str | None, table: str
    ) -> list[UniqueConstraintInfo]:
        self._verify_connected()
        key = f"{schema or 'public'}.{table}"
        return self.unique_constraints.get(key, [])

    async def list_check_constraints(
        self, schema: str | None, table: str
    ) -> list[CheckConstraintInfo]:
        self._verify_connected()
        key = f"{schema or 'public'}.{table}"
        return self.check_constraints.get(key, [])

    async def list_indexes(self, schema: str | None, table: str) -> list[IndexInfo]:
        self._verify_connected()
        key = f"{schema or 'public'}.{table}"
        return sorted(self.indexes.get(key, []), key=lambda idx: idx.index_name)

    async def list_views(self, schema: str | None = None) -> list[ViewInfo]:
        self._verify_connected()
        filtered = self.views
        if schema:
            filtered = [v for v in filtered if v.schema_name == schema]
        return sorted(filtered, key=lambda v: (v.schema_name, v.view_name))

    async def __aenter__(self) -> FakeDatabaseConnector:
        await self.connect()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> None:
        await self.close()
