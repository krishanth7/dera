"""DERA PostgreSQL Connector — Secure Connection Lifecycle & TLS Manager.

Establishes and manages asyncpg database connections with strict TLS verification,
SSRF target validation, statement timeout enforcement, and read-only session locking.
"""

from __future__ import annotations

import asyncio
import os
import ssl
from typing import Any

import asyncpg

from dera_connectors.context import CancellationToken
from dera_connectors.errors import (
    ConnectorCancelledError,
    ConnectorError,
    ConnectorTLSError,
)
from dera_connectors.postgresql.configuration import PostgresConnectorConfig
from dera_connectors.postgresql.errors import map_postgres_error
from dera_connectors.security import validate_network_target


def create_postgres_ssl_context(config: PostgresConnectorConfig) -> ssl.SSLContext | bool:
    """Create a configured SSLContext or boolean based on TLSSettings.

    Parameters
    ----------
    config : PostgresConnectorConfig
        Connector configuration containing TLSSettings.

    Returns
    -------
    ssl.SSLContext | bool
        Configured SSLContext or boolean for asyncpg.
    """
    tls = config.tls
    mode = tls.ssl_mode.lower()

    if mode == "disable":
        return False

    if mode in ("prefer", "allow") and not tls.ca_cert_path and not tls.client_cert_path:
        # Default asyncpg SSL flag
        return True

    # Standard SSLContext configuration
    try:
        ctx = ssl.create_default_context(
            purpose=ssl.Purpose.SERVER_AUTH,
            cafile=tls.ca_cert_path
            if tls.ca_cert_path and os.path.exists(tls.ca_cert_path)
            else None,
        )

        if mode == "require":
            # Encrypted transport without verifying server certificate or hostname
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
        elif mode == "verify-ca":
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_REQUIRED
        elif mode == "verify-full":
            ctx.check_hostname = tls.verify_hostname
            ctx.verify_mode = ssl.CERT_REQUIRED
        else:
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE

        if tls.client_cert_path and tls.client_key_path:
            if os.path.exists(tls.client_cert_path) and os.path.exists(tls.client_key_path):
                ctx.load_cert_chain(
                    certfile=tls.client_cert_path,
                    keyfile=tls.client_key_path,
                )

        return ctx
    except Exception as exc:
        raise ConnectorTLSError(
            message=f"Failed to initialize PostgreSQL SSL context: {exc}",
            ssl_mode=mode,
        ) from exc


class PostgresConnectionManager:
    """Manages an individual asyncpg connection lifecycle and session security."""

    def __init__(self, config: PostgresConnectorConfig) -> None:
        self._config = config
        self._connection: asyncpg.Connection | None = None
        self._lock = asyncio.Lock()

    @property
    def is_connected(self) -> bool:
        """Return True if connection is established and open."""
        return self._connection is not None and not self._connection.is_closed()

    @property
    def raw_connection(self) -> asyncpg.Connection:
        """Return raw asyncpg connection or raise error if not connected."""
        if self._connection is None or self._connection.is_closed():
            raise ConnectorError(message="PostgreSQL connection is not open.")
        return self._connection

    async def connect(
        self,
        cancellation_token: CancellationToken | None = None,
        allow_loopback: bool = False,
    ) -> None:
        """Establish network connection, negotiate TLS, and apply read-only session settings.

        Parameters
        ----------
        cancellation_token : CancellationToken | None
            Optional token allowing caller to cancel connection attempts.
        allow_loopback : bool
            Allow localhost connections (useful for local testing and containerized testbeds).
        """
        async with self._lock:
            if self.is_connected:
                return

            if cancellation_token and cancellation_token.is_cancelled:
                raise ConnectorCancelledError("Connection attempt cancelled before start.")

            # 1. SSRF target network validation
            host = self._config.host or "127.0.0.1"
            if not allow_loopback or host not in ("127.0.0.1", "localhost", "::1"):
                validate_network_target(host=host, allow_private_networks=allow_loopback)

            # 2. SSL context creation
            ssl_arg = create_postgres_ssl_context(self._config)

            # 3. Connection arguments
            kwargs = self._config.build_asyncpg_kwargs()
            kwargs["ssl"] = ssl_arg

            try:
                # 4. Open asyncpg connection with connect timeout
                self._connection = await asyncio.wait_for(
                    asyncpg.connect(**kwargs),
                    timeout=self._config.timeouts.connect_timeout_seconds,
                )

                # 5. Session-level security hardening:
                #    Strictly enforce read-only transaction mode and statement timeout
                timeout_ms = self._config.statement_timeout_ms
                await self._connection.execute(
                    "SET SESSION CHARACTERISTICS AS TRANSACTION READ ONLY;"
                )
                await self._connection.execute(f"SET statement_timeout = {int(timeout_ms)};")

            except Exception as exc:
                if self._connection is not None and not self._connection.is_closed():
                    try:
                        await self._connection.close(timeout=2.0)
                    except Exception:
                        pass
                self._connection = None
                raise map_postgres_error(
                    exc,
                    operation="connect",
                    details={
                        "host": host,
                        "port": self._config.port or 5432,
                        "database": self._config.database,
                    },
                ) from exc

    async def close(self) -> None:
        """Idempotently close the asyncpg connection and release resources."""
        async with self._lock:
            conn = self._connection
            self._connection = None
            if conn is not None:
                try:
                    is_closed = False
                    if hasattr(conn, "is_closed"):
                        res = conn.is_closed()
                        if asyncio.iscoroutine(res):
                            res = await res
                        if isinstance(res, bool):
                            is_closed = res
                    if not is_closed and hasattr(conn, "close"):
                        res = conn.close(timeout=2.0)
                        if asyncio.iscoroutine(res):
                            await res
                except Exception:
                    pass

    async def fetch(
        self,
        query: str,
        *args: Any,
        cancellation_token: CancellationToken | None = None,
        timeout: float | None = None,
    ) -> list[asyncpg.Record]:
        """Execute a read-only query and return records with timeout and cancellation checks."""
        if not self.is_connected:
            raise ConnectorError(message="Cannot execute query: PostgreSQL connection is closed.")

        if cancellation_token and cancellation_token.is_cancelled:
            raise ConnectorCancelledError("Query execution cancelled.")

        effective_timeout = timeout or self._config.timeouts.query_timeout_seconds

        try:
            return await asyncio.wait_for(
                self.raw_connection.fetch(query, *args),
                timeout=effective_timeout,
            )
        except Exception as exc:
            raise map_postgres_error(
                exc,
                operation="fetch",
                details={"statement_timeout_seconds": effective_timeout},
            ) from exc

    async def fetchrow(
        self,
        query: str,
        *args: Any,
        cancellation_token: CancellationToken | None = None,
        timeout: float | None = None,
    ) -> asyncpg.Record | None:
        """Execute a read-only query and return a single row or None."""
        if not self.is_connected:
            raise ConnectorError(message="Cannot execute query: PostgreSQL connection is closed.")

        if cancellation_token and cancellation_token.is_cancelled:
            raise ConnectorCancelledError("Query execution cancelled.")

        effective_timeout = timeout or self._config.timeouts.query_timeout_seconds

        try:
            return await asyncio.wait_for(
                self.raw_connection.fetchrow(query, *args),
                timeout=effective_timeout,
            )
        except Exception as exc:
            raise map_postgres_error(
                exc,
                operation="fetchrow",
                details={"statement_timeout_seconds": effective_timeout},
            ) from exc
