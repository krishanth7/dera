"""DERA MySQL-Family Connectors — Deterministic Catalog Introspection.

Provides strongly-typed, read-only metadata introspection routines for MySQL and MariaDB
databases querying INFORMATION_SCHEMA tables with deterministic sorting and least privilege.
"""

from __future__ import annotations

from typing import Any

from dera_connectors.context import CancellationToken
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
from dera_connectors.mysql_family.connection import MySqlFamilyConnectionManager
from dera_connectors.mysql_family.queries import (
    QUERY_CHECK_CONSTRAINTS_FALLBACK,
    QUERY_CHECK_CONSTRAINTS_MYSQL8,
    QUERY_COLUMNS,
    QUERY_FOREIGN_KEYS,
    QUERY_IDENTITY,
    QUERY_INDEXES,
    QUERY_INDEXES_MYSQL8,
    QUERY_PRIMARY_KEY,
    QUERY_SCHEMAS,
    QUERY_TABLES,
    QUERY_TRIGGERS,
    QUERY_UNIQUE_CONSTRAINTS,
    QUERY_VIEWS,
)
from dera_connectors.mysql_family.types import parse_column_type_attributes


async def introspect_identity(
    conn_mgr: MySqlFamilyConnectionManager,
    default_engine: DatabaseEngine = DatabaseEngine.MYSQL,
    cancellation_token: CancellationToken | None = None,
    timeout: float | None = None,
) -> DatabaseIdentity:
    """Introspect server identity, version, dialect, and hosting provider.

    Parameters
    ----------
    conn_mgr : MySqlFamilyConnectionManager
        Active connection manager.
    default_engine : DatabaseEngine
        Expected default engine type.
    cancellation_token : CancellationToken | None
        Optional cancellation token.
    timeout : float | None
        Operation timeout in seconds.

    Returns
    -------
    DatabaseIdentity
        Sanitized database server identity and fingerprint.
    """
    row = await conn_mgr.fetchrow(
        QUERY_IDENTITY,
        cancellation_token=cancellation_token,
        timeout=timeout,
    )
    if not row:
        return DatabaseIdentity(
            engine=default_engine,
            server_version=None,
            driver_version="PyMySQL",
            provider=DatabaseProvider.GENERIC,
            database_name=None,
        )

    server_version = str(row.get("server_version") or "")
    version_comment = str(row.get("version_comment") or "").lower()
    current_db = row.get("current_database")
    current_user = str(row.get("current_user") or "")

    # Detect MariaDB vs MySQL
    # MariaDB versions typically contain "MariaDB" in version string or version_comment
    is_mariadb = "mariadb" in server_version.lower() or "mariadb" in version_comment
    engine = DatabaseEngine.MARIADB if is_mariadb else DatabaseEngine.MYSQL

    # Detect Cloud Provider / Variant
    provider = DatabaseProvider.GENERIC
    if "aurora" in version_comment:
        provider = DatabaseProvider.AWS_AURORA
    elif "rds" in version_comment or "amazon" in version_comment:
        provider = DatabaseProvider.AWS_RDS
    elif "google" in version_comment or "cloudsql" in version_comment:
        provider = DatabaseProvider.GCP_CLOUDSQL

    hints: dict[str, Any] = {
        "version_comment": version_comment,
        "is_mariadb": is_mariadb,
        "current_user": current_user,
    }

    return DatabaseIdentity(
        engine=engine,
        server_version=server_version,
        driver_version="PyMySQL",
        provider=provider,
        database_name=str(current_db) if current_db else None,
        server_capability_hints=hints,
    )


async def introspect_schemas(
    conn_mgr: MySqlFamilyConnectionManager,
    cancellation_token: CancellationToken | None = None,
    timeout: float | None = None,
) -> list[SchemaInfo]:
    """Inspect user-accessible database schemas excluding internal system databases.

    Parameters
    ----------
    conn_mgr : MySqlFamilyConnectionManager
        Active connection manager.
    cancellation_token : CancellationToken | None
        Optional cancellation token.
    timeout : float | None
        Operation timeout in seconds.

    Returns
    -------
    list[SchemaInfo]
        Deterministically sorted list of user schemas.
    """
    rows = await conn_mgr.fetch(
        QUERY_SCHEMAS,
        cancellation_token=cancellation_token,
        timeout=timeout,
    )
    schemas = [
        SchemaInfo(
            schema_name=str(r["schema_name"]),
            comment=f"Charset: {r.get('character_set')}, Collation: {r.get('collation_name')}"
            if r.get("character_set")
            else None,
        )
        for r in rows
    ]
    return sorted(schemas, key=lambda s: s.schema_name)


