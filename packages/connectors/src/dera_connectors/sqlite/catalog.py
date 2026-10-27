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
    CheckConstraintInfo,
    ColumnInfo,
    ForeignKeyInfo,
    IndexInfo,
    PrimaryKeyInfo,
    SchemaInfo,
    TableInfo,
    TriggerInfo,
    UniqueConstraintInfo,
    ViewInfo,
)
from dera_connectors.sqlite.connection import SqliteConnectionManager
from dera_connectors.sqlite.queries import (
    QUERY_ALL_TABLES,
    QUERY_ALL_TRIGGERS,
    QUERY_ALL_VIEWS,
    QUERY_DATABASE_LIST,
    QUERY_SQLITE_VERSION,
    QUERY_TABLE_BY_NAME,
    QUERY_TRIGGERS_BY_TABLE,
    QUERY_VIEW_BY_NAME,
    build_pragma_foreign_key_list,
    build_pragma_index_info,
    build_pragma_index_list,
    build_pragma_index_xinfo,
    build_pragma_table_info,
    build_pragma_table_xinfo,
)
from dera_connectors.sqlite.types import determine_sqlite_affinity

# Regex to detect STRICT and WITHOUT ROWID options at the close of CREATE TABLE statements
_STRICT_TABLE_REGEX = re.compile(r"\bSTRICT\b", re.IGNORECASE)
_WITHOUT_ROWID_REGEX = re.compile(r"\bWITHOUT\s+ROWID\b", re.IGNORECASE)
_TRIGGER_EVENT_REGEX = re.compile(
    r"\b(BEFORE|AFTER|INSTEAD\s+OF)\s+(INSERT|UPDATE(?:\s+OF\s+[^\s]+)?|DELETE)\b",
    re.IGNORECASE,
)


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
            "sqlite_version": sqlite3.sqlite_version,
        },
    )


async def introspect_schemas(
    conn_mgr: SqliteConnectionManager,
) -> list[SchemaInfo]:
    """Enumerate database namespaces from PRAGMA database_list."""
    rows = await conn_mgr.execute_query(QUERY_DATABASE_LIST)
    schemas: list[SchemaInfo] = []

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

    clean_sql = " ".join(table_sql.split())
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
        rows = await conn_mgr.execute_query(build_pragma_table_info(table))

    columns: list[ColumnInfo] = []
    for row in rows:
        cid = int(row["cid"])
        col_name = str(row["name"])
        declared_type = str(row["type"]) if row["type"] is not None else ""
        notnull = bool(row["notnull"])
        dflt_value = str(row["dflt_value"]) if row["dflt_value"] is not None else None
        pk_pos = int(row["pk"])

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
                ordinal_position=cid + 1,
                data_type=declared_type or affinity.value.lower(),
                is_nullable=not notnull,
                default_expression=dflt_value,
                is_identity=False,
                is_generated=is_generated,
                comment=None,
                engine_specific=engine_specific,
            )
        )

    return sorted(columns, key=lambda c: c.ordinal_position)


async def introspect_primary_key(
    conn_mgr: SqliteConnectionManager,
    table: str,
    schema: str | None = None,
) -> PrimaryKeyInfo | None:
    """Inspect primary key constraint and composite column ordering."""
    target_schema = schema or "main"
    columns = await introspect_columns(conn_mgr, table, schema=target_schema)

    pk_cols = [c for c in columns if c.engine_specific.get("pk_order", 0) > 0]
    if not pk_cols:
        return None

    # Sort PK columns by pk_order in engine_specific
    pk_cols.sort(key=lambda c: c.engine_specific.get("pk_order", 0))
    pk_names = [c.column_name for c in pk_cols]

    return PrimaryKeyInfo(
        constraint_name=f"pk_{table}",
        schema_name=target_schema,
        table_name=table,
        column_names=pk_names,
    )


