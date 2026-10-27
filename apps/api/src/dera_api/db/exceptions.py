"""DERA Database — Persistence Exceptions and Error Mapping.

Provides typed domain exceptions for database operations and mapping functions
that convert raw SQLAlchemy / asyncpg driver exceptions into RFC 9457-safe
DERA domain errors without leaking SQL statements, parameters, or credentials.
"""

import re
from typing import NoReturn

from sqlalchemy.exc import (
    IntegrityError,
    OperationalError,
)
from sqlalchemy.exc import (
    TimeoutError as SATimeoutError,
)

from dera_api.contracts.errors import ErrorCode
from dera_api.core.exceptions import (
    ConflictError,
    DependencyUnavailableError,
    DeraError,
)


def sanitize_database_error_message(message: str) -> str:
    """Mask credentials and internal connection strings in error messages.

    Parameters
    ----------
    message : str
        Raw error message from database driver or ORM.

    Returns
    -------
    str
        Sanitized message with passwords masked and sensitive details removed.
    """
    # Mask username:password@ in URIs
    sanitized = re.sub(r"://([^:]+):([^@]+)@", r"://\1:***@", message)
    # Strip detailed SQL parameter bindings if present
    sanitized = re.sub(r"\[parameters: [^\]]+\]", "[parameters: <redacted>]", sanitized)
    return sanitized


class DatabaseError(DeraError):
    """Base exception for all internal platform database errors."""

    def __init__(
        self, message: str, code: ErrorCode = ErrorCode.INTERNAL_ERROR, status_code: int = 500
    ) -> None:
        super().__init__(
            message=sanitize_database_error_message(message),
            code=code,
            status_code=status_code,
        )


class DatabaseConnectionError(DependencyUnavailableError):
    """Raised when the platform PostgreSQL database cannot be reached."""

    def __init__(self, message: str = "Platform database is temporarily unavailable") -> None:
        super().__init__(message=sanitize_database_error_message(message))


class DatabaseTimeoutError(DependencyUnavailableError):
    """Raised when a database query or connection acquisition times out."""

    def __init__(self, message: str = "Database operation timed out") -> None:
        super().__init__(message=sanitize_database_error_message(message))


class DatabaseConstraintViolationError(ConflictError):
    """Raised when an integrity, unique, check, or foreign key constraint is violated."""

    def __init__(self, message: str = "Database constraint violation") -> None:
        super().__init__(message=sanitize_database_error_message(message))


class DatabaseMigrationMismatchError(DatabaseError):
    """Raised when database schema version does not match ORM expectations."""

    def __init__(self, message: str = "Database schema migration mismatch detected") -> None:
        super().__init__(
            message=sanitize_database_error_message(message),
            code=ErrorCode.INTERNAL_ERROR,
            status_code=500,
        )


def map_database_exception(exc: Exception) -> DeraError:
    """Map a raw SQLAlchemy or driver exception into a sanitized DeraError.

    Parameters
    ----------
    exc : Exception
        Exception raised during a database operation.

    Returns
    -------
    DeraError
        Sanitized, classified DERA domain error suitable for client response.
    """
    if isinstance(exc, IntegrityError):
        # Unique constraint violation, foreign key failure, check constraint failure
        orig_msg = str(exc.orig) if hasattr(exc, "orig") and exc.orig else str(exc)
        if "unique" in orig_msg.lower() or "duplicate key" in orig_msg.lower():
            return DatabaseConstraintViolationError(
                "A record with the specified unique identifier already exists."
            )
        if "foreign key" in orig_msg.lower():
            return DatabaseConstraintViolationError("Referenced relation constraint failed.")
        if "not-null" in orig_msg.lower() or "not null" in orig_msg.lower():
            return DatabaseConstraintViolationError("Required non-null field constraint failed.")
        return DatabaseConstraintViolationError("Data integrity constraint violation.")

    if isinstance(exc, (SATimeoutError, TimeoutError)):
        return DatabaseTimeoutError("Database operation or connection timed out.")

    if isinstance(exc, OperationalError):
        return DatabaseConnectionError("Platform database connection failed or is unavailable.")

    if isinstance(exc, DeraError):
        return exc

    return DatabaseError(f"Database operation failed: {type(exc).__name__}")


def raise_mapped_database_exception(exc: Exception) -> NoReturn:
    """Map and immediately raise the sanitized DeraError.

    Parameters
    ----------
    exc : Exception
        Raw exception to map and raise.
    """
    raise map_database_exception(exc) from None
