"""DERA Canonical Metadata Adapters Package.

Exports engine-specific metadata adapters for PostgreSQL, SQLite, MySQL, and MariaDB.
"""

from dera.metadata.adapters.mariadb import MariaDbMetadataAdapter
from dera.metadata.adapters.mysql import MySqlMetadataAdapter
from dera.metadata.adapters.postgresql import PostgresqlMetadataAdapter
from dera.metadata.adapters.sqlite import SqliteMetadataAdapter

__all__ = [
    "MariaDbMetadataAdapter",
    "MySqlMetadataAdapter",
    "PostgresqlMetadataAdapter",
    "SqliteMetadataAdapter",
]
