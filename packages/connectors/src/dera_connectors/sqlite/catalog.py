"""DERA SQLite Connector — Catalog Introspection & Metadata Models.

Implements deterministic metadata extraction for SQLite 3.x embedded databases,
including identity discovery, schema discovery, table enumeration with STRICT and
WITHOUT ROWID recognition, column declarations, constraints, indexes, views, and triggers.
"""

from __future__ import annotations

import re
import sqlite3
from typing import Any

from dera_connectors.engine import DatabaseEngine, DatabaseIdentity, DatabaseProvider
from dera_connectors.metadata import (
    SchemaInfo,
    TableInfo,
)
from dera_connectors.sqlite.connection import SqliteConnectionManager
from dera_connectors.sqlite.queries import (
    QUERY_ALL_TABLES,
    QUERY_DATABASE_LIST,
    QUERY_SQLITE_VERSION,
    QUERY_TABLE_BY_NAME,
)

# Regex to detect STRICT and WITHOUT ROWID options at the close of CREATE TABLE statements
_STRICT_TABLE_REGEX = re.compile(r"\bSTRICT\b", re.IGNORECASE)
_WITHOUT_ROWID_REGEX = re.compile(r"\bWITHOUT\s+ROWID\b", re.IGNORECASE)


async def introspect_identity(
    conn_mgr: SqliteConnectionManager,
    database_name: str,
) -> DatabaseIdentity:
    """Discover SQLite runtime version and identity information."""
    rows = await conn_mgr.execute_query(QUERY_SQLITE_VERSION)
    server_version = rows[0][0] if rows and len(rows[0]) > 0 else "unknown"

    return DatabaseIdentity(
        engine=DatabaseEngine.SQLITE,
        server_version=str(server_version),
        driver_version=sqlite3.sqlite_version,
        provider=DatabaseProvider.GENERIC,
        database_name=database_name,
        connector_version="0.1.0-dev",
        server_capability_hints={
            "c_version": sqlite3.sqlite_version,
            "runtime_version": server_version,
            "py_sqlite_version": sqlite3.version,
        },
    )


async def introspect_schemas(
    conn_mgr: SqliteConnectionManager,
) -> list[SchemaInfo]:
    """Enumerate database namespaces from PRAGMA database_list."""
    rows = await conn_mgr.execute_query(QUERY_DATABASE_LIST)
    schemas: list[SchemaInfo] = []

    # Columns: seq, name, file
    for row in rows:
        name = row["name"]
        schemas.append(
            SchemaInfo(
                schema_name=name,
                comment=f"SQLite database namespace backed by {row['file'] or ':memory:'}",
            )
        )

    if not schemas:
        schemas.append(SchemaInfo(schema_name="main", comment="Primary SQLite database schema"))

    return sorted(schemas, key=lambda s: (0 if s.schema_name == "main" else 1, s.schema_name))


def parse_table_options(table_sql: str | None) -> dict[str, Any]:
    """Parse table options such as WITHOUT ROWID and STRICT from CREATE TABLE SQL."""
    options: dict[str, Any] = {
        "is_strict": False,
        "without_rowid": False,
    }
    if not table_sql:
        return options

    # Normalize whitespace
    clean_sql = " ".join(table_sql.split())

    # Find the final closing parenthesis
    last_paren_idx = clean_sql.rfind(")")
    if last_paren_idx != -1:
        trailing_options = clean_sql[last_paren_idx + 1 :]
        if _STRICT_TABLE_REGEX.search(trailing_options):
            options["is_strict"] = True
        if _WITHOUT_ROWID_REGEX.search(trailing_options):
            options["without_rowid"] = True

    return options


async def introspect_tables(
    conn_mgr: SqliteConnectionManager,
    schema: str | None = None,
    table_filter: str | None = None,
) -> list[TableInfo]:
    """Enumerate user tables and virtual tables from sqlite_schema."""
    target_schema = schema or "main"

    if table_filter:
        rows = await conn_mgr.execute_query(QUERY_TABLE_BY_NAME, (table_filter,))
    else:
        rows = await conn_mgr.execute_query(QUERY_ALL_TABLES)

    tables: list[TableInfo] = []
    for row in rows:
        t_name = row["table_name"]
        t_type = row["object_type"].upper()
        t_sql = row["table_sql"]

        opts = parse_table_options(t_sql)
        opts["sql"] = t_sql

        tables.append(
            TableInfo(
                schema_name=target_schema,
                table_name=t_name,
                object_type="TABLE" if t_type == "TABLE" else t_type,
                comment=None,
                engine_specific=opts,
            )
        )

    return sorted(tables, key=lambda t: (t.schema_name, t.table_name))