async def introspect_foreign_keys(
    conn_mgr: SqliteConnectionManager,
    table: str,
    schema: str | None = None,
) -> list[ForeignKeyInfo]:
    """Inspect foreign key constraints using PRAGMA foreign_key_list."""
    target_schema = schema or "main"
    rows = await conn_mgr.execute_query(build_pragma_foreign_key_list(table))

    # Group by fk id
    fk_groups: dict[int, list[sqlite3.Row]] = {}
    for row in rows:
        fk_id = int(row["id"])
        fk_groups.setdefault(fk_id, []).append(row)

    foreign_keys: list[ForeignKeyInfo] = []
    for fk_id, items in fk_groups.items():
        # Sort column pairs by sequence
        items.sort(key=lambda r: int(r["seq"]))
        first = items[0]
        ref_table = str(first["table"])
        on_update = str(first["on_update"]) if first["on_update"] else "NO ACTION"
        on_delete = str(first["on_delete"]) if first["on_delete"] else "NO ACTION"

        column_names = [str(it["from"]) for it in items]
        referenced_columns = [str(it["to"]) if it["to"] else str(it["from"]) for it in items]

        foreign_keys.append(
            ForeignKeyInfo(
                constraint_name=f"fk_{table}_{fk_id}",
                schema_name=target_schema,
                table_name=table,
                column_names=column_names,
                referenced_schema=target_schema,
                referenced_table=ref_table,
                referenced_columns=referenced_columns,
                on_update=on_update,
                on_delete=on_delete,
            )
        )

    return sorted(foreign_keys, key=lambda f: f.constraint_name)


async def introspect_unique_constraints(
    conn_mgr: SqliteConnectionManager,
    table: str,
    schema: str | None = None,
) -> list[UniqueConstraintInfo]:
    """Inspect unique constraints from PRAGMA index_list with origin 'u' or 'pk'."""
    target_schema = schema or "main"
    rows = await conn_mgr.execute_query(build_pragma_index_list(table))

    unique_constraints: list[UniqueConstraintInfo] = []
    for row in rows:
        is_unique = bool(row["unique"])
        origin = str(row["origin"]).lower() if "origin" in row.keys() else ""
        idx_name = str(row["name"])

        # Differentiate unique constraints from user-created unique indexes (origin == 'c')
        if is_unique and origin in ("u", "pk"):
            # Get columns participating in this unique constraint
            col_rows = await conn_mgr.execute_query(build_pragma_index_info(idx_name))
            col_rows_sorted = sorted(col_rows, key=lambda r: int(r["seqno"]))
            col_names = [str(r["name"]) for r in col_rows_sorted if r["name"]]

            unique_constraints.append(
                UniqueConstraintInfo(
                    constraint_name=idx_name,
                    schema_name=target_schema,
                    table_name=table,
                    column_names=col_names,
                    is_deferrable=False,
                    is_initially_deferred=False,
                )
            )

    return sorted(unique_constraints, key=lambda u: u.constraint_name)


def extract_check_constraints_from_sql(
    schema_name: str,
    table_name: str,
    table_sql: str | None,
) -> list[CheckConstraintInfo]:
    """Safely extract CHECK constraints from table DDL without executing SQL."""
    if not table_sql:
        return []

    results: list[CheckConstraintInfo] = []
    pos = 0
    upper_sql = table_sql.upper()
    check_counter = 1

    while True:
        idx = upper_sql.find("CHECK", pos)
        if idx == -1:
            break

        is_start_word = idx == 0 or not (upper_sql[idx - 1].isalnum() or upper_sql[idx - 1] == "_")
        is_end_word = (idx + 5 >= len(upper_sql)) or not (
            upper_sql[idx + 5].isalnum() or upper_sql[idx + 5] == "_"
        )

        if not (is_start_word and is_end_word):
            pos = idx + 5
            continue

        open_paren_idx = table_sql.find("(", idx + 5)
        if open_paren_idx == -1:
            pos = idx + 5
            continue

        depth = 0
        in_string = False
        string_char = ""
        end_paren_idx = -1

        for i in range(open_paren_idx, len(table_sql)):
            ch = table_sql[i]
            if in_string:
                if ch == string_char:
                    if i + 1 < len(table_sql) and table_sql[i + 1] == string_char:
                        continue
                    in_string = False
            else:
                if ch in ("'", '"', "`"):
                    in_string = True
                    string_char = ch
                elif ch == "(":
                    depth += 1
                elif ch == ")":
                    depth -= 1
                    if depth == 0:
                        end_paren_idx = i
                        break

        if end_paren_idx != -1:
            check_clause = table_sql[open_paren_idx + 1 : end_paren_idx].strip()
            prefix = table_sql[:idx].strip()
            constraint_name = None
            if "CONSTRAINT" in prefix.upper():
                c_idx = prefix.upper().rfind("CONSTRAINT")
                c_name_part = prefix[c_idx + 10 :].strip()
                if c_name_part:
                    constraint_name = c_name_part.split()[-1].strip("\"`[]'")

            if not constraint_name:
                constraint_name = f"chk_{table_name}_{check_counter}"

            results.append(
                CheckConstraintInfo(
                    constraint_name=constraint_name,
                    schema_name=schema_name,
                    table_name=table_name,
                    check_clause=check_clause,
                )
            )
            check_counter += 1
            pos = end_paren_idx + 1
        else:
            pos = idx + 5

    return sorted(results, key=lambda c: c.constraint_name or "")


