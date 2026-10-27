"""DERA Canonical Metadata Normalization & Identity — SQLite Adapter.

Normalizes SQLite catalog types, type affinities, STRICT table declarations,
and partial index/check constraint metadata.
"""

from __future__ import annotations

from dera.metadata.enums import CanonicalTypeCategory, GenerationMode, IndexType


class SqliteMetadataAdapter:
    """Specialized metadata adapter for SQLite PRAGMA and sqlite_master output."""

    @staticmethod
    def categorize_type(data_type: str) -> CanonicalTypeCategory:
        """Categorize SQLite declared type using standard SQLite type affinity rules.

        Rules from SQLite documentation:
        1. If declared type contains 'INT', it has INTEGER affinity.
        2. If declared type contains 'CHAR', 'CLOB', or 'TEXT', it has TEXT affinity.
        3. If declared type contains 'BLOB' or no type is specified, it has BLOB/BINARY affinity.
        4. If declared type contains 'REAL', 'FLOA', or 'DOUB', it has REAL/FLOAT affinity.
        5. Otherwise, it has NUMERIC affinity (DECIMAL/NUMERIC).
        """
        dt = data_type.strip().upper()
        if not dt:
            return CanonicalTypeCategory.UNKNOWN

        # Explicit JSON or Boolean keywords
        if "BOOLEAN" in dt or "BOOL" in dt:
            return CanonicalTypeCategory.BOOLEAN
        if "JSON" in dt:
            return CanonicalTypeCategory.JSON
        if "UUID" in dt:
            return CanonicalTypeCategory.UUID
        if "DATE" in dt or "TIME" in dt:
            return (
                CanonicalTypeCategory.TIMESTAMP
                if ("TIMESTAMP" in dt or ("DATE" in dt and "TIME" in dt))
                else (CanonicalTypeCategory.DATE if "DATE" in dt else CanonicalTypeCategory.TIME)
            )

        # 1. Rule 1: INT
        if "INT" in dt:
            return CanonicalTypeCategory.INTEGER

        # 2. Rule 2: CHAR, CLOB, TEXT
        if any(token in dt for token in ("CHAR", "CLOB", "TEXT")):
            return CanonicalTypeCategory.TEXT

        # 3. Rule 3: BLOB
        if "BLOB" in dt:
            return CanonicalTypeCategory.BINARY

        # 4. Rule 4: REAL, FLOA, DOUB
        if any(token in dt for token in ("REAL", "FLOA", "DOUB")):
            return CanonicalTypeCategory.FLOAT

        # 5. Rule 5: Numeric / Decimal fallback
        if any(token in dt for token in ("NUMERIC", "DECIMAL")):
            return CanonicalTypeCategory.DECIMAL

        return CanonicalTypeCategory.OTHER

    @staticmethod
    def parse_generation_mode(hidden_val: int | None) -> GenerationMode:
        """Parse SQLite table_xinfo hidden flag: 2=VIRTUAL, 3=STORED."""
        if hidden_val == 2:
            return GenerationMode.VIRTUAL
        if hidden_val == 3:
            return GenerationMode.STORED
        return GenerationMode.NONE

    @staticmethod
    def parse_index_type(origin: str | None) -> IndexType:
        """SQLite primarily implements B-tree indexes."""
        return IndexType.BTREE
