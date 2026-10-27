"""DERA SQLite Connector — Pre-Reviewed Catalog & PRAGMA Introspection Queries.

Provides parameterized and safely quoted SQL statements and PRAGMA queries targeting
sqlite_schema and SQLite 3 metadata facilities.
"""

from __future__ import annotations


def quote_sqlite_identifier(identifier: str) -> str:
    """Safely quote a SQLite identifier (table, column, schema name) using standard double quotes.

    Parameters
    ----------
    identifier : str
        Raw identifier string.

    Returns
    -------
    str
        Properly double-quoted and escaped SQLite identifier.
    """
    escaped = identifier.replace('"', '""')
    return f'"{escaped}"'


# Runtime version and database namespace queries
QUERY_SQLITE_VERSION = "SELECT sqlite_version();"
QUERY_DATABASE_LIST = "PRAGMA database_list;"

# Schema object enumeration from sqlite_schema (excluding internal system objects by default)
QUERY_ALL_TABLES = """
SELECT
    name AS table_name,
    type AS object_type,
    sql AS table_sql
FROM sqlite_schema
WHERE type = 'table'
  AND name NOT LIKE 'sqlite_%'
ORDER BY name ASC;
"""

QUERY_TABLE_BY_NAME = """
SELECT
    name AS table_name,
    type AS object_type,
    sql AS table_sql
FROM sqlite_schema
WHERE type = 'table'
  AND name = ?;
"""

QUERY_ALL_VIEWS = """
SELECT
    name AS view_name,
    sql AS view_sql
FROM sqlite_schema
WHERE type = 'view'
  AND name NOT LIKE 'sqlite_%'
ORDER BY name ASC;
"""

QUERY_VIEW_BY_NAME = """
SELECT
    name AS view_name,
    sql AS view_sql
FROM sqlite_schema
WHERE type = 'view'
  AND name = ?;
"""

QUERY_ALL_TRIGGERS = """
SELECT
    name AS trigger_name,
    tbl_name AS table_name,
    sql AS trigger_sql
FROM sqlite_schema
WHERE type = 'trigger'
  AND name NOT LIKE 'sqlite_%'
ORDER BY name ASC;
"""

QUERY_TRIGGERS_BY_TABLE = """
SELECT
    name AS trigger_name,
    tbl_name AS table_name,
    sql AS trigger_sql
FROM sqlite_schema
WHERE type = 'trigger'
  AND tbl_name = ?
ORDER BY name ASC;
"""

QUERY_EXPLICIT_INDEXES = """
SELECT
    name AS index_name,
    tbl_name AS table_name,
    sql AS index_sql
FROM sqlite_schema
WHERE type = 'index'
  AND name NOT LIKE 'sqlite_%'
ORDER BY name ASC;
"""


def build_pragma_table_xinfo(table_name: str) -> str:
    """Construct safe PRAGMA table_xinfo statement with quoted identifier."""
    return f"PRAGMA table_xinfo({quote_sqlite_identifier(table_name)});"


def build_pragma_table_info(table_name: str) -> str:
    """Construct safe PRAGMA table_info fallback statement with quoted identifier."""
    return f"PRAGMA table_info({quote_sqlite_identifier(table_name)});"


def build_pragma_foreign_key_list(table_name: str) -> str:
    """Construct safe PRAGMA foreign_key_list statement with quoted identifier."""
    return f"PRAGMA foreign_key_list({quote_sqlite_identifier(table_name)});"


def build_pragma_index_list(table_name: str) -> str:
    """Construct safe PRAGMA index_list statement with quoted identifier."""
    return f"PRAGMA index_list({quote_sqlite_identifier(table_name)});"


def build_pragma_index_xinfo(index_name: str) -> str:
    """Construct safe PRAGMA index_xinfo statement with quoted identifier."""
    return f"PRAGMA index_xinfo({quote_sqlite_identifier(index_name)});"


def build_pragma_index_info(index_name: str) -> str:
    """Construct safe PRAGMA index_info fallback statement with quoted identifier."""
    return f"PRAGMA index_info({quote_sqlite_identifier(index_name)});"
