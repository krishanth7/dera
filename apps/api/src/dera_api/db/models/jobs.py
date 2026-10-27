"""DERA Database — Job and Outbox Models.

Defines the Job and JobOutboxEvent models for DERA Phase 4.5 Background Workers
and Job Orchestration. Enforces UUID primary keys, workspace isolation,
idempotency constraints, state machine tracking, and transactional outbox guarantees.
"""

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import (
    JSON,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Mapped, mapped_column

from dera_api.db.base import Base


class Job(Base):
    """Authoritative background job state entity."""

    __tablename__ = "dera_jobs"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
        doc="Authoritative unique job identifier (UUIDv4).",
    )
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("dera_workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Tenant workspace boundary owning this job.",
    )
    created_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid,
        ForeignKey("dera_users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        doc="User principal who enqueued the job, or NULL for system tasks.",
    )
    job_type: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        index=True,
        doc="Allowlisted task type name (e.g., system.health_probe.v1).",
    )
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="pending",
        index=True,
        doc="Current state: pending, queued, running, retry_scheduled, succeeded, failed, cancel_requested, cancelled.",
    )
    priority: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="normal",
        doc="Job scheduling priority: low, normal, high, critical.",
    )
    payload: Mapped[dict[str, Any]] = mapped_column(
        JSON().with_variant(postgresql.JSONB, "postgresql"),
        nullable=False,
        default=dict,
        doc="Deterministic input parameters for the registered task.",
    )
    result: Mapped[dict[str, Any] | None] = mapped_column(
        JSON().with_variant(postgresql.JSONB, "postgresql"),
        nullable=True,
        default=None,
        doc="Execution output upon successful completion.",
    )
    error_code: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        doc="Machine-readable error classification code if execution failed.",
    )
    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="Sanitized human-readable error description without secrets.",
    )
    attempt_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        doc="Total number of execution attempts conducted.",
    )
    max_attempts: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=3,
        doc="Maximum execution attempts permitted before terminal failure.",
    )
    idempotency_key: Mapped[str | None] = mapped_column(
        String(128),
        nullable=True,
        index=True,
        doc="Optional client-provided idempotency token scoped to workspace.",
    )
    timeout_seconds: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=300,
        doc="Maximum permitted run time in seconds before timeout abortion.",
    )
    worker_id: Mapped[str | None] = mapped_column(
        String(128),
        nullable=True,
        doc="Identifier of the worker process currently executing the job attempt.",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
        doc="UTC timestamp when the job record was initially created.",
    )
    queued_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="UTC timestamp when the job was dispatched to the broker queue.",
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="UTC timestamp when the worker claimed and started executing the job.",
    )
    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="UTC timestamp when the job reached terminal state (succeeded/failed/cancelled).",
    )
    next_retry_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="Scheduled UTC timestamp for the next retry attempt if retry_scheduled.",
    )

    __table_args__ = (
        UniqueConstraint(
            "workspace_id",
            "idempotency_key",
            name="uq_dera_jobs_workspace_idempotency",
        ),
        Index("ix_dera_jobs_status_created", "status", "created_at"),
        Index("ix_dera_jobs_workspace_status", "workspace_id", "status"),
    )

    def is_terminal(self) -> bool:
        """Returns True if the job has reached an immutable terminal state."""
        return self.status in {"succeeded", "failed", "cancelled"}

    def __repr__(self) -> str:
        return f"<Job(id={self.id}, type={self.job_type}, status={self.status}, attempts={self.attempt_count})>"


class JobOutboxEvent(Base):
    """Transactional outbox event record ensuring reliable broker delivery."""

    __tablename__ = "dera_job_outbox"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
        doc="Authoritative unique outbox event identifier (UUIDv4).",
    )
    job_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("dera_jobs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Target background job entity to dispatch.",
    )
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("dera_workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Tenant workspace owning the job.",
    )
    event_type: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        default="job.queued",
        doc="Outbox message type (e.g. job.queued, job.cancelled).",
    )
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="pending",
        index=True,
        doc="Dispatch status: pending, dispatched, failed.",
    )
    retry_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        doc="Number of dispatch attempts to the queue broker.",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
        doc="UTC timestamp when the outbox record was written.",
    )
    dispatched_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="UTC timestamp when the message was acknowledged by the broker.",
    )

    __table_args__ = (Index("ix_dera_job_outbox_status_created", "status", "created_at"),)

    def __repr__(self) -> str:
        return f"<JobOutboxEvent(id={self.id}, job_id={self.job_id}, status={self.status})>"
