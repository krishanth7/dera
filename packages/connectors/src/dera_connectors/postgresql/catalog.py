"""DERA PostgreSQL Connector — Catalog Inspection Engine.

Executes parameterized catalog queries against pg_catalog and transforms raw database
records into strongly typed, immutable DERA metadata models with deterministic sorting.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from dera_connectors.context import CancellationToken
from dera_connectors.engine import DatabaseEngine, DatabaseIdentity, DatabaseProvider
from dera_connectors.metadata import (
    CheckConstraintInfo,
    ColumnInfo,
    ForeignKeyInfo,
    IndexInfo,
    PartitionInfo,
    PrimaryKeyInfo,
    SchemaInfo,
    SequenceInfo,
    TableInfo,
    UniqueConstraintInfo,
    ViewInfo,
)
from dera_connectors.postgresql.queries import (
    QUERY_CHECK_CONSTRAINTS,
    QUERY_COLUMNS,
    QUERY_FOREIGN_KEYS,
    QUERY_IDENTITY,
    QUERY_INDEXES,
    QUERY_PARTITIONS,
    QUERY_PRIMARY_KEY,
    QUERY_SCHEMAS,
    QUERY_SEQUENCES,
    QUERY_TABLES,
    QUERY_UNIQUE_CONSTRAINTS,
    QUERY_VIEWS,
)

if TYPE_CHECKING:
    from dera_connectors.postgresql.connection import PostgresConnectionManager


async def inspect_identity(
    conn_mgr: PostgresConnectionManager,
    provider: DatabaseProvider = DatabaseProvider.GENERIC,
    cancellation_token: CancellationToken | None = None,
    timeout: float | None = None,
) -> DatabaseIdentity:
    """Discover server version, current database name, and driver details."""
    row = await conn_mgr.fetchrow(
        QUERY_IDENTITY,
        cancellation_token=cancellation_token,
        timeout=timeout,
    )

    if row is None:
        return DatabaseIdentity(
            engine=DatabaseEngine.POSTGRESQL,
            provider=provider,
            server_version="PostgreSQL (Unknown)",
            driver_version="asyncpg",
            connector_version="0.1.0-dev",
        )

    full_version = str(row["full_version"] or "PostgreSQL")
    version_num = int(row["version_num"] or 0)
    db_name = row["current_database"]

    # Short version extraction e.g. "PostgreSQL 16.2"
    first_part = full_version.split(" on ")[0] if " on " in full_version else full_version

    return DatabaseIdentity(
        engine=DatabaseEngine.POSTGRESQL,
        provider=provider,
        server_version=first_part.strip(),
        driver_version="asyncpg",
        database_name=str(db_name) if db_name else None,
        connector_version="0.1.0-dev",
        server_capability_hints={"server_version_num": version_num, "raw_version": full_version},
    )


async def inspect_schemas(
    conn_mgr: PostgresConnectionManager,
    cancellation_token: CancellationToken | None = None,
    timeout: float | None = None,
) -> list[SchemaInfo]:
    """Inspect and return user schemas in deterministic alphabetical order."""
    rows = await conn_mgr.fetch(
        QUERY_SCHEMAS,
        cancellation_token=cancellation_token,
        timeout=timeout,
    )

    schemas = [
        SchemaInfo(
            schema_name=str(r["schema_name"]),
            comment=r["comment"],
        )
        for r in rows
    ]

    return sorted(schemas, key=lambda s: s.schema_name)


async def inspect_tables(
    conn_mgr: PostgresConnectionManager,
    schema: str | None = None,
    cancellation_token: CancellationToken | None = None,
    timeout: float | None = None,
) -> list[TableInfo]:
    """Inspect tables, partitioned tables, and foreign tables in deterministic order."""
    rows = await conn_mgr.fetch(
        QUERY_TABLES,
        schema,
        cancellation_token=cancellation_token,
        timeout=timeout,
    )

    tables = [
        TableInfo(
            schema_name=str(r["schema_name"]),
            table_name=str(r["table_name"]),
            object_type=str(r["object_type"]),
            comment=r["comment"],
            engine_specific={
                "is_unlogged": bool(r["is_unlogged"]),
                "is_partitioned": bool(r["is_partitioned"]),
            },
        )
        for r in rows
    ]

    return sorted(tables, key=lambda t: (t.schema_name, t.table_name))


async def inspect_columns(
    conn_mgr: PostgresConnectionManager,
    schema: str | None,
    table: str,
    cancellation_token: CancellationToken | None = None,
    timeout: float | None = None,
) -> list[ColumnInfo]:
    """Inspect table columns in deterministic ordinal order."""
    rows = await conn_mgr.fetch(
        QUERY_COLUMNS,
        schema,
        table,
        cancellation_token=cancellation_token,
        timeout=timeout,
    )

    columns = [
        ColumnInfo(
            schema_name=str(r["schema_name"]),
            table_name=str(r["table_name"]),
            column_name=str(r["column_name"]),
            ordinal_position=int(r["ordinal_position"]),
            data_type=str(r["data_type"]),
            is_nullable=bool(r["is_nullable"]),
            default_expression=r["default_expression"],
            is_identity=bool(r["is_identity"]),
            is_generated=bool(r["is_generated"]),
            generation_expression=r["generation_expression"],
            comment=r["comment"],
            engine_specific={
                "collation": r["collation_name"],
            },
        )
        for r in rows
    ]

    return sorted(columns, key=lambda c: c.ordinal_position)


async def inspect_primary_key(
    conn_mgr: PostgresConnectionManager,
    schema: str | None,
    table: str,
    cancellation_token: CancellationToken | None = None,
    timeout: float | None = None,
) -> PrimaryKeyInfo | None:
    """Inspect primary key constraint for a table."""
    row = await conn_mgr.fetchrow(
        QUERY_PRIMARY_KEY,
        schema,
        table,
        cancellation_token=cancellation_token,
        timeout=timeout,
    )

    if row is None or not row["column_names"]:
        return None

    raw_cols = row["column_names"]
    col_names = [str(c) for c in raw_cols] if isinstance(raw_cols, (list, tuple)) else []

    return PrimaryKeyInfo(
        constraint_name=row["constraint_name"],
        schema_name=str(row["schema_name"]),
        table_name=str(row["table_name"]),
        column_names=col_names,
    )


async def inspect_foreign_keys(
    conn_mgr: PostgresConnectionManager,
    schema: str | None,
    table: str,
    cancellation_token: CancellationToken | None = None,
    timeout: float | None = None,
) -> list[ForeignKeyInfo]:
    """Inspect foreign key constraints for a table in deterministic order."""
    rows = await conn_mgr.fetch(
        QUERY_FOREIGN_KEYS,
        schema,
        table,
        cancellation_token=cancellation_token,
        timeout=timeout,
    )

    fks = []
    for r in rows:
        raw_cols = r["column_names"]
        col_names = [str(c) for c in raw_cols] if isinstance(raw_cols, (list, tuple)) else []
        raw_ref_cols = r["referenced_columns"]
        ref_cols = [str(c) for c in raw_ref_cols] if isinstance(raw_ref_cols, (list, tuple)) else []

        fks.append(
            ForeignKeyInfo(
                constraint_name=r["constraint_name"],
                schema_name=str(r["schema_name"]),
                table_name=str(r["table_name"]),
                column_names=col_names,
                referenced_schema=str(r["referenced_schema"]),
                referenced_table=str(r["referenced_table"]),
                referenced_columns=ref_cols,
                on_update=str(r["on_update"]),
                on_delete=str(r["on_delete"]),
            )
        )

    return sorted(fks, key=lambda fk: (fk.constraint_name or "", fk.column_names))


async def inspect_unique_constraints(
    conn_mgr: PostgresConnectionManager,
    schema: str | None,
    table: str,
    cancellation_token: CancellationToken | None = None,
    timeout: float | None = None,
) -> list[UniqueConstraintInfo]:
    """Inspect unique constraints for a table in deterministic order."""
    rows = await conn_mgr.fetch(
        QUERY_UNIQUE_CONSTRAINTS,
        schema,
        table,
        cancellation_token=cancellation_token,
        timeout=timeout,
    )

    ucs = []
    for r in rows:
        raw_cols = r["column_names"]
        col_names = [str(c) for c in raw_cols] if isinstance(raw_cols, (list, tuple)) else []

        ucs.append(
            UniqueConstraintInfo(
                constraint_name=r["constraint_name"],
                schema_name=str(r["schema_name"]),
                table_name=str(r["table_name"]),
                column_names=col_names,
            )
        )

    return sorted(ucs, key=lambda u: (u.constraint_name or "", u.column_names))


async def inspect_check_constraints(
    conn_mgr: PostgresConnectionManager,
    schema: str | None,
    table: str,
    cancellation_token: CancellationToken | None = None,
    timeout: float | None = None,
) -> list[CheckConstraintInfo]:
    """Inspect check constraints for a table in deterministic order."""
    rows = await conn_mgr.fetch(
        QUERY_CHECK_CONSTRAINTS,
        schema,
        table,
        cancellation_token=cancellation_token,
        timeout=timeout,
    )

    ccs = [
        CheckConstraintInfo(
            constraint_name=r["constraint_name"],
            schema_name=str(r["schema_name"]),
            table_name=str(r["table_name"]),
            check_clause=str(r["check_clause"] or ""),
        )
        for r in rows
    ]

    return sorted(ccs, key=lambda c: (c.constraint_name or "", c.check_clause))


async def inspect_indexes(
    conn_mgr: PostgresConnectionManager,
    schema: str | None,
    table: str,
    cancellation_token: CancellationToken | None = None,
    timeout: float | None = None,
) -> list[IndexInfo]:
    """Inspect secondary indexes for a table in deterministic order."""
    rows = await conn_mgr.fetch(
        QUERY_INDEXES,
        schema,
        table,
        cancellation_token=cancellation_token,
        timeout=timeout,
    )

    indexes = []
    for r in rows:
        raw_cols = r["column_names"]
        col_names = [str(c) for c in raw_cols] if isinstance(raw_cols, (list, tuple)) else []

        indexes.append(
            IndexInfo(
                index_name=str(r["index_name"]),
                schema_name=str(r["schema_name"]),
                table_name=str(r["table_name"]),
                column_names=col_names,
                is_unique=bool(r["is_unique"]),
                is_primary=bool(r["is_primary"]),
                index_type=str(r["index_type"]).upper() if r["index_type"] else None,
                predicate=r["predicate"],
            )
        )

    return sorted(indexes, key=lambda i: i.index_name)


async def inspect_views(
    conn_mgr: PostgresConnectionManager,
    schema: str | None = None,
    cancellation_token: CancellationToken | None = None,
    timeout: float | None = None,
) -> list[ViewInfo]:
    """Inspect standard views and materialized views in deterministic order."""
    rows = await conn_mgr.fetch(
        QUERY_VIEWS,
        schema,
        cancellation_token=cancellation_token,
        timeout=timeout,
    )

    views = [
        ViewInfo(
            schema_name=str(r["schema_name"]),
            view_name=str(r["view_name"]),
            is_materialized=bool(r["is_materialized"]),
            view_definition=r["view_definition"],
            comment=r["comment"],
        )
        for r in rows
    ]

    return sorted(views, key=lambda v: (v.schema_name, v.view_name))


async def inspect_sequences(
    conn_mgr: PostgresConnectionManager,
    schema: str | None = None,
    cancellation_token: CancellationToken | None = None,
    timeout: float | None = None,
) -> list[SequenceInfo]:
    """Inspect sequence objects in deterministic order."""
    rows = await conn_mgr.fetch(
        QUERY_SEQUENCES,
        schema,
        cancellation_token=cancellation_token,
        timeout=timeout,
    )

    sequences = [
        SequenceInfo(
            schema_name=str(r["schema_name"]),
            sequence_name=str(r["sequence_name"]),
            data_type=str(r["data_type"] or "bigint"),
            start_value=r["start_value"],
            minimum_value=r["minimum_value"],
            maximum_value=r["maximum_value"],
            increment=int(r["increment"] or 1),
            is_cycling=bool(r["is_cycling"]),
            comment=r["comment"],
        )
        for r in rows
    ]

    return sorted(sequences, key=lambda s: (s.schema_name, s.sequence_name))


async def inspect_partitions(
    conn_mgr: PostgresConnectionManager,
    schema: str | None = None,
    table: str | None = None,
    cancellation_token: CancellationToken | None = None,
    timeout: float | None = None,
) -> list[PartitionInfo]:
    """Inspect table partitioning metadata and parent-child hierarchy."""
    rows = await conn_mgr.fetch(
        QUERY_PARTITIONS,
        schema,
        table,
        cancellation_token=cancellation_token,
        timeout=timeout,
    )

    partitions = []
    for r in rows:
        raw_cols = r["partition_key_columns"]
        col_names = [str(c) for c in raw_cols] if isinstance(raw_cols, (list, tuple)) else []

        partitions.append(
            PartitionInfo(
                schema_name=str(r["schema_name"]),
                table_name=str(r["table_name"]),
                partition_strategy=str(r["partition_strategy"]),
                partition_key_columns=col_names,
                parent_schema=r["parent_schema"],
                parent_table=r["parent_table"],
                partition_bound_expression=r["partition_bound_expression"],
            )
        )

    return sorted(partitions, key=lambda p: (p.schema_name, p.table_name))
