"""DERA SQLite Connector — Read-Only Connection Manager & Lifecycle.

Manages the lifecycle of local SQLite 3 connections with strict read-only URI modes,
PRAGMA query_only enforcement, non-blocking asynchronous thread offloading, and
cancellation interrupts.
"""

from __future__ import annotations

import asyncio
import sqlite3
from typing import Any

from dera_connectors.lifecycle import ConnectionLifecycle, ConnectionState
from dera_connectors.sqlite.configuration import SqliteConnectorConfig
from dera_connectors.sqlite.errors import map_sqlite_error
from dera_connectors.sqlite.filesystem import build_sqlite_readonly_uri, validate_sqlite_path


class SqliteConnectionManager:
    """Manages an asynchronous, read-only SQLite 3 connection."""

    def __init__(self, config: SqliteConnectorConfig) -> None:
        self._config = config
        self._lifecycle = ConnectionLifecycle()
        self._conn: sqlite3.Connection | None = None
        self._canonical_path: str = ""
        self._lock = asyncio.Lock()

    @property
    def is_connected(self) -> bool:
        """Return True if connection is active and ready."""
        return self._lifecycle.state == ConnectionState.CONNECTED and self._conn is not None

    @property
    def canonical_path(self) -> str:
        """Return the validated canonical filesystem path."""
        return self._canonical_path

    async def connect(self, cancellation_token: Any | None = None) -> None:
        """Establish a read-only SQLite database connection."""
        if cancellation_token and getattr(cancellation_token, "is_cancelled", False):
            from dera_connectors.errors import ConnectorCancelledError

            raise ConnectorCancelledError("Connection cancelled by user.")

        async with self._lock:
            if self.is_connected:
                return

            self._lifecycle.transition_to(ConnectionState.CONNECTING)

            try:
                # 1. Validate and canonicalize filesystem path
                self._canonical_path = await asyncio.to_thread(
                    validate_sqlite_path,
                    self._config.database,
                    self._config.approved_storage_roots,
                    self._config.allow_memory_databases,
                )

                # 2. Build secure read-only URI
                uri = build_sqlite_readonly_uri(
                    self._canonical_path,
                    immutable=self._config.immutable_snapshot,
                )

                # 3. Connect via worker thread
                def _open_connection() -> sqlite3.Connection:
                    conn = sqlite3.connect(
                        uri,
                        uri=True,
                        timeout=self._config.timeouts.connect_timeout_seconds,
                        check_same_thread=False,
                    )
                    conn.row_factory = sqlite3.Row

                    # 4. Enforce read-only and busy timeout pragmas
                    conn.execute("PRAGMA query_only = ON;")
                    conn.execute(f"PRAGMA busy_timeout = {self._config.busy_timeout_ms};")
                    return conn

                self._conn = await asyncio.to_thread(_open_connection)
                self._lifecycle.transition_to(ConnectionState.CONNECTED)
            except Exception as exc:
                self._lifecycle.transition_to(ConnectionState.FAILED)
                await self._cleanup()
                raise map_sqlite_error(exc, database=self._config.database) from exc

    async def close(self) -> None:
        """Safely close active connection and release resources."""
        async with self._lock:
            if self._lifecycle.state in (ConnectionState.CLOSED, ConnectionState.FAILED):
                return
            self._lifecycle.transition_to(ConnectionState.CLOSING)
            await self._cleanup()
            self._lifecycle.transition_to(ConnectionState.CLOSED)

    async def execute_query(
        self,
        query: str,
        params: tuple[Any, ...] | list[Any] | None = None,
        timeout: float | None = None,
    ) -> list[sqlite3.Row]:
        """Execute a read-only query and return matching rows as sqlite3.Row objects.

        Parameters
        ----------
        query : str
            Approved introspection SQL statement.
        params : tuple | list | None
            Query parameters for safe parameter substitution.
        timeout : float | None
            Execution timeout in seconds (defaults to config query_timeout_seconds).

        Returns
        -------
        list[sqlite3.Row]
            Matching result rows.
        """
        if not self.is_connected or self._conn is None:
            await self.connect()

        assert self._conn is not None
        effective_timeout = timeout or self._config.timeouts.query_timeout_seconds

        def _run_query() -> list[sqlite3.Row]:
            assert self._conn is not None
            cursor = self._conn.cursor()
            try:
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                return cursor.fetchall()
            finally:
                cursor.close()

        try:
            return await asyncio.wait_for(
                asyncio.to_thread(_run_query),
                timeout=effective_timeout,
            )
        except TimeoutError as exc:
            # Interrupt running query in C runtime
            if self._conn:
                self._conn.interrupt()
            raise map_sqlite_error(exc, database=self._config.database) from exc
        except Exception as exc:
            raise map_sqlite_error(exc, database=self._config.database) from exc

    async def _cleanup(self) -> None:
        """Internal cleanup helper."""
        if self._conn is not None:
            try:
                await asyncio.to_thread(self._conn.close)
            except Exception:
                pass
            finally:
                self._conn = None
