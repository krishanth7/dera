"""DERA MariaDB Connector — Typed Configuration & Boundaries.

Defines immutable, strongly-typed connection configuration for MariaDB database instances
with standard 3306 port default, character set bindings, and session bounds.
"""

from __future__ import annotations

from pydantic import ConfigDict, Field, model_validator

from dera_connectors.configuration import ConnectorConfig
from dera_connectors.engine import DatabaseEngine, DatabaseProvider


class MariaDbConnectorConfig(ConnectorConfig):
    """Typed connection configuration for MariaDB 10.11+ and 11.4 LTS database instances."""

    model_config = ConfigDict(frozen=True)

    engine: DatabaseEngine = Field(
        default=DatabaseEngine.MARIADB,
        description="Database engine type (must be DatabaseEngine.MARIADB).",
    )
    provider: DatabaseProvider = Field(
        default=DatabaseProvider.GENERIC,
        description="Deployment provider (GENERIC, AWS_RDS, etc.).",
    )
    port: int | None = Field(
        default=3306,
        ge=1,
        le=65535,
        description="Network port for MariaDB listener (defaults to 3306).",
    )
    charset: str = Field(
        default="utf8mb4",
        description="Connection character set encoding (defaults to utf8mb4).",
    )

    @model_validator(mode="after")
    def _validate_mariadb(self) -> MariaDbConnectorConfig:
        """Enforce MariaDB engine family and default port 3306."""
        if self.engine != DatabaseEngine.MARIADB:
            object.__setattr__(self, "engine", DatabaseEngine.MARIADB)
        if self.port is None:
            object.__setattr__(self, "port", 3306)
        return self
