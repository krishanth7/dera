"""DERA Connectors — Deterministic Database Metadata Connectors.

Provides read-only database introspection adapters for PostgreSQL, SQLite,
MySQL, and cloud data platforms.
"""

from dera_connectors.base.connector import (
    BaseConnector,
    ConnectionConfig,
)
from dera_connectors.sqlite.connector import SqliteConnector

__version__ = "0.1.0-dev"

__all__ = [
    "BaseConnector",
    "ConnectionConfig",
    "SqliteConnector",
    "__version__",
]
