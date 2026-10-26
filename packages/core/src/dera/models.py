"""Canonical schema representation models for DERA.

Engine-agnostic data structures representing tables, columns, constraints,
indexes, and immutable schema snapshots.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import hashlib
import json
from typing import Any


@dataclass(frozen=True)
class DatabaseColumn:
    """Represents a column in a database table."""

    name: str
    data_type: str
    is_nullable: bool = True
    default_expression: str | None = None
    ordinal_position: int = 1
    character_maximum_length: int | None = None
    numeric_precision: int | None = None
    numeric_scale: int | None = None
    description: str | None = None


@dataclass(frozen=True)
class PrimaryKeyConstraint:
    """Represents an explicit primary key constraint."""

    name: str
    columns: tuple[str, ...]


@dataclass(frozen=True)
class ForeignKeyConstraint:
    """Represents a referential integrity foreign key constraint."""

    name: str
    source_columns: tuple[str, ...]
    target_schema: str
    target_table: str
    target_columns: tuple[str, ...]
    on_update: str = "NO ACTION"
    on_delete: str = "NO ACTION"


@dataclass(frozen=True)
class TableIndex:
    """Represents an index defined on a database table."""

    name: str
    columns: tuple[str, ...]
    is_unique: bool = False
    index_type: str = "BTREE"
    predicate: str | None = None


@dataclass(frozen=True)
class DatabaseTable:
    """Represents a database table and its associated constraints and indexes."""

    schema: str
    name: str
    columns: tuple[DatabaseColumn, ...] = field(default_factory=tuple)
    primary_key: PrimaryKeyConstraint | None = None
    foreign_keys: tuple[ForeignKeyConstraint, ...] = field(default_factory=tuple)
    indexes: tuple[TableIndex, ...] = field(default_factory=tuple)
    description: str | None = None

    @property
    def fully_qualified_name(self) -> str:
        """Returns schema.table identifier."""
        return f"{self.schema}.{self.name}"

    @property
    def column_names(self) -> tuple[str, ...]:
        """Returns tuple of all column names."""
        return tuple(col.name for col in self.columns)


@dataclass(frozen=True)
class SchemaSnapshot:
    """Immutable, versioned snapshot of an inspected database schema."""

    database_name: str
    engine: str
    tables: tuple[DatabaseTable, ...]
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    snapshot_id: str = field(default="")

    def compute_hash(self) -> str:
        """Generates a deterministic SHA-256 fingerprint of the schema structure."""
        canonical_dict: dict[str, Any] = {
            "database": self.database_name,
            "engine": self.engine,
            "tables": [
                {
                    "fqn": t.fully_qualified_name,
                    "columns": [
                        {"name": c.name, "type": c.data_type, "nullable": c.is_nullable}
                        for c in t.columns
                    ],
                    "pk": t.primary_key.columns if t.primary_key else None,
                    "fks": [
                        {
                            "name": fk.name,
                            "src": fk.source_columns,
                            "tgt_table": f"{fk.target_schema}.{fk.target_table}",
                            "tgt_cols": fk.target_columns,
                        }
                        for fk in t.foreign_keys
                    ],
                    "indexes": [
                        {"name": idx.name, "cols": idx.columns, "unique": idx.is_unique}
                        for idx in t.indexes
                    ],
                }
                for t in sorted(self.tables, key=lambda x: x.fully_qualified_name)
            ],
        }
        serialized = json.dumps(canonical_dict, sort_keys=True)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


# Ergonomic canonical aliases
Column = DatabaseColumn
Table = DatabaseTable
ForeignKey = ForeignKeyConstraint
Index = TableIndex