async def introspect_tables(
    conn_mgr: MySqlFamilyConnectionManager,
    schema_name: str,
    cancellation_token: CancellationToken | None = None,
    timeout: float | None = None,
) -> list[TableInfo]:
    """Inspect tables within a specific schema.

    Parameters
    ----------
    conn_mgr : MySqlFamilyConnectionManager
        Active connection manager.
    schema_name : str
        Target schema name.
    cancellation_token : CancellationToken | None
        Optional cancellation token.
    timeout : float | None
        Operation timeout in seconds.

    Returns
    -------
    list[TableInfo]
        Deterministically sorted list of tables in schema.
    """
    rows = await conn_mgr.fetch(
        QUERY_TABLES,
        (schema_name,),
        cancellation_token=cancellation_token,
        timeout=timeout,
    )
    tables: list[TableInfo] = []
    for r in rows:
        obj_type = str(r.get("object_type") or "TABLE").upper()
        if obj_type == "BASE TABLE":
            obj_type = "TABLE"

        engine_specific: dict[str, Any] = {}
        if r.get("storage_engine"):
            engine_specific["storage_engine"] = str(r["storage_engine"])
        if r.get("collation_name"):
            engine_specific["collation"] = str(r["collation_name"])
        if r.get("auto_increment_val") is not None:
            engine_specific["auto_increment"] = r["auto_increment_val"]

        tables.append(
            TableInfo(
                schema_name=str(r["schema_name"]),
                table_name=str(r["table_name"]),
                object_type=obj_type,
                comment=r.get("comment") or None,
                engine_specific=engine_specific,
            )
        )
    return sorted(tables, key=lambda t: t.table_name)


async def introspect_columns(
    conn_mgr: MySqlFamilyConnectionManager,
    schema_name: str,
    table_name: str,
    cancellation_token: CancellationToken | None = None,
    timeout: float | None = None,
) -> list[ColumnInfo]:
    """Inspect columns for a table with parsed attributes and generated column status.

    Parameters
    ----------
    conn_mgr : MySqlFamilyConnectionManager
        Active connection manager.
    schema_name : str
        Target schema name.
    table_name : str
        Target table name.
    cancellation_token : CancellationToken | None
        Optional cancellation token.
    timeout : float | None
        Operation timeout in seconds.

    Returns
    -------
    list[ColumnInfo]
        Deterministically sorted list of column definitions ordered by ordinal position.
    """
    rows = await conn_mgr.fetch(
        QUERY_COLUMNS,
        (schema_name, table_name),
        cancellation_token=cancellation_token,
        timeout=timeout,
    )
    columns: list[ColumnInfo] = []
    for r in rows:
        col_type = str(r.get("column_type") or "")
        data_type = str(r.get("data_type") or "")
        extra = str(r.get("extra") or "").lower()
        gen_expr = r.get("generation_expression")

        is_identity = "auto_increment" in extra
        is_generated = (
            "virtual" in extra or "stored" in extra or "persistent" in extra or bool(gen_expr)
        )

        parsed_attrs = parse_column_type_attributes(col_type, data_type)
        engine_specific: dict[str, Any] = {
            "column_type": col_type,
            **parsed_attrs,
        }
        if r.get("character_set"):
            engine_specific["character_set"] = str(r["character_set"])
        if r.get("collation_name"):
            engine_specific["collation"] = str(r["collation_name"])
        if "virtual" in extra:
            engine_specific["generation_type"] = "VIRTUAL"
        elif "stored" in extra or "persistent" in extra:
            engine_specific["generation_type"] = "STORED"

        columns.append(
            ColumnInfo(
                schema_name=str(r["schema_name"]),
                table_name=str(r["table_name"]),
                column_name=str(r["column_name"]),
                ordinal_position=int(r["ordinal_position"]),
                data_type=data_type,
                is_nullable=str(r.get("is_nullable") or "").upper() == "YES",
                default_expression=r.get("default_expression"),
                is_identity=is_identity,
                is_generated=is_generated,
                generation_expression=str(gen_expr) if gen_expr else None,
                comment=r.get("comment") or None,
                engine_specific=engine_specific,
            )
        )
    return sorted(columns, key=lambda c: c.ordinal_position)


