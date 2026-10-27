"""DERA Jobs — Pydantic Schemas and Contracts.

Defines strongly-typed Pydantic v2 data models for job submission, status responses,
cancellation requests, and worker execution contexts.
"""

from datetime import datetime
from typing import Annotated, Any
import uuid

from pydantic import BaseModel, ConfigDict, Field

from dera_api.jobs.enums import JobPriority, JobStatus


class JobCreateRequest(BaseModel):
    """Payload for submitting a background job within a tenant workspace."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    job_type: Annotated[
        str,
        Field(
            min_length=3,
            max_length=128,
            pattern=r"^[a-z0-9][a-z0-9_.-]*[a-z0-9]$",
            description="Allowlisted background task identifier (e.g., system.health_probe.v1).",
            examples=["system.health_probe.v1"],
        ),
    ]
    payload: Annotated[
        dict[str, Any],
        Field(
            default_factory=dict,
            description="Deterministic input parameters for the registered task handler.",
            examples=[{"target": "system"}],
        ),
    ]
    priority: Annotated[
        JobPriority,
        Field(
            default=JobPriority.NORMAL,
            description="Scheduling priority tier.",
        ),
    ]
    idempotency_key: Annotated[
        str | None,
        Field(
            default=None,
            min_length=1,
            max_length=128,
            description="Optional client idempotency token scoped to the workspace.",
            examples=["submission-probe-20261027-001"],
        ),
    ]
    timeout_seconds: Annotated[
        int | None,
        Field(
            default=None,
            ge=1,
            le=3600,
            description="Execution timeout in seconds. Defaults to platform setting if omitted.",
            examples=[300],
        ),
    ]


class JobResponse(BaseModel):
    """Public representation of a background job entity."""

    model_config = ConfigDict(from_attributes=True, frozen=True)

    id: uuid.UUID = Field(..., description="Unique job identifier (UUIDv4).")
    workspace_id: uuid.UUID = Field(..., description="Owning tenant workspace identifier.")
    created_by_user_id: uuid.UUID | None = Field(
        default=None,
        description="User principal who enqueued the job, or NULL for system actions.",
    )
    job_type: str = Field(..., description="Allowlisted task type name.")
    status: JobStatus = Field(..., description="Current job lifecycle status.")
    priority: JobPriority = Field(..., description="Scheduling priority tier.")
    payload: dict[str, Any] = Field(default_factory=dict, description="Job input payload.")
    result: dict[str, Any] | None = Field(
        default=None,
        description="Structured execution output upon success.",
    )
    error_code: str | None = Field(
        default=None,
        description="Error classification code if execution failed.",
    )
    error_message: str | None = Field(
        default=None,
        description="Sanitized error description without sensitive credentials.",
    )
    attempt_count: int = Field(..., description="Total execution attempts conducted.")
    max_attempts: int = Field(..., description="Maximum permitted execution attempts.")
    idempotency_key: str | None = Field(
        default=None,
        description="Client-provided idempotency token if supplied.",
    )
    timeout_seconds: int = Field(..., description="Configured execution deadline in seconds.")
    worker_id: str | None = Field(
        default=None,
        description="Identifier of worker executing the current attempt.",
    )
    created_at: datetime = Field(..., description="UTC creation timestamp.")
    queued_at: datetime | None = Field(default=None, description="UTC queue dispatch timestamp.")
    started_at: datetime | None = Field(default=None, description="UTC worker start timestamp.")
    finished_at: datetime | None = Field(default=None, description="UTC terminal state timestamp.")
    next_retry_at: datetime | None = Field(
        default=None,
        description="UTC scheduled retry timestamp if status is retry_scheduled.",
    )


class JobListResponse(BaseModel):
    """Paginated collection of workspace background jobs."""

    model_config = ConfigDict(frozen=True)

    items: list[JobResponse] = Field(..., description="List of jobs matching query parameters.")
    total: int = Field(..., ge=0, description="Total matching job count in workspace.")
    limit: int = Field(..., ge=1, le=100, description="Applied page limit.")
    offset: int = Field(..., ge=0, description="Applied pagination offset.")


class JobCancelResponse(BaseModel):
    """Result of requesting job cancellation."""

    model_config = ConfigDict(frozen=True)

    id: uuid.UUID = Field(..., description="Unique job identifier.")
    status: JobStatus = Field(..., description="Updated job status after cancellation request.")
    message: str = Field(..., description="Human-readable cancellation status message.")


class JobExecutionContext(BaseModel):
    """Internal strongly-typed context passed to registered task handlers."""

    model_config = ConfigDict(frozen=True)

    job_id: uuid.UUID = Field(..., description="Job identifier.")
    workspace_id: uuid.UUID = Field(..., description="Tenant workspace boundary.")
    job_type: str = Field(..., description="Task type being executed.")
    attempt_number: int = Field(..., ge=1, description="1-indexed attempt number.")
    timeout_seconds: int = Field(..., description="Execution deadline in seconds.")
    worker_id: str = Field(..., description="Executing worker process identifier.")
    correlation_id: str | None = Field(default=None, description="Audit/trace correlation ID.")


class JobExecutionResult(BaseModel):
    """Result returned by a registered task handler upon success."""

    model_config = ConfigDict(frozen=True)

    output: dict[str, Any] = Field(
        default_factory=dict,
        description="Deterministic output dictionary to persist.",
    )
