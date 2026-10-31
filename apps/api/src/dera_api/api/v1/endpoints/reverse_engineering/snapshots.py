"""DERA API — Phase 6.6 Snapshot Management & Integrity Endpoints.

Provides creation, listing, retrieval, and cryptographic verification of immutable schema snapshots.
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
    SnapshotCreateRequest,
    SnapshotListResponse,
    SnapshotSummaryResponse,
    SnapshotVerifyResponse,
)

router = APIRouter()


@router.post(
    "/snapshots",
    response_model=SnapshotSummaryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create an immutable schema snapshot",
    responses={
        201: {
            "model": SnapshotSummaryResponse,
            "description": "Snapshot successfully captured and persisted.",
        },
        400: {
            "model": ProblemDetail,
            "description": "Invalid snapshot request or workspace context.",
        },
        401: {"model": ProblemDetail, "description": "Authentication required."},
        403: {
            "model": ProblemDetail,
            "description": "Forbidden / Snapshot create permission denied.",
        },
        404: {
            "model": ProblemDetail,
            "description": "Source schema not found in authorized workspace.",
        },
    },
)
async def create_schema_snapshot(
    payload: SnapshotCreateRequest,
    workspace_id: Annotated[str, Depends(resolve_authorized_workspace_id)],
    service: Annotated[ReverseEngineeringService, Depends(get_re_service)],
) -> SnapshotSummaryResponse:
    """Capture and persist an immutable cryptographic schema snapshot from verified analysis results."""
    snapshot = await service.create_snapshot(
        workspace_id=workspace_id,
        schema_id=payload.schema_id,
        tags=payload.tags,
    )
    if not snapshot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Schema with ID '{payload.schema_id}' was not found in authorized workspace.",
        )

    return SnapshotSummaryResponse(
        snapshot_id=snapshot.snapshot_id,
        fingerprint=snapshot.fingerprint,
        database_id=snapshot.database_id,
        database_name=snapshot.database_name,
        engine=snapshot.engine,
        capture_timestamp=snapshot.capture_timestamp,
        completeness=snapshot.completeness.value,
        table_count=snapshot.metadata_counts.get("table_count", len(snapshot.tables)),
        tags=list(snapshot.tags),
    )


@router.get(
    "/snapshots",
    response_model=SnapshotListResponse,
    status_code=status.HTTP_200_OK,
    summary="List snapshots within authorized workspace",
    responses={
        200: {"model": SnapshotListResponse, "description": "Snapshot catalog retrieved."},
        401: {"model": ProblemDetail, "description": "Authentication required."},
        403: {"model": ProblemDetail, "description": "Forbidden / Access denied."},
    },
)
async def list_schema_snapshots(
    workspace_id: Annotated[str, Depends(resolve_authorized_workspace_id)],
    service: Annotated[ReverseEngineeringService, Depends(get_re_service)],
    database_id: Annotated[str | None, Query(description="Filter by source database ID")] = None,
    fingerprint: Annotated[
        str | None, Query(description="Filter by exact SHA-256 fingerprint")
    ] = None,
    offset: Annotated[int, Query(ge=0, description="Pagination offset")] = 0,
    limit: Annotated[int, Query(ge=1, le=100, description="Page limit")] = 50,
) -> SnapshotListResponse:
    """Retrieve paginated catalog of stored immutable snapshots belonging to authorized workspace."""
    snapshots = await service.list_snapshots(
        workspace_id=workspace_id,
        database_id=database_id,
        fingerprint=fingerprint,
    )

    # Sort stably by capture_timestamp descending, then snapshot_id
    snapshots.sort(key=lambda s: (s.capture_timestamp, s.snapshot_id), reverse=True)
    total_count = len(snapshots)
    paged = snapshots[offset : offset + limit]

    summaries = [
        SnapshotSummaryResponse(
            snapshot_id=s.snapshot_id,
            fingerprint=s.fingerprint,
            database_id=s.database_id,
            database_name=s.database_name,
            engine=s.engine,
            capture_timestamp=s.capture_timestamp,
            completeness=s.completeness.value,
            table_count=s.metadata_counts.get("table_count", len(s.tables)),
            tags=list(s.tags),
        )
        for s in paged
    ]

    return SnapshotListResponse(
        snapshots=summaries,
        total_count=total_count,
    )


@router.get(
    "/snapshots/{snapshot_id}",
    response_model=SnapshotSummaryResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve snapshot metadata",
    responses={
        200: {"model": SnapshotSummaryResponse, "description": "Snapshot details retrieved."},
        401: {"model": ProblemDetail, "description": "Authentication required."},
        403: {"model": ProblemDetail, "description": "Forbidden / Access denied."},
        404: {"model": ProblemDetail, "description": "Snapshot not found in authorized workspace."},
    },
)
async def get_snapshot_detail(
    snapshot_id: str,
    workspace_id: Annotated[str, Depends(resolve_authorized_workspace_id)],
    service: Annotated[ReverseEngineeringService, Depends(get_re_service)],
) -> SnapshotSummaryResponse:
    """Retrieve validated immutable snapshot metadata by identifier."""
    snapshot = await service.get_snapshot(workspace_id, snapshot_id)
    if not snapshot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Snapshot '{snapshot_id}' not found in authorized workspace.",
        )

    return SnapshotSummaryResponse(
        snapshot_id=snapshot.snapshot_id,
        fingerprint=snapshot.fingerprint,
        database_id=snapshot.database_id,
        database_name=snapshot.database_name,
        engine=snapshot.engine,
        capture_timestamp=snapshot.capture_timestamp,
        completeness=snapshot.completeness.value,
        table_count=snapshot.metadata_counts.get("table_count", len(snapshot.tables)),
        tags=list(snapshot.tags),
    )


@router.post(
    "/snapshots/{snapshot_id}/verify",
    response_model=SnapshotVerifyResponse,
    status_code=status.HTTP_200_OK,
    summary="Cryptographically verify snapshot integrity",
    responses={
        200: {"model": SnapshotVerifyResponse, "description": "Snapshot verification outcome."},
        401: {"model": ProblemDetail, "description": "Authentication required."},
        403: {"model": ProblemDetail, "description": "Forbidden / Access denied."},
        404: {"model": ProblemDetail, "description": "Snapshot not found in authorized workspace."},
    },
)
async def verify_snapshot_integrity_endpoint(
    snapshot_id: str,
    workspace_id: Annotated[str, Depends(resolve_authorized_workspace_id)],
    service: Annotated[ReverseEngineeringService, Depends(get_re_service)],
) -> SnapshotVerifyResponse:
    """Recompute deterministic SHA-256 structural fingerprint and report verification status."""
    report = await service.verify_snapshot(workspace_id, snapshot_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Snapshot '{snapshot_id}' not found in authorized workspace.",
        )

    return SnapshotVerifyResponse(
        snapshot_id=report.snapshot_id,
        status=report.status.value,
        is_valid=report.is_valid,
        fingerprint=report.original_fingerprint,
        recomputed_fingerprint=report.recomputed_fingerprint,
        details=report.details,
        findings=list(report.findings),
    )