async def introspect_primary_key(
    conn_mgr: MySqlFamilyConnectionManager,
    schema_name: str,
    table_name: str,
    cancellation_token: CancellationToken | None = None,
    timeout: float | None = None,
) -> PrimaryKeyInfo | None:
    """Inspect primary key constraint and participating columns.

    Parameters
    ----------
    conn_mgr : MySqlFamilyConnectionManager
        Active connection manager.
    schema_name : str
        Target schema name.
    table_name : str
        Target table name.
    cancellation_token : CancellationToken | None
        Optional cancellation token.
    timeout : float | None
        Operation timeout in seconds.

    Returns
    -------
    PrimaryKeyInfo | None
        Primary key metadata if one exists, otherwise None.
    """
    rows = await conn_mgr.fetch(
        QUERY_PRIMARY_KEY,
        (schema_name, table_name),
        cancellation_token=cancellation_token,
        timeout=timeout,
    )
    if not rows:
        return None

    col_names = [str(r["column_name"]) for r in rows]
    return PrimaryKeyInfo(
        constraint_name="PRIMARY",
        schema_name=schema_name,
        table_name=table_name,
        column_names=col_names,
    )


async def introspect_foreign_keys(
    conn_mgr: MySqlFamilyConnectionManager,
    schema_name: str,
    table_name: str,
    cancellation_token: CancellationToken | None = None,
    timeout: float | None = None,
) -> list[ForeignKeyInfo]:
    """Inspect foreign key constraints and referential actions.

    Parameters
    ----------
    conn_mgr : MySqlFamilyConnectionManager
        Active connection manager.
    schema_name : str
        Target schema name.
    table_name : str
        Target table name.
    cancellation_token : CancellationToken | None
        Optional cancellation token.
    timeout : float | None
        Operation timeout in seconds.

    Returns
    -------
    list[ForeignKeyInfo]
        Deterministically sorted list of foreign key definitions.
    """
    rows = await conn_mgr.fetch(
        QUERY_FOREIGN_KEYS,
        (schema_name, table_name),
        cancellation_token=cancellation_token,
        timeout=timeout,
    )
    grouped: dict[str, dict[str, Any]] = {}
    for r in rows:
        name = str(r["constraint_name"])
        if name not in grouped:
            grouped[name] = {
                "constraint_name": name,
                "schema_name": str(r["schema_name"]),
                "table_name": str(r["table_name"]),
                "column_names": [],
                "referenced_schema": str(r["referenced_schema"]),
                "referenced_table": str(r["referenced_table"]),
                "referenced_columns": [],
                "on_update": str(r.get("update_rule") or "NO ACTION"),
                "on_delete": str(r.get("delete_rule") or "NO ACTION"),
            }
        grouped[name]["column_names"].append(str(r["column_name"]))
        grouped[name]["referenced_columns"].append(str(r["referenced_column"]))

    fks = [
        ForeignKeyInfo(
            constraint_name=data["constraint_name"],
            schema_name=data["schema_name"],
            table_name=data["table_name"],
            column_names=data["column_names"],
            referenced_schema=data["referenced_schema"],
            referenced_table=data["referenced_table"],
            referenced_columns=data["referenced_columns"],
            on_update=data["on_update"],
            on_delete=data["on_delete"],
        )
        for data in grouped.values()
    ]
    return sorted(fks, key=lambda f: f.constraint_name or "")


async def introspect_unique_constraints(
    conn_mgr: MySqlFamilyConnectionManager,
    schema_name: str,
    table_name: str,
    cancellation_token: CancellationToken | None = None,
    timeout: float | None = None,
) -> list[UniqueConstraintInfo]:
    """Inspect unique constraints excluding primary key constraints.

    Parameters
    ----------
    conn_mgr : MySqlFamilyConnectionManager
        Active connection manager.
    schema_name : str
        Target schema name.
    table_name : str
        Target table name.
    cancellation_token : CancellationToken | None
        Optional cancellation token.
    timeout : float | None
        Operation timeout in seconds.

    Returns
    -------
    list[UniqueConstraintInfo]
        Deterministically sorted list of unique constraints.
    """
    rows = await conn_mgr.fetch(
        QUERY_UNIQUE_CONSTRAINTS,
        (schema_name, table_name),
        cancellation_token=cancellation_token,
        timeout=timeout,
    )
    grouped: dict[str, list[str]] = {}
    for r in rows:
        name = str(r["constraint_name"])
        grouped.setdefault(name, []).append(str(r["column_name"]))

    uqs = [
        UniqueConstraintInfo(
            constraint_name=name,
            schema_name=schema_name,
            table_name=table_name,
            column_names=cols,
        )
        for name, cols in grouped.items()
    ]
    return sorted(uqs, key=lambda u: u.constraint_name or "")


