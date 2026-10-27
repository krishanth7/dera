"""DERA Connectors — Resource Bounds & Denial-of-Service Defense.

Enforces deterministic caps on result row counts, identifier lengths, SQL definitions,
total metadata objects, concurrency per workspace, and retry eligibility.
"""

from __future__ import annotations

from dataclasses import dataclass

from dera_connectors.security.errors import (
    ConnectorSecurityError,
    ReadOnlySecurityViolationError,
    ResourceLimitExceededViolationError,
    SSRFSecurityViolationError,
    TenantIsolationViolationError,
)


@dataclass(frozen=True)
class ConnectorResourceLimits:
    """Configurable resource safety thresholds for database connector operations."""

    max_result_rows: int = 50_000
    max_identifier_length: int = 1_024
    max_definition_size_bytes: int = 1_048_576  # 1 MB
    max_metadata_objects: int = 100_000
    max_concurrent_operations_per_workspace: int = 10
    max_pool_size: int = 10
    max_retry_attempts: int = 3

    def check_result_rows(self, count: int) -> None:
        """Validate query result row count against safety limits.

        Raises
        ------
        ResourceLimitExceededViolationError
            If count exceeds max_result_rows.
        """
        if count > self.max_result_rows:
            raise ResourceLimitExceededViolationError(
                metric="result_rows",
                current_value=count,
                max_limit=self.max_result_rows,
            )

    def check_identifier_length(self, name: str) -> None:
        """Validate identifier character length.

        Raises
        ------
        ResourceLimitExceededViolationError
            If length exceeds max_identifier_length.
        """
        length = len(name)
        if length > self.max_identifier_length:
            raise ResourceLimitExceededViolationError(
                metric="identifier_length",
                current_value=length,
                max_limit=self.max_identifier_length,
            )

    def check_definition_size(self, sql_definition: str | bytes) -> None:
        """Validate SQL definition size in bytes.

        Raises
        ------
        ResourceLimitExceededViolationError
            If byte size exceeds max_definition_size_bytes.
        """
        size = len(
            sql_definition.encode("utf-8") if isinstance(sql_definition, str) else sql_definition
        )
        if size > self.max_definition_size_bytes:
            raise ResourceLimitExceededViolationError(
                metric="definition_size_bytes",
                current_value=size,
                max_limit=self.max_definition_size_bytes,
            )

    def check_metadata_object_count(self, count: int) -> None:
        """Validate total schema metadata entities.

        Raises
        ------
        ResourceLimitExceededViolationError
            If count exceeds max_metadata_objects.
        """
        if count > self.max_metadata_objects:
            raise ResourceLimitExceededViolationError(
                metric="metadata_objects",
                current_value=count,
                max_limit=self.max_metadata_objects,
            )

    @staticmethod
    def is_error_retryable(exc: Exception) -> bool:
        """Determine if an exception is eligible for retry.

        Security violations, read-only violations, SSRF, authentication, and tenant
        isolation errors must NEVER be retried.
        """
        # Strictly non-retryable security errors
        if isinstance(
            exc,
            (
                ConnectorSecurityError,
                ReadOnlySecurityViolationError,
                SSRFSecurityViolationError,
                TenantIsolationViolationError,
                PermissionError,
            ),
        ):
            return False

        exc_name = exc.__class__.__name__.lower()
        if any(
            term in exc_name
            for term in ("auth", "permission", "security", "denied", "syntax", "readonly")
        ):
            return False

        # Transient network or timeout errors may be retried if under limit
        return True
