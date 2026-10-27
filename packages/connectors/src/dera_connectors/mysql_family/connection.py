"""DERA MySQL-Family Connectors — Secure Connection & Session Manager.

Manages PyMySQL database connection lifecycles via asyncio.to_thread execution,
enforcing SSRF destination boundaries, TLS certificate validation, statement
deadlines, and strict read-only session locking.
"""

from __future__ import annotations

import asyncio
from typing import Any

import pymysql
import pymysql.cursors

from dera_connectors.configuration import ConnectorConfig
from dera_connectors.context import CancellationToken
from dera_connectors.errors import (
    ConnectorCancelledError,
    ConnectorError,
)
from dera_connectors.mysql_family.errors import map_mysql_family_error
from dera_connectors.mysql_family.security import (
    build_mysql_read_only_session_sql,
    build_mysql_ssl_context,
    validate_mysql_destination,
)


class MySqlFamilyConnectionManager:
    """Manages an individual PyMySQL connection with thread-pool async bridging."""

    def __init__(self, config: ConnectorConfig) -> None:
        """Initialize connection manager with typed connector configuration.

        Parameters
        ----------
        config : ConnectorConfig
            Typed connection configuration specifying host, port, database, credentials,
            TLS settings, and operation timeouts.
        """
        self._config = config
        self._connection: pymysql.Connection | None = None
        self._lock = asyncio.Lock()

    @property
    def is_connected(self) -> bool:
        """Return True if connection is established and healthy."""
        conn = self._connection
        if conn is None:
            return False
        return bool(conn.open)

    @property
    def raw_connection(self) -> pymysql.Connection:
        """Return the raw PyMySQL connection instance.

        Raises
        ------
        ConnectorError
            If connection has not been established or has been closed.
        """
        if self._connection is None or not self._connection.open:
            raise ConnectorError(message="MySQL/MariaDB connection is not open.")
        return self._connection

    async def connect(
        self,
        cancellation_token: CancellationToken | None = None,
        allow_loopback: bool = False,
    ) -> None:
        """Establish network connection, negotiate TLS, and enforce read-only session modes.

        Parameters
        ----------
        cancellation_token : CancellationToken | None
            Optional cancellation token allowing caller to abort pending connection.
        allow_loopback : bool
            Whether loopback connections (127.0.0.1) are permitted for testing.

        Raises
        ------
        ConnectorCancelledError
            If connection was aborted via cancellation token.
        ConnectorSecurityViolationError
            If target host violates SSRF or private network rules.
        ConnectorError
            If network connection, TLS, or authentication fails.
        """
        async with self._lock:
            if self.is_connected:
                return

            if cancellation_token and cancellation_token.is_cancelled:
                raise ConnectorCancelledError("Connection attempt cancelled before start.")

            host = self._config.host or "127.0.0.1"
            port = self._config.port or 3306

            # 1. SSRF target boundary validation
            validate_mysql_destination(
                host=host,
                port=port,
                allow_loopback=allow_loopback,
            )

            # 2. TLS SSLContext creation
            ssl_ctx = build_mysql_ssl_context(self._config.tls)

            # 3. Build PyMySQL connect parameters
            connect_kwargs: dict[str, Any] = {
                "host": host,
                "port": port,
                "user": self._config.username or "root",
                "password": (
                    self._config.password.get_secret_value() if self._config.password else ""
                ),
                "database": self._config.database,
                "charset": "utf8mb4",
                "cursorclass": pymysql.cursors.DictCursor,
                "connect_timeout": int(self._config.timeouts.connect_timeout_seconds),
                "read_timeout": int(self._config.timeouts.query_timeout_seconds),
                "write_timeout": int(self._config.timeouts.query_timeout_seconds),
                "autocommit": True,
            }
            if ssl_ctx is not None:
                connect_kwargs["ssl"] = ssl_ctx

            try:
                # 4. Open PyMySQL connection in thread pool
                connect_timeout = self._config.timeouts.connect_timeout_seconds
                self._connection = await asyncio.wait_for(
                    asyncio.to_thread(pymysql.connect, **connect_kwargs),
                    timeout=connect_timeout,
                )

                # 5. Session-level security hardening & read-only enforcement
                timeout_ms = int(self._config.timeouts.query_timeout_seconds * 1000)
                hardening_statements = build_mysql_read_only_session_sql(timeout_ms=timeout_ms)

                def _apply_session_hardening(conn: pymysql.Connection) -> None:
                    with conn.cursor() as cursor:
                        for stmt in hardening_statements:
                            try:
                                cursor.execute(stmt)
                            except Exception:
                                # Non-fatal if specific variable (like max_execution_time) is unsupported
                                pass

                await asyncio.to_thread(_apply_session_hardening, self._connection)

            except Exception as exc:
                if self._connection is not None:
                    try:
                        await asyncio.to_thread(self._connection.close)
                    except Exception:
                        pass
                self._connection = None
                raise map_mysql_family_error(
                    exc,
                    database=self._config.database,
                    host=host,
                    port=port,
                ) from exc

    async def close(self) -> None:
        """Idempotently close the database connection and release resources."""
        async with self._lock:
            conn = self._connection
            self._connection = None
            if conn is not None and conn.open:
                try:
                    await asyncio.to_thread(conn.close)
                except Exception:
                    pass

    async def fetch(
        self,
        query: str,
        args: tuple[Any, ...] | list[Any] | None = None,
        cancellation_token: CancellationToken | None = None,
        timeout: float | None = None,
    ) -> list[dict[str, Any]]:
        """Execute a read-only metadata query and return all result rows as dicts.

        Parameters
        ----------
        query : str
            Pre-reviewed, parameterized SQL query.
        args : tuple | list | None
            Query parameter substitutions.
        cancellation_token : CancellationToken | None
            Optional cancellation token.
        timeout : float | None
            Execution timeout in seconds.

        Returns
        -------
        list[dict[str, Any]]
            Query result rows.
        """
        if not self.is_connected:
            raise ConnectorError(message="Cannot execute query: Connection is closed.")

        if cancellation_token and cancellation_token.is_cancelled:
            raise ConnectorCancelledError("Query execution cancelled.")

        conn = self.raw_connection
        effective_timeout = timeout or self._config.timeouts.query_timeout_seconds

        def _execute_fetch() -> list[dict[str, Any]]:
            with conn.cursor() as cursor:
                cursor.execute(query, args or ())
                return cursor.fetchall()

        try:
            return await asyncio.wait_for(
                asyncio.to_thread(_execute_fetch),
                timeout=effective_timeout,
            )
        except Exception as exc:
            raise map_mysql_family_error(
                exc,
                database=self._config.database,
                host=self._config.host or "",
                port=self._config.port or 3306,
            ) from exc

    async def fetchrow(
        self,
        query: str,
        args: tuple[Any, ...] | list[Any] | None = None,
        cancellation_token: CancellationToken | None = None,
        timeout: float | None = None,
    ) -> dict[str, Any] | None:
        """Execute a read-only metadata query and return the first row as a dict, or None.

        Parameters
        ----------
        query : str
            Pre-reviewed, parameterized SQL query.
        args : tuple | list | None
            Query parameter substitutions.
        cancellation_token : CancellationToken | None
            Optional cancellation token.
        timeout : float | None
            Execution timeout in seconds.

        Returns
        -------
        dict[str, Any] | None
            First result row, or None if no rows matched.
        """
        if not self.is_connected:
            raise ConnectorError(message="Cannot execute query: Connection is closed.")

        if cancellation_token and cancellation_token.is_cancelled:
            raise ConnectorCancelledError("Query execution cancelled.")

        conn = self.raw_connection
        effective_timeout = timeout or self._config.timeouts.query_timeout_seconds

        def _execute_fetchone() -> dict[str, Any] | None:
            with conn.cursor() as cursor:
                cursor.execute(query, args or ())
                return cursor.fetchone()

        try:
            return await asyncio.wait_for(
                asyncio.to_thread(_execute_fetchone),
                timeout=effective_timeout,
            )
        except Exception as exc:
            raise map_mysql_family_error(
                exc,
                database=self._config.database,
                host=self._config.host or "",
                port=self._config.port or 3306,
            ) from exc
