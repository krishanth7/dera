"""DERA Connectors — SQLite 3.x Asynchronous Read-Only Connector.

Provides deterministic metadata introspection, filesystem boundary isolation,
and read-only connection lifecycles for SQLite 3.x embedded databases.
"""

from dera_connectors.sqlite.adapter import SqliteConnector
from dera_connectors.sqlite.capabilities import get_sqlite_capabilities
from dera_connectors.sqlite.configuration import SqliteConnectorConfig
from dera_connectors.sqlite.errors import map_sqlite_error, sanitize_sqlite_error_message
from dera_connectors.sqlite.filesystem import build_sqlite_readonly_uri, validate_sqlite_path
from dera_connectors.sqlite.types import SQLiteTypeAffinity, determine_sqlite_affinity

__all__ = [
    "SqliteConnector",
    "SqliteConnectorConfig",
    "get_sqlite_capabilities",
    "validate_sqlite_path",
    "build_sqlite_readonly_uri",
    "map_sqlite_error",
    "sanitize_sqlite_error_message",
    "SQLiteTypeAffinity",
    "determine_sqlite_affinity",
]
