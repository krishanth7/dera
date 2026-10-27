"""DERA SQLite Connector — Type Affinity Classification Rules.

Implements the official SQLite 3 Type Affinity determination algorithm
(Rules 1-5 from SQLite specification Section 3.1) while preserving exact declared
data types and STRICT table type invariants.
"""

from __future__ import annotations

from enum import StrEnum


class SQLiteTypeAffinity(StrEnum):
    """Canonical SQLite 3 storage class type affinities."""

    INTEGER = "INTEGER"
    TEXT = "TEXT"
    BLOB = "BLOB"
    REAL = "REAL"
    NUMERIC = "NUMERIC"


# Official SQLite STRICT table allowed data types
STRICT_TABLE_VALID_TYPES = {
    "INT",
    "INTEGER",
    "REAL",
    "TEXT",
    "BLOB",
    "ANY",
}


def determine_sqlite_affinity(declared_type: str | None) -> SQLiteTypeAffinity:
    """Determine SQLite column type affinity according to official specification Section 3.1.

    Rules applied in priority order:
    1. If the declared type contains "INT", affinity is INTEGER.
    2. If the declared type contains "CHAR", "CLOB", or "TEXT", affinity is TEXT.
    3. If the declared type contains "BLOB" or if no type is specified, affinity is BLOB.
    4. If the declared type contains "REAL", "FLOA", or "DOUB", affinity is REAL.
    5. Otherwise, affinity is NUMERIC.

    Parameters
    ----------
    declared_type : str | None
        Declared column type string from table schema or PRAGMA table_xinfo.

    Returns
    -------
    SQLiteTypeAffinity
        The determined SQLite storage affinity.
    """
    if declared_type is None:
        return SQLiteTypeAffinity.BLOB

    upper_type = declared_type.strip().upper()
    if not upper_type:
        return SQLiteTypeAffinity.BLOB

    # Rule 1: Contains "INT" -> INTEGER
    if "INT" in upper_type:
        return SQLiteTypeAffinity.INTEGER

    # Rule 2: Contains "CHAR", "CLOB", or "TEXT" -> TEXT
    if "CHAR" in upper_type or "CLOB" in upper_type or "TEXT" in upper_type:
        return SQLiteTypeAffinity.TEXT

    # Rule 3: Contains "BLOB" -> BLOB
    if "BLOB" in upper_type:
        return SQLiteTypeAffinity.BLOB

    # Rule 4: Contains "REAL", "FLOA", or "DOUB" -> REAL
    if "REAL" in upper_type or "FLOA" in upper_type or "DOUB" in upper_type:
        return SQLiteTypeAffinity.REAL

    # Rule 5: Otherwise -> NUMERIC
    return SQLiteTypeAffinity.NUMERIC


def parse_sqlite_column_type(declared_type: str | None) -> tuple[str, SQLiteTypeAffinity]:
    """Parse declared type string and derive storage affinity.

    Parameters
    ----------
    declared_type : str | None
        Raw declared column type string from catalog.

    Returns
    -------
    tuple[str, SQLiteTypeAffinity]
        Tuple of (clean_declared_type, affinity).
    """
    clean_type = declared_type.strip() if declared_type else ""
    affinity = determine_sqlite_affinity(clean_type)
    return clean_type, affinity
