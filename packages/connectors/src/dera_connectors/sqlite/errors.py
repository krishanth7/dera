"""DERA SQLite Connector — Error Taxonomy Mapping & Path Sanitization.

Translates native Python sqlite3 exceptions and operational faults into DERA Phase 5.1
typed ConnectorError domain models with strict filesystem path sanitization.
"""

from __future__ import annotations

import asyncio
import re
import sqlite3
from typing import Any

from dera_connectors.errors import (
    ConnectorCancelledError,
    ConnectorError,
    ConnectorInvalidConfigurationError,
    ConnectorMetadataError,
    ConnectorPermissionDeniedError,
    ConnectorSecurityViolationError,
    ConnectorTimeoutError,
    ConnectorUnavailableError,
)

# Regular expression to redact file paths from error text
_PATH_REDACT_REGEX = re.compile(
    r"(?:[a-zA-Z]:[\\/]|/)[^\s;'\"]+",
    re.IGNORECASE,
)


def sanitize_sqlite_error_message(message: str) -> str:
    """Sanitize error messages to prevent leakage of internal absolute paths.

    Parameters
    ----------
    message : str
        Raw exception message.

    Returns
    -------
    str
        Sanitized message with filesystem paths replaced by [REDACTED_PATH].
    """

    def _replace_path(match: re.Match[str]) -> str:
        matched = match.group(0)
        # Avoid redacting simple identifiers or SQL keywords
        if "/" in matched or "\\" in matched:
            return "[REDACTED_PATH]"
        return matched

    return _PATH_REDACT_REGEX.sub(_replace_path, message)


def map_sqlite_error(exc: Exception, database: str = "") -> ConnectorError:
    """Map a native sqlite3 or runtime exception into a Phase 5.1 ConnectorError.

    Parameters
    ----------
    exc : Exception
        Exception raised during SQLite introspection or connection.
    database : str
        Target database filename for diagnostics context.

    Returns
    -------
    ConnectorError
        Mapped, strongly-typed connector domain error.
    """
    if isinstance(exc, ConnectorError):
        return exc

    if isinstance(exc, (asyncio.CancelledError, TimeoutError)):
        return ConnectorCancelledError(
            "SQLite operation was cancelled or timed out.",
            details={"database": database},
        )

    raw_msg = str(exc)
    sanitized_msg = sanitize_sqlite_error_message(raw_msg)
    lower_msg = raw_msg.lower()

    details: dict[str, Any] = {
        "engine": "sqlite",
        "error_type": type(exc).__name__,
        "database": database,
    }

    # 1. Read-only violation or mutation attempt
    if (
        "readonly" in lower_msg
        or "query_only" in lower_msg
        or "attempt to write a readonly database" in lower_msg
    ):
        return ConnectorSecurityViolationError(
            f"Read-only security violation on SQLite database: {sanitized_msg}",
            details=details,
        )

    # 2. Permission denied by OS
    if "permission denied" in lower_msg:
        return ConnectorPermissionDeniedError(
            f"Permission denied accessing SQLite database: {sanitized_msg}",
            details=details,
        )

    # 3. Database locked or busy timeout
    if "database is locked" in lower_msg or "database is busy" in lower_msg:
        return ConnectorTimeoutError(
            f"SQLite database is locked or busy timeout exceeded: {sanitized_msg}",
            details=details,
        )

    # 4. Unable to open file or not found
    if "unable to open database file" in lower_msg or "cannot open" in lower_msg:
        return ConnectorUnavailableError(
            f"SQLite database file is unavailable or cannot be opened: {sanitized_msg}",
            details=details,
        )

    # 5. File is not a valid SQLite database or is corrupt
    if "file is not a database" in lower_msg or "database disk image is malformed" in lower_msg:
        return ConnectorMetadataError(
            f"SQLite database image is corrupt or not a valid database: {sanitized_msg}",
            details=details,
        )

    # 6. Schema and catalog errors
    if isinstance(exc, sqlite3.OperationalError):
        if "no such table" in lower_msg or "no such column" in lower_msg:
            return ConnectorMetadataError(
                f"SQLite catalog metadata object not found: {sanitized_msg}",
                details=details,
            )
        return ConnectorMetadataError(
            f"SQLite operational metadata error: {sanitized_msg}",
            details=details,
        )

    if isinstance(exc, sqlite3.DatabaseError):
        return ConnectorMetadataError(
            f"SQLite database error: {sanitized_msg}",
            details=details,
        )

    # 7. Fallback for unclassified configuration/usage errors
    if isinstance(exc, (ValueError, TypeError)):
        return ConnectorInvalidConfigurationError(
            f"Invalid SQLite connector configuration: {sanitized_msg}",
            details=details,
        )

    return ConnectorMetadataError(
        f"Unexpected SQLite connector error: {sanitized_msg}",
        details=details,
    )
