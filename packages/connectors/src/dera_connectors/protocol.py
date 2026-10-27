"""DERA Connectors — Universal Database Connector Protocol.

Defines the core typed Protocol interface and asynchronous context management contract
that all database connector adapters must satisfy.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from dera_connectors.capabilities import ConnectorCapabilities
from dera_connectors.configuration import ConnectorConfig
from dera_connectors.context import ConnectorContext
from dera_connectors.engine import DatabaseIdentity
from dera_connectors.lifecycle import ConnectionState
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


@runtime_checkable
class DatabaseConnector(Protocol):
    """Universal asynchronous database connector protocol.

    All database-specific adapters (PostgreSQL, SQLite, MySQL, MariaDB) and test
    fakes implement this protocol to provide deterministic, read-only metadata inspection.
    """

    @property
    def config(self) -> ConnectorConfig:
        """Return the connector's immutable configuration."""
        ...

    @property
    def context(self) -> ConnectorContext:
        """Return the connector's bound execution and tenant context."""
        ...

    @property
    def state(self) -> ConnectionState:
        """Return the current connection lifecycle state."""
        ...

    async def connect(self) -> None:
        """Establish the underlying database connection and initialize read-only session state.

        Raises
        ------
        ConnectorUnavailableError
            If network connection fails.
        ConnectorAuthenticationFailedError
            If credentials are rejected.
        ConnectorTLSError
            If TLS negotiation fails.
        """
        ...

    async def close(self) -> None:
        """Close the database connection and release all driver resources."""
        ...

    async def test_connection(self) -> ConnectionTestResult:
        """Execute a lightweight non-intrusive probe to verify connectivity and credentials.

        Returns
        -------
        ConnectionTestResult
            Structured result containing success status, latency, and server identity.
        """
        ...

    async def get_identity(self) -> DatabaseIdentity:
        """Return the database engine fingerprint, server version, and driver info.

        Returns
        -------
        DatabaseIdentity
            Sanitized database identity object.
        """
        ...

    async def get_capabilities(self) -> ConnectorCapabilities:
        """Discover and return supported metadata inspection capabilities for this connection.

        Returns
        -------
        ConnectorCapabilities
            Capability matrix reflecting engine and credential permissions.
        """
        ...

    async def list_schemas(self) -> list[SchemaInfo]:
        """Enumerate database schemas or namespaces in deterministic alphabetical order.

        Returns
        -------
        list[SchemaInfo]
            Ordered list of schema descriptors.
        """
        ...

    async def list_tables(self, schema: str | None = None) -> list[TableInfo]:
        """Enumerate tables in deterministic order (by schema and table name).

        Parameters
        ----------
        schema : str | None
            Optional schema filter. If None, enumerates tables across accessible schemas.

        Returns
        -------
        list[TableInfo]
            Ordered list of table descriptors.
        """
        ...

    async def list_columns(self, schema: str | None, table: str) -> list[ColumnInfo]:
        """Inspect table columns in deterministic ordinal order.

        Parameters
        ----------
        schema : str | None
            Schema name owning the table.
        table : str
            Table identifier.

        Returns
        -------
        list[ColumnInfo]
            Ordered list of column metadata entries.
        """
        ...

    async def get_primary_key(self, schema: str | None, table: str) -> PrimaryKeyInfo | None:
        """Inspect primary key constraint for a table.

        Parameters
        ----------
        schema : str | None
            Schema name.
        table : str
            Table name.

        Returns
        -------
        PrimaryKeyInfo | None
            Primary key metadata or None if table has no primary key.
        """
        ...

    async def list_foreign_keys(self, schema: str | None, table: str) -> list[ForeignKeyInfo]:
        """Inspect foreign key constraints for a table in deterministic order.

        Parameters
        ----------
        schema : str | None
            Schema name.
        table : str
            Table name.

        Returns
        -------
        list[ForeignKeyInfo]
            Ordered list of foreign key relationships.
        """
        ...

    async def list_unique_constraints(
        self, schema: str | None, table: str
    ) -> list[UniqueConstraintInfo]:
        """Inspect unique constraints for a table in deterministic order.

        Parameters
        ----------
        schema : str | None
            Schema name.
        table : str
            Table name.

        Returns
        -------
        list[UniqueConstraintInfo]
            Ordered list of unique constraints.
        """
        ...

    async def list_check_constraints(
        self, schema: str | None, table: str
    ) -> list[CheckConstraintInfo]:
        """Inspect check constraints for a table in deterministic order.

        Parameters
        ----------
        schema : str | None
            Schema name.
        table : str
            Table name.

        Returns
        -------
        list[CheckConstraintInfo]
            Ordered list of check constraints.
        """
        ...

    async def list_indexes(self, schema: str | None, table: str) -> list[IndexInfo]:
        """Inspect secondary indexes for a table in deterministic order.

        Parameters
        ----------
        schema : str | None
            Schema name.
        table : str
            Table name.

        Returns
        -------
        list[IndexInfo]
            Ordered list of index metadata.
        """
        ...

    async def list_views(self, schema: str | None = None) -> list[ViewInfo]:
        """Inspect views and materialized views in deterministic order.

        Parameters
        ----------
        schema : str | None
            Optional schema filter.

        Returns
        -------
        list[ViewInfo]
            Ordered list of view descriptors.
        """
        ...

    async def __aenter__(self) -> DatabaseConnector:
        """Enter asynchronous resource context; establishes connection."""
        ...

    async def __aexit__(
        self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: Any
    ) -> None:
        """Exit asynchronous resource context; guarantees connection teardown."""
        ...
