"""DERA Connectors — SQLite Deterministic Introspection Connector.

Implements read-only SQLite metadata introspection adhering to BaseConnector.
"""

from __future__ import annotations

import sqlite3

from dera.models import DatabaseTable
from dera_core.exceptions import ConnectionAuthenticationError

from dera_connectors.base.connector import BaseConnector, ConnectionConfig


class SqliteConnector(BaseConnector):
    """Deterministic read-only SQLite database schema introspection connector."""

    def __init__(self, config: ConnectionConfig) -> None:
        super().__init__(config)
        self._conn: sqlite3.Connection | None = None

    def connect(self) -> None:
        """Connect to SQLite database with read-only pragma enforcement."""
        if self._conn is not None:
            return

        db_path = self.config.database
        try:
            if db_path == ":memory:":
                self._conn = sqlite3.connect(":memory:")
            else:
                uri = f"file:{db_path}?mode=ro" if "mode=" not in db_path else db_path
                try:
                    self._conn = sqlite3.connect(uri, uri=True)
                except sqlite3.OperationalError:
                    self._conn = sqlite3.connect(db_path)

            self._conn.row_factory = sqlite3.Row
            # Enforce read-only query pragma
            self._conn.execute("PRAGMA query_only = ON;")
            self._is_connected = True
        except Exception as e:
            raise ConnectionAuthenticationError(f"Failed to connect to SQLite: {e}") from e

    def disconnect(self) -> None:
        """Close SQLite database connection."""
        if self._conn:
            self._conn.close()
            self._conn = None
            self._is_connected = False

    def test_connection(self) -> bool:
        """Test read accessibility of SQLite database."""
        if not self._is_connected:
            self.connect()
        try:
            assert self._conn is not None
            cursor = self._conn.cursor()
            cursor.execute("SELECT 1;")
            row = cursor.fetchone()
            return row is not None and row[0] == 1
        except Exception:
            return False

    def get_table_names(self) -> list[str]:
        """Retrieve user table names sorted deterministically."""
        if not self._is_connected:
            self.connect()
        assert self._conn is not None

        cursor = self._conn.cursor()
        cursor.execute(
            """
            SELECT name FROM sqlite_master
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
            ORDER BY name ASC
            """
        )
        return [row["name"] for row in cursor.fetchall()]

    def inspect_tables(self) -> list[DatabaseTable]:
        """Introspect all tables into canonical DatabaseTable models."""
        if not self._is_connected:
            self.connect()
        assert self._conn is not None

        tables: list[DatabaseTable] = []
        table_names = self.get_table_names()

        for table_name in table_names:
            cursor = self._conn.cursor()
            safe_name = table_name.replace('"', '""')
            cursor.execute(f'PRAGMA table_info("{safe_name}")')
            _ = cursor.fetchall()

            # Using dera.connectors.sqlite structure to ensure compatibility
            from dera.connectors.sqlite import SqliteConnector as LegacySqlite

            legacy = LegacySqlite(self.config.database)
            try:
                tables.append(legacy.inspect_table(table_name))
            finally:
                legacy.close()

        return tables
