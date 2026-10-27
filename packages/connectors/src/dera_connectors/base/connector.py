"""DERA Connectors — Base Database Connector Interface.

All DERA database connectors inherit from BaseConnector.
Enforces strict read-only introspection boundaries, preventing any mutation
of customer databases during metadata reverse engineering.
"""

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from dera.models import DatabaseTable, SchemaSnapshot
from dera_core.exceptions import ReadOnlyViolationError

# Forbidden SQL tokens that violate read-only metadata introspection
_MUTATION_KEYWORDS = re.compile(
    r"\b(DROP|TRUNCATE|ALTER|CREATE|INSERT|UPDATE|DELETE|GRANT|REVOKE)\b",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class ConnectionConfig:
    """Immutable configuration for database connector connections."""

    dialect: str
    database: str
    host: str | None = None
    port: int | None = None
    username: str | None = None
    # Password should never be logged or exposed in representation
    ssl_mode: str = "prefer"
    read_only: bool = True
    timeout_seconds: int = 30
    extra_options: dict[str, Any] = field(default_factory=dict)

    def safe_dict(self) -> dict[str, Any]:
        """Return configuration dictionary with sanitized credentials."""
        return {
            "dialect": self.dialect,
            "database": self.database,
            "host": self.host,
            "port": self.port,
            "username": self.username,
            "ssl_mode": self.ssl_mode,
            "read_only": self.read_only,
            "timeout_seconds": self.timeout_seconds,
        }


class BaseConnector(ABC):
    """Abstract base class for all deterministic database introspection connectors."""

    def __init__(self, config: ConnectionConfig) -> None:
        self.config = config
        self._is_connected = False

    @property
    def is_connected(self) -> bool:
        """Return whether connector holds an active connection."""
        return self._is_connected

    @property
    def dialect(self) -> str:
        """Return canonical database dialect name."""
        return self.config.dialect

    def validate_query_read_only(self, sql: str) -> None:
        """Validate that an introspection query does not contain DDL or DML mutations."""
        if _MUTATION_KEYWORDS.search(sql):
            raise ReadOnlyViolationError(
                f"Query rejected by read-only connector boundary: {sql[:60]}..."
            )

    @abstractmethod
    def connect(self) -> None:
        """Establish connection to database with read-only transaction parameters."""
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """Close database connection and release resources."""
        pass

    @abstractmethod
    def test_connection(self) -> bool:
        """Verify database connectivity and read privileges."""
        pass

    @abstractmethod
    def inspect_tables(self) -> list[DatabaseTable]:
        """Introspect tables, columns, constraints, and keys from database metadata."""
        pass

    def inspect_schema(self, schema_name: str | None = None) -> SchemaSnapshot:
        """Inspect and return complete canonical SchemaSnapshot."""
        tables = self.inspect_tables()
        return SchemaSnapshot(
            database_name=self.config.database,
            schema_name=schema_name or "public",
            tables=tables,
        )

    def __enter__(self) -> "BaseConnector":
        self.connect()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.disconnect()
