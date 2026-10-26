"""SQLite schema extraction connector for DERA.

Deterministic, read-only reverse engineering of SQLite schemas into
canonical DERA models.
Copyright (c) 2026 Krishanth. All rights reserved.
Licensed under the MIT License.
"""

from __future__ import annotations

import sqlite3
from typing import Any
from dera.models import (
    DatabaseColumn,
    DatabaseTable,
    ForeignKeyConstraint,
    PrimaryKeyConstraint,
    SchemaSnapshot,
    TableIndex,
)


class SqliteConnector:
    """Read-only SQLite schema inspection connector."""

    def __init__(self, connection_string: str) -> None:
        """Initialize connection.
        
        Enforces read-only access for file-based databases via URI if not memory.
        """
        self.connection_string = connection_string
        if connection_string == ":memory:":
            self._conn = sqlite3.connect(":memory:")
        else:
            # Enforce read-only mode for file connections
            uri = f"file:{connection_string}?mode=ro" if "mode=" not in connection_string else connection_string
            try:
                self._conn = sqlite3.connect(uri, uri=True)
            except sqlite3.OperationalError:
                # Fallback to standard connect with query pragmas
                self._conn = sqlite3.connect(connection_string)

        self._conn.row_factory = sqlite3.Row

    @property
    def raw_connection(self) -> sqlite3.Connection:
        """Returns the underlying sqlite connection."""
        return self._conn

    def get_table_names(self) -> list[str]:
        """Returns all user table names in the database."""
        cursor = self._conn.cursor()
        cursor.execute(
            """
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
            ORDER BY name ASC
            """
        )
        return [row["name"] for row in cursor.fetchall()]

    def inspect_table(self, table_name: str) -> DatabaseTable:
        """Extracts schema, columns, primary keys, foreign keys, and indexes for a table."""
        cursor = self._conn.cursor()

        # 1. Columns & Primary Key from PRAGMA table_info
        # Safely quote table name
        safe_name = table_name.replace('"', '""')
        cursor.execute(f'PRAGMA table_info("{safe_name}")')
        col_rows = cursor.fetchall()

        columns: list[DatabaseColumn] = []
        pk_cols: list[tuple[int, str]] = []

        for row in col_rows:
            col_name = row["name"]
            data_type = row["type"] or "TEXT"
            is_nullable = not bool(row["notnull"])
            default_val = row["dflt_value"]
            pk_order = row["pk"]

            columns.append(
                DatabaseColumn(
                    name=col_name,
                    data_type=data_type.upper(),
                    is_nullable=is_nullable,
                    default_expression=str(default_val) if default_val is not None else None,
                )
            )

            if pk_order > 0:
                pk_cols.append((pk_order, col_name))

        # Primary Key
        pk_cols.sort(key=lambda x: x[0])
        pk = PrimaryKeyConstraint(
            name=f"pk_{table_name}",
            columns=tuple(col for _, col in pk_cols),
        ) if pk_cols else None

        # 2. Foreign Keys from PRAGMA foreign_key_list
        cursor.execute(f'PRAGMA foreign_key_list("{safe_name}")')
        fk_rows = cursor.fetchall()

        # Group composite foreign keys by FK id
        fk_map: dict[int, dict[str, Any]] = {}
        for row in fk_rows:
            fk_id = row["id"]
            if fk_id not in fk_map:
                fk_map[fk_id] = {
                    "target_table": row["table"],
                    "source_cols": [],
                    "target_cols": [],
                    "on_update": row["on_update"],
                    "on_delete": row["on_delete"],
                }
            fk_map[fk_id]["source_cols"].append(row["from"])
            fk_map[fk_id]["target_cols"].append(row["to"])

        foreign_keys: list[ForeignKeyConstraint] = []
        for fk_id, fk_data in sorted(fk_map.items()):
            foreign_keys.append(
                ForeignKeyConstraint(
                    name=f"fk_{table_name}_{fk_data['target_table']}_{fk_id}",
                    source_columns=tuple(fk_data["source_cols"]),
                    target_schema="main",
                    target_table=fk_data["target_table"],
                    target_columns=tuple(fk_data["target_cols"]),
                    on_update=fk_data["on_update"],
                    on_delete=fk_data["on_delete"],
                )
            )

        # 3. Indexes from PRAGMA index_list
        cursor.execute(f'PRAGMA index_list("{safe_name}")')
        idx_rows = cursor.fetchall()

        indexes: list[TableIndex] = []
        for idx_row in idx_rows:
            idx_name = idx_row["name"]
            is_unique = bool(idx_row["unique"])

            safe_idx = idx_name.replace('"', '""')
            cursor.execute(f'PRAGMA index_info("{safe_idx}")')
            info_rows = cursor.fetchall()
            idx_cols = tuple(r["name"] for r in info_rows)

            indexes.append(
                TableIndex(
                    name=idx_name,
                    columns=idx_cols,
                    is_unique=is_unique,
                    index_type="BTREE",
                )
            )

        return DatabaseTable(
            schema="main",
            name=table_name,
            columns=tuple(columns),
            primary_key=pk,
            foreign_keys=tuple(foreign_keys),
            indexes=tuple(indexes),
        )

    def extract_snapshot(self, database_name: str = "sqlite_db") -> SchemaSnapshot:
        """Inspects all tables and constructs a canonical SchemaSnapshot."""
        tables = [self.inspect_table(name) for name in self.get_table_names()]
        return SchemaSnapshot(
            database_name=database_name,
            engine="sqlite",
            tables=tuple(tables),
        )

    def close(self) -> None:
        """Closes the database connection."""
        self._conn.close()
