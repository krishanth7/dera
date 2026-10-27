"""DERA Connectors — Unified Error Taxonomy & Exception Hierarchy.

Defines standardized, safe connector exceptions mapped to RFC 9457-compatible error
codes. Automatically sanitizes raw database errors to prevent leaking connection strings,
credentials, or internal network topology.
"""

from enum import StrEnum
from typing import Any

from dera_connectors.security import mask_sensitive_strings


class ConnectorErrorCode(StrEnum):
    """Standardized connector error codes for diagnostic classification."""

    CONNECTOR_UNAVAILABLE = "CONNECTOR_UNAVAILABLE"
    CONNECTOR_AUTHENTICATION_FAILED = "CONNECTOR_AUTHENTICATION_FAILED"
    CONNECTOR_PERMISSION_DENIED = "CONNECTOR_PERMISSION_DENIED"
    CONNECTOR_TIMEOUT = "CONNECTOR_TIMEOUT"
    CONNECTOR_TLS_ERROR = "CONNECTOR_TLS_ERROR"
    CONNECTOR_UNSUPPORTED_ENGINE = "CONNECTOR_UNSUPPORTED_ENGINE"
    CONNECTOR_UNSUPPORTED_CAPABILITY = "CONNECTOR_UNSUPPORTED_CAPABILITY"
    CONNECTOR_INVALID_CONFIGURATION = "CONNECTOR_INVALID_CONFIGURATION"
    CONNECTOR_CONNECTION_LOST = "CONNECTOR_CONNECTION_LOST"
    CONNECTOR_METADATA_ERROR = "CONNECTOR_METADATA_ERROR"
    CONNECTOR_CANCELLED = "CONNECTOR_CANCELLED"
    CONNECTOR_SECURITY_VIOLATION = "CONNECTOR_SECURITY_VIOLATION"


class ConnectorError(Exception):
    """Base class for all DERA database connector exceptions."""

    def __init__(
        self,
        message: str,
        error_code: ConnectorErrorCode,
        details: dict[str, Any] | None = None,
        cause: Exception | None = None,
    ) -> None:
        sanitized_message = mask_sensitive_strings(message)
        super().__init__(sanitized_message)
        self.message = sanitized_message
        self.error_code = error_code
        self.details = details or {}
        self.cause = cause

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(code={self.error_code.value}, message={self.message!r})"


class ConnectorUnavailableError(ConnectorError):
    """Raised when target database cannot be reached on the network."""

    def __init__(self, message: str = "Database server is unreachable.", **kwargs: Any) -> None:
        super().__init__(
            message=message,
            error_code=ConnectorErrorCode.CONNECTOR_UNAVAILABLE,
            **kwargs,
        )


class ConnectorAuthenticationFailedError(ConnectorError):
    """Raised when authentication credentials (username, password, cert) are rejected."""

    def __init__(self, message: str = "Database authentication failed.", **kwargs: Any) -> None:
        super().__init__(
            message=message,
            error_code=ConnectorErrorCode.CONNECTOR_AUTHENTICATION_FAILED,
            **kwargs,
        )


class ConnectorPermissionDeniedError(ConnectorError):
    """Raised when database credentials lack sufficient permissions to read catalogs or metadata."""

    def __init__(
        self,
        message: str = "Insufficient permissions to inspect database metadata.",
        **kwargs: Any,
    ) -> None:
        super().__init__(
            message=message,
            error_code=ConnectorErrorCode.CONNECTOR_PERMISSION_DENIED,
            **kwargs,
        )


class ConnectorTimeoutError(ConnectorError):
    """Raised when connection or query execution exceeds timeout thresholds."""

    def __init__(
        self,
        message: str = "Connector operation timed out.",
        **kwargs: Any,
    ) -> None:
        super().__init__(
            message=message,
            error_code=ConnectorErrorCode.CONNECTOR_TIMEOUT,
            **kwargs,
        )


class ConnectorTLSError(ConnectorError):
    """Raised when TLS handshake, certificate validation, or cipher negotiation fails."""

    def __init__(
        self,
        message: str = "TLS connection failed or certificate validation error.",
        **kwargs: Any,
    ) -> None:
        super().__init__(
            message=message,
            error_code=ConnectorErrorCode.CONNECTOR_TLS_ERROR,
            **kwargs,
        )


class ConnectorUnsupportedEngineError(ConnectorError):
    """Raised when an unrecognized or unsupported database dialect is requested."""

    def __init__(
        self,
        engine: str,
        message: str | None = None,
        **kwargs: Any,
    ) -> None:
        msg = message or f"Database engine '{engine}' is not supported by DERA connectors."
        super().__init__(
            message=msg,
            error_code=ConnectorErrorCode.CONNECTOR_UNSUPPORTED_ENGINE,
            details={"requested_engine": engine},
            **kwargs,
        )


class ConnectorUnsupportedCapabilityError(ConnectorError):
    """Raised when caller invokes a metadata inspection method not supported by this engine/driver."""

    def __init__(
        self,
        capability: str,
        message: str | None = None,
        **kwargs: Any,
    ) -> None:
        msg = message or f"Capability '{capability}' is unsupported by this connector."
        super().__init__(
            message=msg,
            error_code=ConnectorErrorCode.CONNECTOR_UNSUPPORTED_CAPABILITY,
            details={"capability": capability},
            **kwargs,
        )


class ConnectorInvalidConfigurationError(ConnectorError):
    """Raised when connection configuration parameters are malformed or invalid."""

    def __init__(
        self,
        message: str = "Invalid connector configuration provided.",
        **kwargs: Any,
    ) -> None:
        super().__init__(
            message=message,
            error_code=ConnectorErrorCode.CONNECTOR_INVALID_CONFIGURATION,
            **kwargs,
        )


class ConnectorConnectionLostError(ConnectorError):
    """Raised when an established connection drops during an ongoing operation."""

    def __init__(
        self,
        message: str = "Connection to database lost during operation.",
        **kwargs: Any,
    ) -> None:
        super().__init__(
            message=message,
            error_code=ConnectorErrorCode.CONNECTOR_CONNECTION_LOST,
            **kwargs,
        )


class ConnectorMetadataError(ConnectorError):
    """Raised when catalog metadata is corrupted, incomplete, or fails parsing."""

    def __init__(
        self,
        message: str = "Failed to parse or retrieve database metadata.",
        **kwargs: Any,
    ) -> None:
        super().__init__(
            message=message,
            error_code=ConnectorErrorCode.CONNECTOR_METADATA_ERROR,
            **kwargs,
        )


class ConnectorCancelledError(ConnectorError):
    """Raised when an ongoing connector operation is cancelled cooperatively."""

    def __init__(
        self,
        message: str = "Connector operation cancelled by caller.",
        **kwargs: Any,
    ) -> None:
        super().__init__(
            message=message,
            error_code=ConnectorErrorCode.CONNECTOR_CANCELLED,
            **kwargs,
        )


class ConnectorSecurityViolationError(ConnectorError):
    """Raised when an operation violates read-only or SSRF boundaries."""

    def __init__(
        self,
        message: str = "Connector operation rejected by security policy.",
        **kwargs: Any,
    ) -> None:
        super().__init__(
            message=message,
            error_code=ConnectorErrorCode.CONNECTOR_SECURITY_VIOLATION,
            **kwargs,
        )
