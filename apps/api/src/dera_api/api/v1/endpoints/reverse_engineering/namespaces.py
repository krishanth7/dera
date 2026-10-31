"""DERA API — Phase 6.6 Namespace Listing Endpoints.

Provides paginated and filtered listing of schema namespaces / schemas.
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
from dera_api.schemas.reverse_engineering import NamespaceListResponse, NamespaceSummary

router = APIRouter()


@router.get(
    "/schemas/{schema_id}/namespaces",
    response_model=NamespaceListResponse,
    status_code=status.HTTP_200_OK,
    summary="List namespaces within an authorized schema",
    responses={
        200: {"model": NamespaceListResponse, "description": "Namespaces listed successfully."},
        400: {"model": ProblemDetail, "description": "Invalid pagination parameters."},
        401: {"model": ProblemDetail, "description": "Authentication required."},
        403: {"model": ProblemDetail, "description": "Forbidden / Access denied."},
        404: {"model": ProblemDetail, "description": "Schema not found in authorized workspace."},
    },
)
async def list_schema_namespaces(
    schema_id: str,
    workspace_id: Annotated[str, Depends(resolve_authorized_workspace_id)],
    service: Annotated[ReverseEngineeringService, Depends(get_re_service)],
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> NamespaceListResponse:
    """Return paginated list of namespaces with table counts."""
    schema = service.get_schema(workspace_id, schema_id)
    if not schema:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Schema with ID '{schema_id}' was not found in authorized workspace.",
        )

    # Sort namespaces deterministically by name
    sorted_ns = sorted(schema.namespaces, key=lambda ns: ns.name)
    total_count = len(sorted_ns)
    page = sorted_ns[offset : offset + limit]

    summaries = [
        NamespaceSummary(
            namespace_id=ns.id,
            name=ns.name,
            table_count=len(ns.tables),
        )
        for ns in page
    ]

    next_cursor = str(offset + limit) if (offset + limit) < total_count else None
    return NamespaceListResponse(
        namespaces=summaries,
        total_count=total_count,
        next_cursor=next_cursor,
    )
