"""DERA PostgreSQL Connector — Error Classification & SQLSTATE Mapping.

Maps asyncpg, PostgreSQL SQLSTATE codes, and network exceptions into strongly-typed
DERA Phase 5.1 domain errors without leaking raw credentials or connection strings.
"""

from __future__ import annotations

import asyncio
import ssl
from typing import Any

from dera_connectors.errors import (
    ConnectorAuthenticationFailedError,
    ConnectorCancelledError,
    ConnectorConnectionLostError,
    ConnectorError,
    ConnectorMetadataError,
    ConnectorPermissionDeniedError,
    ConnectorSecurityViolationError,
    ConnectorTimeoutError,
    ConnectorTLSError,
    ConnectorUnavailableError,
)
from dera_connectors.security import mask_sensitive_strings


def map_postgres_error(
    exc: BaseException,
    operation: str = "introspection",
    details: dict[str, Any] | None = None,
) -> ConnectorError:
    """Classify and transform an asyncpg or network exception into a DERA ConnectorError.

    Parameters
    ----------
    exc : BaseException
        The raw caught exception.
    operation : str
        The operation during which the failure occurred (e.g. 'connect', 'list_tables').
    details : dict[str, Any] | None
        Optional safe diagnostic context.

    Returns
    -------
    ConnectorError
        Standardized, sanitized domain exception.
    """
    safe_details = details.copy() if details else {}
    raw_message = mask_sensitive_strings(str(exc))
    exc_type_name = type(exc).__name__

    # 1. Cancellation
    if isinstance(exc, asyncio.CancelledError):
        return ConnectorCancelledError(
            message=f"PostgreSQL operation '{operation}' was cancelled by client request.",
            details=safe_details,
        )

    # 2. Timeout
    if isinstance(exc, (TimeoutError, asyncio.TimeoutError)):
        safe_details["timeout_seconds"] = safe_details.get("timeout_seconds", 30.0)
        safe_details["operation"] = operation
        return ConnectorTimeoutError(
            message=f"PostgreSQL operation '{operation}' timed out: {raw_message}",
            details=safe_details,
        )

    # 3. TLS / SSL Errors
    if isinstance(exc, (ssl.SSLError, ssl.CertificateError)):
        safe_details["ssl_mode"] = safe_details.get("ssl_mode", "require")
        return ConnectorTLSError(
            message=f"PostgreSQL TLS handshake failed during '{operation}': {raw_message}",
            details=safe_details,
        )

    # 4. Inspect asyncpg-specific attributes if available
    sqlstate = getattr(exc, "sqlstate", None)
    if sqlstate is None:
        # Check pgcode attribute sometimes used by postgres drivers
        sqlstate = getattr(exc, "pgcode", None)

    if sqlstate is not None:
        safe_details["sqlstate"] = sqlstate

        # Class 28 — Invalid Authorization Specification
        if sqlstate in ("28000", "28P01"):
            return ConnectorAuthenticationFailedError(
                message=f"PostgreSQL authentication failed: invalid username or password ({sqlstate}).",
                details=safe_details,
            )

        # Class 42501 — Insufficient Privilege
        if sqlstate == "42501":
            safe_details["permission"] = "CATALOG_READ"
            return ConnectorPermissionDeniedError(
                message=f"PostgreSQL permission denied for {safe_details.get('resource', 'catalog')} ({sqlstate}).",
                details=safe_details,
            )

        # Class 57014 — Query Canceled / Statement Timeout
        if sqlstate == "57014":
            return ConnectorTimeoutError(
                message=f"PostgreSQL statement cancelled or timed out: {raw_message}",
                details=safe_details,
            )

        # Class 25006 — Read-Only SQL Transaction Violation
        if sqlstate == "25006":
            return ConnectorSecurityViolationError(
                message=f"PostgreSQL read-only transaction rejected modification attempt: {raw_message}",
                details=safe_details,
            )

        # Class 08 — Connection Exceptions (08000, 08003, 08006, etc.)
        if sqlstate.startswith("08") or sqlstate in ("57P01", "57P02", "57P03"):
            return ConnectorConnectionLostError(
                message=f"PostgreSQL connection lost during '{operation}' ({sqlstate}): {raw_message}",
                details=safe_details,
            )

    # 5. Type name based mapping for asyncpg exceptions
    if (
        "InvalidAuthorizationSpecificationError" in exc_type_name
        or "InvalidPasswordError" in exc_type_name
    ):
        return ConnectorAuthenticationFailedError(
            message="PostgreSQL authentication failed: credentials rejected by server.",
            details=safe_details,
        )

    if "InsufficientPrivilegeError" in exc_type_name:
        safe_details["permission"] = "CATALOG_READ"
        return ConnectorPermissionDeniedError(
            message=f"PostgreSQL permission denied: {raw_message}",
            details=safe_details,
        )

    if "QueryCanceledError" in exc_type_name:
        return ConnectorTimeoutError(
            message=f"PostgreSQL statement timed out: {raw_message}",
            details=safe_details,
        )

    if "ReadOnlySqlTransactionError" in exc_type_name:
        return ConnectorSecurityViolationError(
            message=f"PostgreSQL transaction is read-only; mutation forbidden: {raw_message}",
            details=safe_details,
        )

    if any(
        err in exc_type_name
        for err in (
            "AdminShutdownError",
            "CrashShutdownError",
            "CannotConnectNowError",
            "ConnectionDoesNotExistError",
            "ConnectionResetError",
            "BrokenPipeError",
        )
    ):
        return ConnectorConnectionLostError(
            message=f"PostgreSQL connection lost: {raw_message}",
            details=safe_details,
        )

    if (
        isinstance(exc, (ConnectionRefusedError, OSError))
        or "CannotConnectNowError" in exc_type_name
    ):
        return ConnectorUnavailableError(
            message=f"PostgreSQL database is unavailable at target host: {raw_message}",
            details=safe_details,
        )

    # 6. Fallback domain error
    return ConnectorMetadataError(
        message=f"PostgreSQL catalog introspection error during '{operation}': {raw_message}",
        details=safe_details,
    )
