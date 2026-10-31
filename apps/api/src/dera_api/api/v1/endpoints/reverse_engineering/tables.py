"""DERA API — Phase 6.6 Table Listing & Detail Endpoints.

Provides table discovery, filtering, pagination, and comprehensive structural inspection.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from dera_api.api.v1.endpoints.reverse_engineering.deps import (
    get_re_service,
    resolve_authorized_workspace_id,
)
from dera_api.api.v1.endpoints.reverse_engineering.service import ReverseEngineeringService
from dera_api.contracts.errors import ProblemDetail
from dera_api.schemas.reverse_engineering import (
    ColumnDetailResponse,
    ConstraintSummaryResponse,
    ForeignKeySummaryResponse,
    IndexSummaryResponse,
    PrimaryKeyResponse,
    TableDetailResponse,
    TableListResponse,
    TableSummary,
)

router = APIRouter()


@router.get(
    "/schemas/{schema_id}/tables",
    response_model=TableListResponse,
    status_code=status.HTTP_200_OK,
    summary="List tables in an authorized schema",
    responses={
        200: {"model": TableListResponse, "description": "Tables listed successfully."},
        400: {"model": ProblemDetail, "description": "Invalid query parameters."},
        401: {"model": ProblemDetail, "description": "Authentication required."},
        403: {"model": ProblemDetail, "description": "Forbidden / Access denied."},
        404: {"model": ProblemDetail, "description": "Schema not found in authorized workspace."},
    },
)
async def list_schema_tables(
    schema_id: str,
    workspace_id: Annotated[str, Depends(resolve_authorized_workspace_id)],
    service: Annotated[ReverseEngineeringService, Depends(get_re_service)],
    namespace: Annotated[str | None, Query(description="Filter by native namespace name")] = None,
    table_type: Annotated[
        str | None, Query(description="Filter by table type (e.g. TABLE, VIEW)")
    ] = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> TableListResponse:
    """Return paginated list of tables matching optional namespace and table_type filters."""
    schema = service.get_schema(workspace_id, schema_id)
    if not schema:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Schema with ID '{schema_id}' was not found in authorized workspace.",
        )

    tables = list(schema.tables)
    if namespace:
        tables = [
            t for t in tables if getattr(t, "schema_name", getattr(t, "namespace", "")) == namespace
        ]
    if table_type:
        tables = [t for t in tables if str(t.table_type).upper() == table_type.upper()]

    # Sort deterministically
    sorted_tables = sorted(
        tables,
        key=lambda t: (getattr(t, "schema_name", getattr(t, "namespace", "")), t.name),
    )
    total_count = len(sorted_tables)
    page = sorted_tables[offset : offset + limit]

    summaries = [
        TableSummary(
            table_id=t.id,
            namespace=getattr(t, "schema_name", getattr(t, "namespace", "public")),
            name=t.name,
            table_type=str(t.table_type),
            column_count=len(t.columns),
            has_primary_key=t.primary_key is not None,
            foreign_key_count=len(t.foreign_keys),
        )
        for t in page
    ]

    next_cursor = str(offset + limit) if (offset + limit) < total_count else None
    return TableListResponse(
        tables=summaries,
        total_count=total_count,
        next_cursor=next_cursor,
    )


@router.get(
    "/schemas/{schema_id}/tables/{table_id}",
    response_model=TableDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve complete table details",
    responses={
        200: {"model": TableDetailResponse, "description": "Table details retrieved successfully."},
        401: {"model": ProblemDetail, "description": "Authentication required."},
        403: {"model": ProblemDetail, "description": "Forbidden / Access denied."},
        404: {
            "model": ProblemDetail,
            "description": "Schema or table not found in authorized workspace.",
        },
    },
)
async def get_table_detail(
    schema_id: str,
    table_id: str,
    workspace_id: Annotated[str, Depends(resolve_authorized_workspace_id)],
    service: Annotated[ReverseEngineeringService, Depends(get_re_service)],
) -> TableDetailResponse:
    """Return comprehensive metadata for an authorized table including columns, keys, and indexes."""
    schema = service.get_schema(workspace_id, schema_id)
    if not schema:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Schema with ID '{schema_id}' was not found in authorized workspace.",
        )

    table = schema.get_table(table_id)
    if not table:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Table with ID '{table_id}' was not found in schema '{schema_id}'.",
        )

    # Resolve primary key
    pk_resp: PrimaryKeyResponse | None = None
    pk_cols: set[str] = set()
    if table.primary_key is not None:
        pk_cols = set(table.primary_key.column_names)
        pk_resp = PrimaryKeyResponse(
            constraint_id=table.primary_key.id,
            name=table.primary_key.name,
            columns=list(table.primary_key.column_names),
        )

    # Columns
    cols_resp = [
        ColumnDetailResponse(
            column_id=c.id,
            table_id=table.id,
            name=c.name,
            ordinal_position=c.ordinal_position,
            native_type=getattr(c, "native_data_type", getattr(c, "native_type", "")),
            canonical_type=str(c.canonical_type),
            is_nullable=c.is_nullable,
            is_primary_key=c.name in pk_cols,
            default_expression=getattr(c, "default_expression", None),
        )
        for c in sorted(table.columns, key=lambda c: (c.ordinal_position, c.name))
    ]

    # Foreign keys
    fks_resp = [
        ForeignKeySummaryResponse(
            constraint_id=fk.id,
            name=fk.name,
            source_columns=list(fk.column_names),
            referenced_table_id=fk.referenced_table_id,
            referenced_table_name=fk.referenced_table_name,
            referenced_columns=list(fk.referenced_column_names),
            on_delete=str(fk.on_delete) if fk.on_delete else None,
            on_update=str(fk.on_update) if fk.on_update else None,
        )
        for fk in sorted(table.foreign_keys, key=lambda fk: fk.name)
    ]

    # Unique & Check constraints
    uqs_resp = [
        ConstraintSummaryResponse(
            constraint_id=uq.id,
            name=uq.name,
            constraint_type="UNIQUE",
            columns=list(uq.column_names),
            raw_expression=None,
        )
        for uq in sorted(table.unique_constraints, key=lambda uq: uq.name)
    ]

    checks_resp = [
        ConstraintSummaryResponse(
            constraint_id=ck.id,
            name=ck.name,
            constraint_type="CHECK",
            columns=list(ck.column_names),
            raw_expression=ck.expression,
        )
        for ck in sorted(table.check_constraints, key=lambda ck: ck.name)
    ]

    # Indexes
    idxs_resp = [
        IndexSummaryResponse(
            index_id=idx.id,
            name=idx.name,
            is_unique=idx.is_unique,
            is_primary=idx.is_primary,
            columns=[t.name for t in idx.terms if t.name],
        )
        for idx in sorted(table.indexes, key=lambda idx: idx.name)
    ]

    return TableDetailResponse(
        table_id=table.id,
        namespace=getattr(table, "schema_name", getattr(table, "namespace", "public")),
        name=table.name,
        table_type=str(table.table_type),
        columns=cols_resp,
        primary_key=pk_resp,
        foreign_keys=fks_resp,
        unique_constraints=uqs_resp,
        check_constraints=checks_resp,
        indexes=idxs_resp,
    )
