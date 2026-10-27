"""jobs_and_orchestration

Revision ID: 003_jobs_and_orchestration
Revises: 002_identity_and_workspaces
Create Date: 2026-10-27 16:00:00.000000+00:00

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "003_jobs_and_orchestration"
down_revision: str | None = "002_identity_and_workspaces"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. dera_jobs
    op.create_table(
        "dera_jobs",
        sa.Column(
            "id",
            sa.Uuid(),
            nullable=False,
            comment="Authoritative unique job identifier (UUIDv4).",
        ),
        sa.Column(
            "workspace_id",
            sa.Uuid(),
            nullable=False,
            comment="Tenant workspace boundary owning this job.",
        ),
        sa.Column(
            "created_by_user_id",
            sa.Uuid(),
            nullable=True,
            comment="User principal who enqueued the job, or NULL for system tasks.",
        ),
        sa.Column(
            "job_type",
            sa.String(length=128),
            nullable=False,
            comment="Allowlisted task type name (e.g., system.health_probe.v1).",
        ),
        sa.Column(
            "status",
            sa.String(length=32),
            server_default="pending",
            nullable=False,
            comment="Current state: pending, queued, running, retry_scheduled, succeeded, failed, cancel_requested, cancelled.",
        ),
        sa.Column(
            "priority",
            sa.String(length=32),
            server_default="normal",
            nullable=False,
            comment="Job scheduling priority: low, normal, high, critical.",
        ),
        sa.Column(
            "payload",
            sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql"),
            server_default="{}",
            nullable=False,
            comment="Deterministic input parameters for the registered task.",
        ),
        sa.Column(
            "result",
            sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql"),
            nullable=True,
            comment="Execution output upon successful completion.",
        ),
        sa.Column(
            "error_code",
            sa.String(length=64),
            nullable=True,
            comment="Machine-readable error classification code if execution failed.",
        ),
        sa.Column(
            "error_message",
            sa.Text(),
            nullable=True,
            comment="Sanitized human-readable error description without secrets.",
        ),
        sa.Column(
            "attempt_count",
            sa.Integer(),
            server_default="0",
            nullable=False,
            comment="Total number of execution attempts conducted.",
        ),
        sa.Column(
            "max_attempts",
            sa.Integer(),
            server_default="3",
            nullable=False,
            comment="Maximum execution attempts permitted before terminal failure.",
        ),
        sa.Column(
            "idempotency_key",
            sa.String(length=128),
            nullable=True,
            comment="Optional client-provided idempotency token scoped to workspace.",
        ),
        sa.Column(
            "timeout_seconds",
            sa.Integer(),
            server_default="300",
            nullable=False,
            comment="Maximum permitted run time in seconds before timeout abortion.",
        ),
        sa.Column(
            "worker_id",
            sa.String(length=128),
            nullable=True,
            comment="Identifier of the worker process currently executing the job attempt.",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
            comment="UTC timestamp when the job record was initially created.",
        ),
        sa.Column(
            "queued_at",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="UTC timestamp when the job was dispatched to the broker queue.",
        ),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="UTC timestamp when the worker claimed and started executing the job.",
        ),
        sa.Column(
            "finished_at",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="UTC timestamp when the job reached terminal state.",
        ),
        sa.Column(
            "next_retry_at",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="Scheduled UTC timestamp for the next retry attempt if retry_scheduled.",
        ),
        sa.ForeignKeyConstraint(
            ["created_by_user_id"],
            ["dera_users.id"],
            name="fk_dera_jobs_created_by_user_id",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["workspace_id"],
            ["dera_workspaces.id"],
            name="fk_dera_jobs_workspace_id",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_dera_jobs"),
        sa.UniqueConstraint(
            "workspace_id",
            "idempotency_key",
            name="uq_dera_jobs_workspace_idempotency",
        ),
    )
    op.create_index(
        "ix_dera_jobs_workspace_id",
        "dera_jobs",
        ["workspace_id"],
        unique=False,
    )
    op.create_index(
        "ix_dera_jobs_status",
        "dera_jobs",
        ["status"],
        unique=False,
    )
    op.create_index(
        "ix_dera_jobs_job_type",
        "dera_jobs",
        ["job_type"],
        unique=False,
    )
    op.create_index(
        "ix_dera_jobs_created_by_user_id",
        "dera_jobs",
        ["created_by_user_id"],
        unique=False,
    )
    op.create_index(
        "ix_dera_jobs_idempotency_key",
        "dera_jobs",
        ["idempotency_key"],
        unique=False,
    )
    op.create_index(
        "ix_dera_jobs_status_created",
        "dera_jobs",
        ["status", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_dera_jobs_workspace_status",
        "dera_jobs",
        ["workspace_id", "status"],
        unique=False,
    )

    # 2. dera_job_outbox
    op.create_table(
        "dera_job_outbox",
        sa.Column(
            "id",
            sa.Uuid(),
            nullable=False,
            comment="Authoritative unique outbox event identifier (UUIDv4).",
        ),
        sa.Column(
            "job_id",
            sa.Uuid(),
            nullable=False,
            comment="Target background job entity to dispatch.",
        ),
        sa.Column(
            "workspace_id",
            sa.Uuid(),
            nullable=False,
            comment="Tenant workspace owning the job.",
        ),
        sa.Column(
            "event_type",
            sa.String(length=64),
            server_default="job.queued",
            nullable=False,
            comment="Outbox message type (e.g. job.queued, job.cancelled).",
        ),
        sa.Column(
            "status",
            sa.String(length=32),
            server_default="pending",
            nullable=False,
            comment="Dispatch status: pending, dispatched, failed.",
        ),
        sa.Column(
            "retry_count",
            sa.Integer(),
            server_default="0",
            nullable=False,
            comment="Number of dispatch attempts to the queue broker.",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
            comment="UTC timestamp when the outbox record was written.",
        ),
        sa.Column(
            "dispatched_at",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="UTC timestamp when the message was acknowledged by the broker.",
        ),
        sa.ForeignKeyConstraint(
            ["job_id"],
            ["dera_jobs.id"],
            name="fk_dera_job_outbox_job_id",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["workspace_id"],
            ["dera_workspaces.id"],
            name="fk_dera_job_outbox_workspace_id",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_dera_job_outbox"),
    )
    op.create_index(
        "ix_dera_job_outbox_job_id",
        "dera_job_outbox",
        ["job_id"],
        unique=False,
    )
    op.create_index(
        "ix_dera_job_outbox_workspace_id",
        "dera_job_outbox",
        ["workspace_id"],
        unique=False,
    )
    op.create_index(
        "ix_dera_job_outbox_status",
        "dera_job_outbox",
        ["status"],
        unique=False,
    )
    op.create_index(
        "ix_dera_job_outbox_status_created",
        "dera_job_outbox",
        ["status", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    # Drop in reverse dependency order
    op.drop_index("ix_dera_job_outbox_status_created", table_name="dera_job_outbox")
    op.drop_index("ix_dera_job_outbox_status", table_name="dera_job_outbox")
    op.drop_index("ix_dera_job_outbox_workspace_id", table_name="dera_job_outbox")
    op.drop_index("ix_dera_job_outbox_job_id", table_name="dera_job_outbox")
    op.drop_table("dera_job_outbox")

    op.drop_index("ix_dera_jobs_workspace_status", table_name="dera_jobs")
    op.drop_index("ix_dera_jobs_status_created", table_name="dera_jobs")
    op.drop_index("ix_dera_jobs_idempotency_key", table_name="dera_jobs")
    op.drop_index("ix_dera_jobs_created_by_user_id", table_name="dera_jobs")
    op.drop_index("ix_dera_jobs_job_type", table_name="dera_jobs")
    op.drop_index("ix_dera_jobs_status", table_name="dera_jobs")
    op.drop_index("ix_dera_jobs_workspace_id", table_name="dera_jobs")
    op.drop_table("dera_jobs")
