"""DERA Connectors — Security & Safety Error Taxonomy.

Defines strongly typed, categorized exceptions for read-only violations, SSRF attempts,
DNS rebinding, filesystem boundary escapes, tenant cross-access, and resource limit overflows.
"""

from __future__ import annotations

from typing import Any


class ConnectorSecurityError(Exception):
    """Base exception for all security violations within the connector subsystem."""

    def __init__(
        self,
        message: str,
        code: str = "SECURITY_VIOLATION",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details or {}

    def to_dict(self) -> dict[str, Any]:
        """Convert security exception into a sanitized dictionary."""
        return {
            "error_code": self.code,
            "message": self.message,
            "details": self.details,
        }


class ReadOnlySecurityViolationError(ConnectorSecurityError):
    """Raised when an SQL query attempts data or schema modification."""

    def __init__(self, query_snippet: str, detected_token: str | None = None) -> None:
        details = {"token": detected_token} if detected_token else {}
        super().__init__(
            f"Query violates read-only connector policy: {query_snippet}",
            code="READ_ONLY_VIOLATION",
            details=details,
        )


class SSRFSecurityViolationError(ConnectorSecurityError):
    """Raised when a connection target attempts to access prohibited internal or cloud metadata networks."""

    def __init__(self, host: str, reason: str) -> None:
        super().__init__(
            f"Connection target '{host}' rejected by SSRF egress policy: {reason}",
            code="SSRF_VIOLATION",
            details={"host": host, "reason": reason},
        )


class DNSRebindingViolationError(ConnectorSecurityError):
    """Raised when destination IP shifts unexpectedly between pre-flight validation and connection."""

    def __init__(self, host: str, original_ip: str, rebind_ip: str) -> None:
        super().__init__(
            f"DNS rebinding detected for host '{host}': original IP '{original_ip}' changed to '{rebind_ip}'.",
            code="DNS_REBINDING_VIOLATION",
            details={"host": host, "original_ip": original_ip, "rebind_ip": rebind_ip},
        )


class FilesystemIsolationViolationError(ConnectorSecurityError):
    """Raised when a local file reference traverses outside approved workspace storage roots or uses an unsafe symlink."""

    def __init__(self, target_path: str, reason: str) -> None:
        super().__init__(
            f"Filesystem access to '{target_path}' denied: {reason}",
            code="FILESYSTEM_ISOLATION_VIOLATION",
            details={"target_path": target_path, "reason": reason},
        )


class TenantIsolationViolationError(ConnectorSecurityError):
    """Raised when a connector operation attempts cross-workspace resource access."""

    def __init__(self, caller_workspace_id: str, target_workspace_id: str) -> None:
        super().__init__(
            f"Cross-workspace connector access denied: caller '{caller_workspace_id}' cannot access target '{target_workspace_id}'.",
            code="TENANT_ISOLATION_VIOLATION",
            details={
                "caller_workspace_id": caller_workspace_id,
                "target_workspace_id": target_workspace_id,
            },
        )


class TimeoutExceededViolationError(ConnectorSecurityError):
    """Raised when a connector operation exceeds its allocated deadline budget."""

    def __init__(self, operation: str, deadline_seconds: float, elapsed_seconds: float) -> None:
        super().__init__(
            f"Operation '{operation}' exceeded deadline budget of {deadline_seconds:.1f}s (elapsed: {elapsed_seconds:.1f}s).",
            code="TIMEOUT_EXCEEDED",
            details={
                "operation": operation,
                "deadline_seconds": deadline_seconds,
                "elapsed_seconds": elapsed_seconds,
            },
        )


class CancellationRequestedViolationError(ConnectorSecurityError):
    """Raised when an operation is cooperatively aborted by caller cancellation."""

    def __init__(self, reason: str = "Operation cancelled by caller.") -> None:
        super().__init__(
            f"Connector operation cancelled: {reason}",
            code="OPERATION_CANCELLED",
            details={"reason": reason},
        )


class ResourceLimitExceededViolationError(ConnectorSecurityError):
    """Raised when a metadata inspection exceeds configured safety thresholds."""

    def __init__(self, metric: str, current_value: int, max_limit: int) -> None:
        super().__init__(
            f"Resource safety limit exceeded for '{metric}': {current_value} exceeds maximum allowed {max_limit}.",
            code="RESOURCE_LIMIT_EXCEEDED",
            details={
                "metric": metric,
                "current_value": current_value,
                "max_limit": max_limit,
            },
        )


class UnauthorizedQueryError(ConnectorSecurityError):
    """Raised when an SQL query is not recognized or permitted by the query allowlist registry."""

    def __init__(self, operation_id: str, reason: str) -> None:
        super().__init__(
            f"Query operation '{operation_id}' rejected by query policy: {reason}",
            code="UNAUTHORIZED_QUERY",
            details={"operation_id": operation_id, "reason": reason},
        )


class CredentialExposureError(ConnectorSecurityError):
    """Raised when unmasked credentials or secrets are detected in public logs or error messages."""

    def __init__(self, field_name: str) -> None:
        super().__init__(
            f"Potential credential exposure detected in field '{field_name}'.",
            code="CREDENTIAL_EXPOSURE",
            details={"field_name": field_name},
        )
