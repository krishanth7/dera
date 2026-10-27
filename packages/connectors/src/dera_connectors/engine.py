"""DERA Connectors — Database Engine Identity & Fingerprint Models.

Defines strongly-typed database engine enumerations, cloud provider designations,
and sanitized server identity models for Phase 5.1.
"""

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class DatabaseEngine(StrEnum):
    """Supported database engine families across DERA connector adapters."""

    POSTGRESQL = "postgresql"
    SQLITE = "sqlite"
    MYSQL = "mysql"
    MARIADB = "mariadb"


class DatabaseProvider(StrEnum):
    """Cloud provider or platform distribution designation for database engines."""

    GENERIC = "generic"
    SUPABASE = "supabase"
    AWS_RDS = "aws_rds"
    AWS_AURORA = "aws_aurora"
    GCP_CLOUDSQL = "gcp_cloudsql"
    AZURE_DATABASE = "azure_database"
    NEON = "neon"


class DatabaseIdentity(BaseModel):
    """Sanitized database server identity and fingerprint.

    Contains engine details, driver version, server version string, and capability
    hints without exposing sensitive hostnames or internal IP addresses.
    """

    model_config = ConfigDict(frozen=True)

    engine: DatabaseEngine = Field(
        ...,
        description="Canonical database engine family.",
    )
    server_version: str | None = Field(
        default=None,
        description="Reported database engine server version string.",
    )
    driver_version: str | None = Field(
        default=None,
        description="Introspection client driver and adapter version.",
    )
    provider: DatabaseProvider = Field(
        default=DatabaseProvider.GENERIC,
        description="Hosting provider or dialect distribution designation.",
    )
    database_name: str | None = Field(
        default=None,
        description="Active database or catalog identifier if safely available.",
    )
    connector_version: str = Field(
        default="0.1.0-dev",
        description="DERA connector adapter implementation version.",
    )
    server_capability_hints: dict[str, Any] = Field(
        default_factory=dict,
        description="Engine-specific non-sensitive server feature hints.",
    )