async def introspect_check_constraints(
    conn_mgr: MySqlFamilyConnectionManager,
    schema_name: str,
    table_name: str,
    is_mariadb: bool = False,
    cancellation_token: CancellationToken | None = None,
    timeout: float | None = None,
) -> list[CheckConstraintInfo]:
    """Inspect check constraints for MySQL 8.0.16+ or MariaDB 10.2+.

    Parameters
    ----------
    conn_mgr : MySqlFamilyConnectionManager
        Active connection manager.
    schema_name : str
        Target schema name.
    table_name : str
        Target table name.
    is_mariadb : bool
        Whether connected engine is MariaDB.
    cancellation_token : CancellationToken | None
        Optional cancellation token.
    timeout : float | None
        Operation timeout in seconds.

    Returns
    -------
    list[CheckConstraintInfo]
        Deterministically sorted list of check constraints, or empty list if unsupported.
    """
    rows: list[dict[str, Any]] = []
    if not is_mariadb:
        try:
            rows = await conn_mgr.fetch(
                QUERY_CHECK_CONSTRAINTS_MYSQL8,
                (schema_name, table_name),
                cancellation_token=cancellation_token,
                timeout=timeout,
            )
        except Exception:
            rows = []

    if not rows:
        try:
            fallback_rows = await conn_mgr.fetch(
                QUERY_CHECK_CONSTRAINTS_FALLBACK,
                (schema_name,),
                cancellation_token=cancellation_token,
                timeout=timeout,
            )
            rows = fallback_rows
        except Exception:
            rows = []

    checks: list[CheckConstraintInfo] = []
    for r in rows:
        clause = str(r.get("check_clause") or "")
        checks.append(
            CheckConstraintInfo(
                constraint_name=str(r.get("constraint_name")),
                schema_name=schema_name,
                table_name=table_name,
                check_clause=clause,
            )
        )
    return sorted(checks, key=lambda c: c.constraint_name or "")


async def introspect_indexes(
    conn_mgr: MySqlFamilyConnectionManager,
    schema_name: str,
    table_name: str,
    is_mysql8: bool = False,
    cancellation_token: CancellationToken | None = None,
    timeout: float | None = None,
) -> list[IndexInfo]:
    """Inspect indexes for a table including functional expressions and visibility where supported.

    Parameters
    ----------
    conn_mgr : MySqlFamilyConnectionManager
        Active connection manager.
    schema_name : str
        Target schema name.
    table_name : str
        Target table name.
    is_mysql8 : bool
        Whether connected server is MySQL 8.0+ supporting EXPRESSION and IS_VISIBLE columns.
    cancellation_token : CancellationToken | None
        Optional cancellation token.
    timeout : float | None
        Operation timeout in seconds.

    Returns
    -------
    list[IndexInfo]
        Deterministically sorted list of secondary and primary indexes.
    """
    rows: list[dict[str, Any]] = []
    if is_mysql8:
        try:
            rows = await conn_mgr.fetch(
                QUERY_INDEXES_MYSQL8,
                (schema_name, table_name),
                cancellation_token=cancellation_token,
                timeout=timeout,
            )
        except Exception:
            rows = await conn_mgr.fetch(
                QUERY_INDEXES,
                (schema_name, table_name),
                cancellation_token=cancellation_token,
                timeout=timeout,
            )
    else:
        rows = await conn_mgr.fetch(
            QUERY_INDEXES,
            (schema_name, table_name),
            cancellation_token=cancellation_token,
            timeout=timeout,
        )

    grouped: dict[str, dict[str, Any]] = {}
    for r in rows:
        name = str(r["index_name"])
        col_name = r.get("column_name")
        expr = r.get("expression")
        term = str(expr) if expr else str(col_name or "")

        if name not in grouped:
            is_non_unique = bool(r.get("non_unique", 1))
            is_primary = name.upper() == "PRIMARY"
            engine_specific: dict[str, Any] = {}
            if r.get("sub_part"):
                engine_specific["sub_part"] = r["sub_part"]
            if r.get("collation"):
                engine_specific["collation"] = r["collation"]
            if r.get("is_visible") is not None:
                engine_specific["is_visible"] = str(r["is_visible"]).upper() == "YES"

            grouped[name] = {
                "index_name": name,
                "is_unique": not is_non_unique,
                "is_primary": is_primary,
                "index_type": str(r.get("index_type") or "BTREE").upper(),
                "terms": [],
                "engine_specific": engine_specific,
            }

        grouped[name]["terms"].append(term)

    indexes = [
        IndexInfo(
            index_name=data["index_name"],
            schema_name=schema_name,
            table_name=table_name,
            column_names=data["terms"],
            is_unique=data["is_unique"],
            is_primary=data["is_primary"],
            index_type=data["index_type"],
            engine_specific=data["engine_specific"],
        )
        for data in grouped.values()
    ]
    return sorted(indexes, key=lambda i: i.index_name)


