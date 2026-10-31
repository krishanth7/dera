"""DERA API — Phase 6.6 Deterministic Export Endpoints.

Provides initiation, job status tracking, and authorized download of deterministic export artifacts
(JSON, CSV, GraphML, DOT, Snapshot) with formula injection protection and resource limits.
"""

from __future__ import annotations

import re
from typing import Annotated

from dera.reverse_engineering.exports.errors import (
    ExportError,
    ExportResourceLimitError,
    ExportSecurityError,
    ExportValidationError,
    UnsupportedExportFormatError,
)
from dera.reverse_engineering.exports.limits import DEFAULT_EXPORT_LIMITS
from dera.reverse_engineering.exports.models import ExportOptions
from dera.reverse_engineering.exports.validation import validate_export_options
from fastapi import APIRouter, Depends, HTTPException, Response, status

from dera_api.api.v1.endpoints.reverse_engineering.deps import (
    get_re_service,
    resolve_authorized_workspace_id,
)
from dera_api.api.v1.endpoints.reverse_engineering.service import ReverseEngineeringService
from dera_api.contracts.errors import ProblemDetail
from dera_api.schemas.reverse_engineering import ExportCreateRequest, ExportJobResponse

router = APIRouter()


def _sanitize_filename(name: str) -> str:
    """Ensure download filename contains only safe ASCII characters without path traversal."""
    cleaned = re.sub(r"[^a-zA-Z0-9_\-\.]", "_", name)
    return cleaned.strip("._") or "export_artifact"


@router.post(
    "/exports",
    response_model=ExportJobResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a deterministic export artifact",
    responses={
        201: {
            "model": ExportJobResponse,
            "description": "Export job initiated and artifact prepared.",
        },
        400: {"model": ProblemDetail, "description": "Invalid export options or validation error."},
        401: {"model": ProblemDetail, "description": "Authentication required."},
        403: {
            "model": ProblemDetail,
            "description": "Forbidden / Export create permission denied.",
        },
        404: {"model": ProblemDetail, "description": "Target schema or resource not found."},
        413: {"model": ProblemDetail, "description": "Export resource limits exceeded."},
        422: {"model": ProblemDetail, "description": "Unsupported export format or scope."},
    },
)
async def create_export_artifact(
    payload: ExportCreateRequest,
    workspace_id: Annotated[str, Depends(resolve_authorized_workspace_id)],
    service: Annotated[ReverseEngineeringService, Depends(get_re_service)],
) -> ExportJobResponse:
    """Initiate and generate a deterministic structural export artifact."""
    if not payload.schema_id and not payload.snapshot_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either 'schema_id' or 'snapshot_id' must be provided for export generation.",
        )

    options = ExportOptions(
        format=payload.format,
        scope=payload.scope,
        target_id=payload.target_id,
        safe_mode=payload.safe_mode,
        pretty_print=payload.pretty_print,
    )

    try:
        validate_export_options(options, DEFAULT_EXPORT_LIMITS)
    except ExportValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Export validation failed: {exc}",
        ) from exc
    except UnsupportedExportFormatError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unsupported export format: {exc}",
        ) from exc

    # Verify target existence within workspace
    if payload.schema_id:
        schema = service.get_schema(workspace_id, payload.schema_id)
        if not schema:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Schema '{payload.schema_id}' was not found in authorized workspace.",
            )

    try:
        export_id, artifact = service.create_export(
            workspace_id=workspace_id,
            options=options,
            schema_id=payload.schema_id,
            snapshot_id=payload.snapshot_id,
        )
    except ExportResourceLimitError as exc:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Export resource limit exceeded: {exc}",
        ) from exc
    except ExportSecurityError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Export security validation failed: {exc}",
        ) from exc
    except ExportError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate export artifact: {exc}",
        ) from exc

    job = service.get_export_job(workspace_id, export_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Export job tracking failed.",
        )

    return ExportJobResponse(
        export_id=job["export_id"],
        job_id=job["job_id"],
        status=job["status"],
        format=job["format"],
        scope=job["scope"],
        created_at=job["created_at"],
        completed_at=job["completed_at"],
        error_message=job["error_message"],
        download_url=f"/api/v1/reverse-engineering/exports/{export_id}/download",
    )


@router.get(
    "/exports/{export_id}",
    response_model=ExportJobResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve export job status",
    responses={
        200: {"model": ExportJobResponse, "description": "Export job status retrieved."},
        401: {"model": ProblemDetail, "description": "Authentication required."},
        403: {"model": ProblemDetail, "description": "Forbidden / Access denied."},
        404: {
            "model": ProblemDetail,
            "description": "Export job not found in authorized workspace.",
        },
    },
)
async def get_export_status(
    export_id: str,
    workspace_id: Annotated[str, Depends(resolve_authorized_workspace_id)],
    service: Annotated[ReverseEngineeringService, Depends(get_re_service)],
) -> ExportJobResponse:
    """Retrieve status and metadata of an authorized export job."""
    job = service.get_export_job(workspace_id, export_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Export job '{export_id}' not found in authorized workspace.",
        )

    return ExportJobResponse(
        export_id=job["export_id"],
        job_id=job["job_id"],
        status=job["status"],
        format=job["format"],
        scope=job["scope"],
        created_at=job["created_at"],
        completed_at=job["completed_at"],
        error_message=job["error_message"],
        download_url=f"/api/v1/reverse-engineering/exports/{export_id}/download",
    )


@router.get(
    "/exports/{export_id}/download",
    status_code=status.HTTP_200_OK,
    summary="Download deterministic export artifact",
    responses={
        200: {"description": "Binary or text export artifact stream."},
        401: {"model": ProblemDetail, "description": "Authentication required."},
        403: {"model": ProblemDetail, "description": "Forbidden / Access denied."},
        404: {
            "model": ProblemDetail,
            "description": "Export artifact not found in authorized workspace.",
        },
    },
)
async def download_export_artifact(
    export_id: str,
    workspace_id: Annotated[str, Depends(resolve_authorized_workspace_id)],
    service: Annotated[ReverseEngineeringService, Depends(get_re_service)],
) -> Response:
    """Download export artifact with verified MIME type, SHA-256 ETag, and safe filename headers."""
    artifact = service.get_export_artifact(workspace_id, export_id)
    if not artifact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Export artifact '{export_id}' not found in authorized workspace.",
        )

    safe_filename = _sanitize_filename(artifact.filename)
    headers = {
        "Content-Disposition": f'attachment; filename="{safe_filename}"',
        "ETag": f'"{artifact.sha256_digest}"',
        "X-Content-Type-Options": "nosniff",
        "X-Artifact-Size": str(artifact.size_bytes),
    }

    return Response(
        content=artifact.content,
        media_type=artifact.media_type,
        headers=headers,
    )
