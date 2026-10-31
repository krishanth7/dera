"""DERA API — Phase 6.6 Constraint Retrieval Endpoints.

Provides query, filtering, and inspection of all schema constraints (PK, FK, Unique, Check).
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
from dera_api.schemas.reverse_engineering import ConstraintListResponse, ConstraintSummaryResponse

router = APIRouter()


@router.get(
    "/schemas/{schema_id}/constraints",
    response_model=ConstraintListResponse,
    status_code=status.HTTP_200_OK,
    summary="List constraints in an authorized schema",
    responses={
        200: {"model": ConstraintListResponse, "description": "Constraints listed successfully."},
        401: {"model": ProblemDetail, "description": "Authentication required."},
        403: {"model": ProblemDetail, "description": "Forbidden / Access denied."},
        404: {"model": ProblemDetail, "description": "Schema not found in authorized workspace."},
    },
)
async def list_schema_constraints(
    schema_id: str,
    workspace_id: Annotated[str, Depends(resolve_authorized_workspace_id)],
    service: Annotated[ReverseEngineeringService, Depends(get_re_service)],
    table_id: Annotated[str | None, Query(description="Filter by table ID")] = None,
    constraint_type: Annotated[
        str | None, Query(description="Filter by type (PRIMARY_KEY, FOREIGN_KEY, UNIQUE, CHECK)")
    ] = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> ConstraintListResponse:
    """Return paginated list of constraints with optional table and type filters."""
    schema = service.get_schema(workspace_id, schema_id)
    if not schema:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Schema with ID '{schema_id}' was not found in authorized workspace.",
        )

    all_constraints: list[ConstraintSummaryResponse] = []

    for t in schema.tables:
        if table_id and t.id != table_id:
            continue

        if t.primary_key:
            if not constraint_type or constraint_type.upper() in {"PRIMARY_KEY", "PRIMARY KEY"}:
                all_constraints.append(
                    ConstraintSummaryResponse(
                        constraint_id=t.primary_key.id,
                        name=t.primary_key.name,
                        constraint_type="PRIMARY_KEY",
                        columns=list(t.primary_key.column_names),
                        raw_expression=None,
                    )
                )

        for uq in t.unique_constraints:
            if not constraint_type or constraint_type.upper() == "UNIQUE":
                all_constraints.append(
                    ConstraintSummaryResponse(
                        constraint_id=uq.id,
                        name=uq.name,
                        constraint_type="UNIQUE",
                        columns=list(uq.column_names),
                        raw_expression=None,
                    )
                )

        for ck in t.check_constraints:
            if not constraint_type or constraint_type.upper() == "CHECK":
                all_constraints.append(
                    ConstraintSummaryResponse(
                        constraint_id=ck.id,
                        name=ck.name,
                        constraint_type="CHECK",
                        columns=list(ck.column_names),
                        raw_expression=ck.expression,
                    )
                )

        for fk in t.foreign_keys:
            if not constraint_type or constraint_type.upper() in {"FOREIGN_KEY", "FOREIGN KEY"}:
                all_constraints.append(
                    ConstraintSummaryResponse(
                        constraint_id=fk.id,
                        name=fk.name,
                        constraint_type="FOREIGN_KEY",
                        columns=list(fk.column_names),
                        raw_expression=None,
                    )
                )

    # Sort deterministically
    sorted_constraints = sorted(
        all_constraints, key=lambda c: (c.constraint_type, c.name, c.constraint_id)
    )
    total_count = len(sorted_constraints)
    page = sorted_constraints[offset : offset + limit]

    return ConstraintListResponse(
        constraints=page,
        total_count=total_count,
    )
