"""DERA Core — Structured Domain Exceptions.

All exceptions raised by DERA core models, graph algorithms, diagnostics,
and connector interfaces inherit from DeraError.
"""

from typing import Any


class DeraError(Exception):
    """Base exception for all DERA domain errors."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def to_dict(self) -> dict[str, Any]:
        """Convert exception to structured dictionary for serialization."""
        return {
            "error_type": self.__class__.__name__,
            "message": self.message,
            "details": self.details,
        }


class SchemaParsingError(DeraError):
    """Raised when schema extraction, DDL parsing, or metadata decoding fails."""

    pass


class CycleDetectedError(DeraError):
    """Raised when circular foreign key dependencies prevent topological ordering."""

    def __init__(self, message: str, cycle_path: list | None = None) -> None:
        super().__init__(message, details={"cycle_path": cycle_path or []})
        self.cycle_path = cycle_path or []


class DiagnosticRuleError(DeraError):
    """Raised when an internal diagnostic rule execution fails."""

    pass


class ConnectorError(DeraError):
    """Base exception for database connector failures."""

    pass


class ReadOnlyViolationError(ConnectorError):
    """Raised when a non-read-only query or mutation is attempted against a target database."""

    pass


class ConnectionAuthenticationError(ConnectorError):
    """Raised when database connection authentication fails."""

    pass


class ConfigurationError(DeraError):
    """Raised when platform or environment configuration is invalid."""

    pass