async def introspect_check_constraints(
    conn_mgr: SqliteConnectionManager,
    table: str,
    schema: str | None = None,
) -> list[CheckConstraintInfo]:
    """Inspect check constraints by safely parsing table DDL."""
    target_schema = schema or "main"
    rows = await conn_mgr.execute_query(QUERY_TABLE_BY_NAME, (table,))
    if not rows:
        return []

    table_sql = rows[0]["table_sql"]
    return extract_check_constraints_from_sql(target_schema, table, table_sql)


async def introspect_indexes(
    conn_mgr: SqliteConnectionManager,
    table: str,
    schema: str | None = None,
) -> list[IndexInfo]:
    """Inspect indexes for table using PRAGMA index_list and index_xinfo."""
    target_schema = schema or "main"
    rows = await conn_mgr.execute_query(build_pragma_index_list(table))

    indexes: list[IndexInfo] = []
    for row in rows:
        idx_name = str(row["name"])
        is_unique = bool(row["unique"])
        origin = str(row["origin"]).lower() if "origin" in row.keys() else "c"
        is_partial = bool(row["partial"]) if "partial" in row.keys() else False

        # PRAGMA index_xinfo: seqno, cid, name, desc, coll, key
        try:
            term_rows = await conn_mgr.execute_query(build_pragma_index_xinfo(idx_name))
        except Exception:
            term_rows = await conn_mgr.execute_query(build_pragma_index_info(idx_name))

        term_rows_filtered = [
            t for t in term_rows if (bool(t["key"]) if "key" in t.keys() else True)
        ]
        term_rows_sorted = sorted(term_rows_filtered, key=lambda r: int(r["seqno"]))
        column_names = [
            str(t["name"]) if t["name"] else f"expr_term_{int(t['seqno'])}"
            for t in term_rows_sorted
        ]

        indexes.append(
            IndexInfo(
                index_name=idx_name,
                schema_name=target_schema,
                table_name=table,
                column_names=column_names,
                is_unique=is_unique,
                is_primary=origin == "pk",
                index_type="BTREE",
                predicate="partial index" if is_partial else None,
                engine_specific={
                    "origin": origin,
                    "is_partial": is_partial,
                },
            )
        )

    return sorted(indexes, key=lambda idx: idx.index_name)


async def introspect_views(
    conn_mgr: SqliteConnectionManager,
    schema: str | None = None,
    view_filter: str | None = None,
) -> list[ViewInfo]:
    """Inspect SQL views from sqlite_schema without executing view definitions."""
    target_schema = schema or "main"

    if view_filter:
        rows = await conn_mgr.execute_query(QUERY_VIEW_BY_NAME, (view_filter,))
    else:
        rows = await conn_mgr.execute_query(QUERY_ALL_VIEWS)

    views: list[ViewInfo] = []
    for row in rows:
        v_name = str(row["view_name"])
        v_sql = str(row["view_sql"]) if row["view_sql"] else None

        views.append(
            ViewInfo(
                schema_name=target_schema,
                view_name=v_name,
                is_materialized=False,
                view_definition=v_sql,
                comment=None,
            )
        )

    return sorted(views, key=lambda v: (v.schema_name, v.view_name))


async def introspect_triggers(
    conn_mgr: SqliteConnectionManager,
    table: str | None = None,
    schema: str | None = None,
) -> list[TriggerInfo]:
    """Inspect triggers from sqlite_schema without executing trigger bodies."""
    target_schema = schema or "main"

    if table:
        rows = await conn_mgr.execute_query(QUERY_TRIGGERS_BY_TABLE, (table,))
    else:
        rows = await conn_mgr.execute_query(QUERY_ALL_TRIGGERS)

    triggers: list[TriggerInfo] = []
    for row in rows:
        tr_name = str(row["trigger_name"])
        tbl_name = str(row["table_name"])
        tr_sql = str(row["trigger_sql"]) if row["trigger_sql"] else ""

        timing = "BEFORE"
        event = "INSERT"
        match = _TRIGGER_EVENT_REGEX.search(tr_sql)
        if match:
            timing = match.group(1).upper()
            event = match.group(2).upper()

        triggers.append(
            TriggerInfo(
                schema_name=target_schema,
                table_name=tbl_name,
                trigger_name=tr_name,
                timing=timing,
                event=event,
                definition=tr_sql or None,
                is_enabled=True,
            )
        )

    return sorted(triggers, key=lambda tr: (tr.schema_name, tr.table_name, tr.trigger_name))
