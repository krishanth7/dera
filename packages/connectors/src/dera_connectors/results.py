"""DERA Connectors — Connection Test & Inspection Results.

Defines standardized result models for database connectivity tests and metadata scans.
"""

from pydantic import BaseModel, ConfigDict, Field

from dera_connectors.engine import DatabaseIdentity


class ConnectionTestResult(BaseModel):
    """Result of a diagnostic connectivity verification probe."""

    model_config = ConfigDict(frozen=True)

    success: bool = Field(
        ...,
        description="True if connection and basic catalog read succeeded.",
    )
    latency_ms: float = Field(
        ...,
        ge=0.0,
        description="Round-trip latency in milliseconds for connection test.",
    )
    identity: DatabaseIdentity | None = Field(
        default=None,
        description="Identified database server fingerprint if test succeeded.",
    )
    capabilities_summary: list[str] = Field(
        default_factory=list,
        description="Summary list of key capabilities verified during test.",
    )
    error_code: str | None = Field(
        default=None,
        description="Standardized error code if connection test failed.",
    )
    error_message: str | None = Field(
        default=None,
        description="Sanitized diagnostic error message if test failed.",
    )
