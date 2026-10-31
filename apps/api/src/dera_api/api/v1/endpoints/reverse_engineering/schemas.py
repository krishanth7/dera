"""DERA API — Phase 6.6 Schema Endpoints.

Provides schema retrieval and catalog metadata inspection within authorized workspace scope.
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
from dera_api.schemas.reverse_engineering import SchemaSummaryResponse

router = APIRouter()


@router.get(
    "/schemas",
    response_model=list[SchemaSummaryResponse],
    status_code=status.HTTP_200_OK,
    summary="List all schemas in authorized workspace",
    responses={
        200: {"description": "List of schema summaries."},
        400: {"model": ProblemDetail, "description": "Missing workspace context header."},
        401: {"model": ProblemDetail, "description": "Authentication required."},
        403: {"model": ProblemDetail, "description": "Forbidden / Access denied."},
    },
)
async def list_schemas(
    workspace_id: Annotated[str, Depends(resolve_authorized_workspace_id)],
    service: Annotated[ReverseEngineeringService, Depends(get_re_service)],
) -> list[SchemaSummaryResponse]:
    """Retrieve catalog summaries for all schemas registered in an authorized workspace."""
    schemas = service.list_schemas(workspace_id)
    summaries: list[SchemaSummaryResponse] = []
    for schema in schemas:
        db = schema.database
        summaries.append(
            SchemaSummaryResponse(
                schema_id=db.id,
                database_id=db.id,
                database_name=db.name,
                engine=db.engine,
                namespace_count=len(schema.namespaces),
                table_count=len(schema.tables),
                view_count=len(schema.views),
                foreign_key_count=len(schema.foreign_key_references),
                completeness=schema.metadata_completeness.value,
                source_engine=db.provenance.source_engine,
                source_version=db.provenance.source_version,
                connector_version=db.provenance.connector_version,
                collection_timestamp=db.provenance.collection_timestamp,
            )
        )
    return summaries


@router.get(
    "/schemas/{schema_id}",
    response_model=SchemaSummaryResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve canonical schema representation summary",
    responses={
        200: {
            "model": SchemaSummaryResponse,
            "description": "Schema summary retrieved successfully.",
        },
        400: {"model": ProblemDetail, "description": "Missing workspace context header."},
        401: {"model": ProblemDetail, "description": "Authentication required."},
        403: {"model": ProblemDetail, "description": "Forbidden / Access denied."},
        404: {"model": ProblemDetail, "description": "Schema not found in authorized workspace."},
    },
)
async def get_schema_summary(
    schema_id: str,
    workspace_id: Annotated[str, Depends(resolve_authorized_workspace_id)],
    service: Annotated[ReverseEngineeringService, Depends(get_re_service)],
) -> SchemaSummaryResponse:
    """Retrieve high-level catalog summary for an authorized canonical schema."""
    schema = service.get_schema(workspace_id, schema_id)
    if not schema:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Schema with ID '{schema_id}' was not found in authorized workspace.",
        )

    db = schema.database
    return SchemaSummaryResponse(
        schema_id=db.id,
        database_id=db.id,
        database_name=db.name,
        engine=db.engine,
        namespace_count=len(schema.namespaces),
        table_count=len(schema.tables),
        view_count=len(schema.views),
        foreign_key_count=len(schema.foreign_key_references),
        completeness=schema.metadata_completeness.value,
        source_engine=db.provenance.source_engine,
        source_version=db.provenance.source_version,
        connector_version=db.provenance.connector_version,
        collection_timestamp=db.provenance.collection_timestamp,
    )
