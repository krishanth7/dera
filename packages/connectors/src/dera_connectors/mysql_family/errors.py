"""DERA MySQL-Family Connectors — Error Mapping and Sanitization.

Maps PyMySQL and native MySQL/MariaDB error codes and exceptions into
DERA Phase 5.1 typed ConnectorError domain models with credential and
connection string masking.
"""

from __future__ import annotations

import asyncio
from typing import Any

from dera_connectors.errors import (
    ConnectorAuthenticationFailedError,
    ConnectorCancelledError,
    ConnectorError,
    ConnectorInvalidConfigurationError,
    ConnectorMetadataError,
    ConnectorPermissionDeniedError,
    ConnectorSecurityViolationError,
    ConnectorTimeoutError,
    ConnectorTLSError,
    ConnectorUnavailableError,
)
from dera_connectors.security import mask_sensitive_strings

# MySQL / MariaDB Error Code Constants
ER_DBACCESS_DENIED_ERROR = 1044
ER_ACCESS_DENIED_ERROR = 1045
ER_BAD_DB_ERROR = 1049
ER_TABLEACCESS_DENIED_ERROR = 1142
ER_COLUMNACCESS_DENIED_ERROR = 1143
ER_SPECIFIC_ACCESS_DENIED_ERROR = 1227
ER_QUERY_INTERRUPTED = 1317
ER_CON_COUNT_ERROR = 1040
ER_HOST_NOT_PRIVILEGED = 1130
ER_HOST_IS_BLOCKED = 1129
ER_QUERY_TIMEOUT = 3024
CR_CONNECTION_ERROR = 2002
CR_CONN_HOST_ERROR = 2003
CR_UNKNOWN_HOST = 2005
CR_SERVER_GONE_ERROR = 2006
CR_SERVER_LOST = 2013
CR_SSL_CONNECTION_ERROR = 2026


def map_mysql_family_error(
    exc: Exception,
    database: str = "",
    host: str = "",
    port: int = 3306,
) -> ConnectorError:
    """Map a native PyMySQL or runtime exception into a Phase 5.1 ConnectorError.

    Parameters
    ----------
    exc : Exception
        Raw exception raised by PyMySQL or Python runtime.
    database : str
        Target database/schema name for diagnostic context.
    host : str
        Target host for context.
    port : int
        Target port for context.

    Returns
    -------
    ConnectorError
        Strongly-typed DERA domain exception with masked credentials.
    """
    if isinstance(exc, ConnectorError):
        return exc

    if isinstance(exc, (ConnectorCancelledError, asyncio.CancelledError)):
        return ConnectorCancelledError(
            "MySQL operation cancelled by caller.",
            details={"database": database, "host": host, "port": port},
            cause=exc,
        )

    if isinstance(exc, (TimeoutError, asyncio.TimeoutError)):
        return ConnectorTimeoutError(
            f"MySQL connection or query timed out after configured deadline for database '{database}'.",
            details={"database": database, "host": host, "port": port},
            cause=exc,
        )

    # Inspect PyMySQL / MySQL error attributes
    errno = getattr(exc, "errno", None)
    if errno is None and hasattr(exc, "args") and exc.args and isinstance(exc.args[0], int):
        errno = exc.args[0]

    raw_msg = str(exc)
    sanitized_msg = mask_sensitive_strings(raw_msg)
    details: dict[str, Any] = {
        "database": database,
        "host": host,
        "port": port,
        "errno": errno,
        "error_code": errno,
    }

    # 1. Authentication failures
    if errno in (ER_ACCESS_DENIED_ERROR, ER_HOST_NOT_PRIVILEGED):
        return ConnectorAuthenticationFailedError(
            f"Authentication failed for user on database '{database}': {sanitized_msg}",
            details=details,
            cause=exc,
        )

    # 2. Permission denied
    if errno in (
        ER_DBACCESS_DENIED_ERROR,
        ER_TABLEACCESS_DENIED_ERROR,
        ER_COLUMNACCESS_DENIED_ERROR,
        ER_SPECIFIC_ACCESS_DENIED_ERROR,
    ):
        return ConnectorPermissionDeniedError(
            f"Access denied to inspect database objects: {sanitized_msg}",
            details=details,
            cause=exc,
        )

    # 3. Connection / Network unavailable
    if errno in (
        CR_CONNECTION_ERROR,
        CR_CONN_HOST_ERROR,
        CR_UNKNOWN_HOST,
        CR_SERVER_GONE_ERROR,
        CR_SERVER_LOST,
        ER_HOST_IS_BLOCKED,
        ER_CON_COUNT_ERROR,
    ):
        return ConnectorUnavailableError(
            f"MySQL server is unreachable at {host}:{port}: {sanitized_msg}",
            details=details,
            cause=exc,
        )

    # 4. TLS / SSL Connection Error
    if errno == CR_SSL_CONNECTION_ERROR or "ssl" in raw_msg.lower() or "tls" in raw_msg.lower():
        return ConnectorTLSError(
            f"TLS handshake or certificate verification failed for {host}:{port}: {sanitized_msg}",
            details=details,
            cause=exc,
        )

    # 5. Query execution timeouts
    if (
        errno == ER_QUERY_TIMEOUT
        or "max_execution_time" in raw_msg.lower()
        or "max_statement_time" in raw_msg.lower()
    ):
        return ConnectorTimeoutError(
            f"MySQL query execution exceeded timeout: {sanitized_msg}",
            details=details,
            cause=exc,
        )

    # 6. Query execution cancelled
    if errno == ER_QUERY_INTERRUPTED or "interrupted" in raw_msg.lower():
        return ConnectorCancelledError(
            f"MySQL query execution was cancelled: {sanitized_msg}",
            details=details,
            cause=exc,
        )

    # 6. Database / schema does not exist
    if errno == ER_BAD_DB_ERROR:
        return ConnectorInvalidConfigurationError(
            f"Database '{database}' does not exist on MySQL server: {sanitized_msg}",
            details=details,
            cause=exc,
        )

    # 7. Read-only mutation rejection
    if "read only" in raw_msg.lower() or "read-only" in raw_msg.lower():
        return ConnectorSecurityViolationError(
            f"Database mutation rejected by read-only security policy: {sanitized_msg}",
            details=details,
            cause=exc,
        )

    # Fallback to MetadataError
    return ConnectorMetadataError(
        f"MySQL metadata operation failed: {sanitized_msg}",
        details=details,
        cause=exc,
    )
