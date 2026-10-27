"""DERA SQLite Connector — Typed Configuration & Filesystem Isolation Bounds.

Defines immutable, strongly-typed connection configuration for SQLite 3.x embedded
databases with strict filesystem boundary validation, read-only parameters, and
timeout configurations.
"""

import os

from pydantic import ConfigDict, Field, model_validator

from dera_connectors.configuration import ConnectorConfig
from dera_connectors.engine import DatabaseEngine, DatabaseProvider


class SqliteConnectorConfig(ConnectorConfig):
    """Typed connection configuration for local SQLite 3 database instances."""

    model_config = ConfigDict(frozen=True)

    engine: DatabaseEngine = Field(
        default=DatabaseEngine.SQLITE,
        description="Database engine family (must be DatabaseEngine.SQLITE).",
    )
    provider: DatabaseProvider = Field(
        default=DatabaseProvider.GENERIC,
        description="Deployment provider designation.",
    )
    approved_storage_roots: list[str] = Field(
        default_factory=list,
        description="Approved filesystem directory roots within which SQLite files must reside.",
    )
    allow_memory_databases: bool = Field(
        default=False,
        description="Permit in-memory (:memory:) databases for ephemeral test isolation only.",
    )
    busy_timeout_ms: int = Field(
        default=5000,
        ge=100,
        le=60000,
        description="SQLite PRAGMA busy_timeout in milliseconds.",
    )
    immutable_snapshot: bool = Field(
        default=False,
        description="If True, opens database in immutable mode (immutable=1) for verified static snapshots.",
    )
    max_objects_limit: int = Field(
        default=50000,
        ge=100,
        le=500000,
        description="Maximum metadata objects returned per introspection query.",
    )

    @model_validator(mode="after")
    def _validate_sqlite_configuration(self) -> "SqliteConnectorConfig":
        """Enforce SQLite engine constraints and strip network parameters."""
        if self.engine != DatabaseEngine.SQLITE:
            object.__setattr__(self, "engine", DatabaseEngine.SQLITE)

        # Invariant: SQLite is an embedded file engine, not network-attached
        if self.host is not None:
            raise ValueError("SQLite connectors do not support network 'host' configuration.")
        if self.port is not None:
            raise ValueError("SQLite connectors do not support network 'port' configuration.")

        # In-memory database validation
        db = self.database.strip()
        if db in (":memory:", "file::memory:") and not self.allow_memory_databases:
            raise ValueError(
                "In-memory SQLite databases (:memory:) are disabled by default. "
                "Set allow_memory_databases=True to enable for testing."
            )

        # Normalize approved storage roots if provided
        if self.approved_storage_roots:
            normalized_roots = [
                os.path.realpath(os.path.abspath(r)) for r in self.approved_storage_roots if r
            ]
            object.__setattr__(self, "approved_storage_roots", normalized_roots)

        return self
