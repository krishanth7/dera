"""DERA API — Phase 6.6 Column Detail Endpoint.

Provides granular inspection of individual column attributes and type profiles.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from dera_api.api.v1.endpoints.reverse_engineering.deps import (
    get_re_service,
    resolve_authorized_workspace_id,
)
from dera_api.api.v1.endpoints.reverse_engineering.service import ReverseEngineeringService
from dera_api.contracts.errors import ProblemDetail
from dera_api.schemas.reverse_engineering import ColumnDetailResponse

router = APIRouter()


@router.get(
    "/schemas/{schema_id}/columns/{column_id}",
    response_model=ColumnDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve column metadata by ID",
    responses={
        200: {
            "model": ColumnDetailResponse,
            "description": "Column detail retrieved successfully.",
        },
        401: {"model": ProblemDetail, "description": "Authentication required."},
        403: {"model": ProblemDetail, "description": "Forbidden / Access denied."},
        404: {
            "model": ProblemDetail,
            "description": "Schema or column not found in authorized workspace.",
        },
    },
)
async def get_column_detail(
    schema_id: str,
    column_id: str,
    workspace_id: Annotated[str, Depends(resolve_authorized_workspace_id)],
    service: Annotated[ReverseEngineeringService, Depends(get_re_service)],
) -> ColumnDetailResponse:
    """Retrieve detailed metadata for a column across any table in an authorized schema."""
    schema = service.get_schema(workspace_id, schema_id)
    if not schema:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Schema with ID '{schema_id}' was not found in authorized workspace.",
        )

    # Search tables for column_id
    found_col = None
    parent_table = None
    for t in schema.tables:
        for c in t.columns:
            if c.id == column_id:
                found_col = c
                parent_table = t
                break
        if found_col:
            break

    if not found_col or not parent_table:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Column with ID '{column_id}' was not found in schema '{schema_id}'.",
        )

    is_pk = (
        parent_table.primary_key is not None
        and found_col.name in parent_table.primary_key.column_names
    )

    return ColumnDetailResponse(
        column_id=found_col.id,
        table_id=parent_table.id,
        name=found_col.name,
        ordinal_position=found_col.ordinal_position,
        native_type=getattr(found_col, "native_data_type", getattr(found_col, "native_type", "")),
        canonical_type=str(found_col.canonical_type),
        is_nullable=found_col.is_nullable,
        is_primary_key=is_pk,
        default_expression=getattr(found_col, "default_expression", None),
    )