async def introspect_views(
    conn_mgr: MySqlFamilyConnectionManager,
    schema_name: str,
    cancellation_token: CancellationToken | None = None,
    timeout: float | None = None,
) -> list[ViewInfo]:
    """Inspect views and view definitions within a schema.

    Parameters
    ----------
    conn_mgr : MySqlFamilyConnectionManager
        Active connection manager.
    schema_name : str
        Target schema name.
    cancellation_token : CancellationToken | None
        Optional cancellation token.
    timeout : float | None
        Operation timeout in seconds.

    Returns
    -------
    list[ViewInfo]
        Deterministically sorted list of views.
    """
    rows = await conn_mgr.fetch(
        QUERY_VIEWS,
        (schema_name,),
        cancellation_token=cancellation_token,
        timeout=timeout,
    )
    views: list[ViewInfo] = []
    for r in rows:
        engine_specific: dict[str, Any] = {}
        if r.get("check_option"):
            engine_specific["check_option"] = str(r["check_option"])
        if r.get("is_updatable"):
            engine_specific["is_updatable"] = str(r["is_updatable"]).upper() == "YES"
        if r.get("security_type"):
            engine_specific["security_type"] = str(r["security_type"])
        if r.get("definer"):
            engine_specific["definer"] = str(r["definer"])

        views.append(
            ViewInfo(
                schema_name=str(r["schema_name"]),
                view_name=str(r["view_name"]),
                is_materialized=False,
                view_definition=r.get("view_definition"),
                engine_specific=engine_specific,
            )
        )
    return sorted(views, key=lambda v: v.view_name)


async def introspect_triggers(
    conn_mgr: MySqlFamilyConnectionManager,
    schema_name: str,
    table_name: str | None = None,
    cancellation_token: CancellationToken | None = None,
    timeout: float | None = None,
) -> list[TriggerInfo]:
    """Inspect triggers within a schema and optionally filter by table.

    Parameters
    ----------
    conn_mgr : MySqlFamilyConnectionManager
        Active connection manager.
    schema_name : str
        Target schema name.
    table_name : str | None
        Optional table name to filter triggers.
    cancellation_token : CancellationToken | None
        Optional cancellation token.
    timeout : float | None
        Operation timeout in seconds.

    Returns
    -------
    list[TriggerInfo]
        Deterministically sorted list of triggers.
    """
    rows = await conn_mgr.fetch(
        QUERY_TRIGGERS,
        (schema_name,),
        cancellation_token=cancellation_token,
        timeout=timeout,
    )
    triggers: list[TriggerInfo] = []
    for r in rows:
        target_table = str(r.get("table_name") or "")
        if table_name is not None and target_table != table_name:
            continue

        engine_specific: dict[str, Any] = {}
        if r.get("definer"):
            engine_specific["definer"] = str(r["definer"])

        triggers.append(
            TriggerInfo(
                schema_name=str(r["schema_name"]),
                table_name=target_table,
                trigger_name=str(r["trigger_name"]),
                timing=str(r.get("action_timing") or "BEFORE").upper(),
                event=str(r.get("event_manipulation") or "INSERT").upper(),
                definition=r.get("action_statement"),
                is_enabled=True,
                engine_specific=engine_specific,
            )
        )
    return sorted(triggers, key=lambda t: t.trigger_name)
