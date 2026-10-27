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
    ColumnInfo,
    SchemaInfo,
    TableInfo,
)
from dera_connectors.sqlite.connection import SqliteConnectionManager
from dera_connectors.sqlite.queries import (
    QUERY_ALL_TABLES,
    QUERY_DATABASE_LIST,
    QUERY_SQLITE_VERSION,
    QUERY_TABLE_BY_NAME,
    build_pragma_table_info,
    build_pragma_table_xinfo,
)
from dera_connectors.sqlite.types import determine_sqlite_affinity

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


async def introspect_columns(
    conn_mgr: SqliteConnectionManager,
    table: str,
    schema: str | None = None,
) -> list[ColumnInfo]:
    """Inspect table columns using PRAGMA table_xinfo with table_info fallback."""
    target_schema = schema or "main"

    try:
        rows = await conn_mgr.execute_query(build_pragma_table_xinfo(table))
    except Exception:
        # Fallback to standard table_info on older SQLite versions
        rows = await conn_mgr.execute_query(build_pragma_table_info(table))

    columns: list[ColumnInfo] = []
    for row in rows:
        cid = int(row["cid"])
        col_name = str(row["name"])
        declared_type = str(row["type"]) if row["type"] is not None else ""
        notnull = bool(row["notnull"])
        dflt_value = str(row["dflt_value"]) if row["dflt_value"] is not None else None
        pk_pos = int(row["pk"])

        # Determine hidden flag (0=normal, 1=hidden, 2=stored generated, 3=virtual generated)
        hidden_flag = int(row["hidden"]) if "hidden" in row.keys() else 0
        is_generated = hidden_flag in (2, 3)

        affinity = determine_sqlite_affinity(declared_type)

        engine_specific: dict[str, Any] = {
            "affinity": affinity.value,
            "hidden_flag": hidden_flag,
            "pk_order": pk_pos,
        }
        if is_generated:
            engine_specific["generation_type"] = "STORED" if hidden_flag == 2 else "VIRTUAL"

        columns.append(
            ColumnInfo(
                schema_name=target_schema,
                table_name=table,
                column_name=col_name,
                ordinal_position=cid + 1,  # 1-based indexing for standard DERA contract
                data_type=affinity.value.lower(),
                native_type=declared_type or affinity.value,
                is_nullable=not notnull,
                default_value=dflt_value,
                is_primary_key=pk_pos > 0,
                is_identity=False,
                is_generated=is_generated,
                comment=None,
                engine_specific=engine_specific,
            )
        )

    return sorted(columns, key=lambda c: c.ordinal_position)

