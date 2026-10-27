"""DERA API — Background Jobs & Orchestration Endpoints.

Provides tenant-isolated background job submission, status retrieval,
paginated listing, and cooperative cancellation within workspace boundaries.
"""

from typing import Annotated
import uuid

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from dera_api.auth.dependencies import (
    get_current_user,
    require_workspace_permission_by_id,
    verify_csrf,
)
from dera_api.auth.roles import Permission
from dera_api.contracts.errors import ProblemDetail
from dera_api.db.dependencies import get_db_session
from dera_api.db.models.identity import User
from dera_api.db.models.workspace import Workspace, WorkspaceMembership
from dera_api.db.session import transaction_scope
from dera_api.jobs.enums import JobStatus
from dera_api.jobs.schemas import (
    JobCancelResponse,
    JobCreateRequest,
    JobListResponse,
    JobResponse,
)
from dera_api.jobs.service import JobService

router = APIRouter(prefix="/workspaces/{workspace_id}/jobs", tags=["Jobs"])


@router.post(
    "",
    response_model=JobResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(verify_csrf)],
    summary="Submit a background job within a tenant workspace",
    responses={
        201: {"model": JobResponse, "description": "Job submitted successfully."},
        400: {"model": ProblemDetail, "description": "Invalid job payload or unsupported task type."},
        401: {"model": ProblemDetail, "description": "Authentication required."},
        403: {"model": ProblemDetail, "description": "Insufficient permissions (requires job:create)."},
        404: {"model": ProblemDetail, "description": "Workspace not found or inactive."},
        409: {"model": ProblemDetail, "description": "Idempotency key payload conflict."},
    },
)
async def submit_job(
    request: Request,
    workspace_id: uuid.UUID,
    payload: JobCreateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    _auth: Annotated[
        tuple[Workspace, WorkspaceMembership],
        Depends(require_workspace_permission_by_id(Permission.JOB_CREATE)),
    ],
    db_session: Annotated[AsyncSession, Depends(get_db_session)],
) -> JobResponse:
    """Submit a background job with allowlist validation and outbox dispatch."""
    client_ip = request.client.host if request.client else None
    request_id = getattr(request.state, "request_id", None)

    async with transaction_scope(db_session):
        job_service = JobService(db_session)
        job = await job_service.submit_job(
            workspace_id=workspace_id,
            request=payload,
            user_id=current_user.id,
            request_id=request_id,
            client_ip=client_ip,
        )
        return JobResponse.model_validate(job)


@router.get(
    "",
    response_model=JobListResponse,
    status_code=status.HTTP_200_OK,
    summary="List background jobs within a workspace",
    responses={
        200: {"model": JobListResponse, "description": "Paginated list of jobs."},
        401: {"model": ProblemDetail, "description": "Authentication required."},
        403: {"model": ProblemDetail, "description": "Insufficient permissions (requires job:read)."},
        404: {"model": ProblemDetail, "description": "Workspace not found or inactive."},
    },
)
async def list_jobs(
    workspace_id: uuid.UUID,
    _auth: Annotated[
        tuple[Workspace, WorkspaceMembership],
        Depends(require_workspace_permission_by_id(Permission.JOB_READ)),
    ],
    db_session: Annotated[AsyncSession, Depends(get_db_session)],
    status_filter: Annotated[
        JobStatus | None,
        Query(alias="status", description="Filter by lifecycle state."),
    ] = None,
    job_type: Annotated[
        str | None,
        Query(description="Filter by allowlisted task type identifier."),
    ] = None,
    limit: Annotated[
        int,
        Query(ge=1, le=100, description="Maximum number of items per page."),
    ] = 50,
    offset: Annotated[
        int,
        Query(ge=0, description="Offset for pagination."),
    ] = 0,
) -> JobListResponse:
    """Query workspace background jobs with pagination and optional filters."""
    job_service = JobService(db_session)
    items, total = await job_service.list_jobs(
        workspace_id=workspace_id,
        status=status_filter,
        job_type=job_type,
        limit=limit,
        offset=offset,
    )
    return JobListResponse(
        items=[JobResponse.model_validate(item) for item in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/{job_id}",
    response_model=JobResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve details of a specific background job",
    responses={
        200: {"model": JobResponse, "description": "Job details retrieved successfully."},
        401: {"model": ProblemDetail, "description": "Authentication required."},
        403: {"model": ProblemDetail, "description": "Insufficient permissions (requires job:read)."},
        404: {"model": ProblemDetail, "description": "Job or workspace not found."},
    },
)
async def get_job(
    workspace_id: uuid.UUID,
    job_id: uuid.UUID,
    _auth: Annotated[
        tuple[Workspace, WorkspaceMembership],
        Depends(require_workspace_permission_by_id(Permission.JOB_READ)),
    ],
    db_session: Annotated[AsyncSession, Depends(get_db_session)],
) -> JobResponse:
    """Retrieve authoritative job status and results within workspace boundary."""
    job_service = JobService(db_session)
    job = await job_service.get_job(workspace_id=workspace_id, job_id=job_id)
    return JobResponse.model_validate(job)


@router.post(
    "/{job_id}/cancel",
    response_model=JobCancelResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(verify_csrf)],
    summary="Request cooperative cancellation of a background job",
    responses={
        200: {"model": JobCancelResponse, "description": "Cancellation initiated or completed."},
        401: {"model": ProblemDetail, "description": "Authentication required."},
        403: {"model": ProblemDetail, "description": "Insufficient permissions (requires job:cancel)."},
        404: {"model": ProblemDetail, "description": "Job or workspace not found."},
        409: {"model": ProblemDetail, "description": "Job is already completed."},
    },
)
async def cancel_job(
    request: Request,
    workspace_id: uuid.UUID,
    job_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    _auth: Annotated[
        tuple[Workspace, WorkspaceMembership],
        Depends(require_workspace_permission_by_id(Permission.JOB_CANCEL)),
    ],
    db_session: Annotated[AsyncSession, Depends(get_db_session)],
) -> JobCancelResponse:
    """Cancel a pending, queued, or running background job."""
    client_ip = request.client.host if request.client else None
    request_id = getattr(request.state, "request_id", None)

    async with transaction_scope(db_session):
        job_service = JobService(db_session)
        updated_job, message = await job_service.cancel_job(
            workspace_id=workspace_id,
            job_id=job_id,
            user_id=current_user.id,
            request_id=request_id,
            client_ip=client_ip,
        )
        return JobCancelResponse(
            id=updated_job.id,
            status=JobStatus(updated_job.status),
            message=message,
        )
