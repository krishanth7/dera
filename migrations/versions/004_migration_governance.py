"""migration_governance_persistence

Revision ID: 004_migration_governance
Revises: 003_jobs_and_orchestration
Create Date: 2026-11-01 12:00:00.000000+00:00

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "004_migration_governance"
down_revision: str | None = "003_jobs_and_orchestration"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. dera_migration_reviews
    op.create_table(
        "dera_migration_reviews",
        sa.Column("id", sa.Uuid(), nullable=False, comment="Internal primary key UUID."),
        sa.Column(
            "review_id",
            sa.String(length=128),
            nullable=False,
            comment="Domain review identifier.",
        ),
        sa.Column(
            "workspace_id",
            sa.Uuid(),
            nullable=False,
            comment="Foreign key to workspace context.",
        ),
        sa.Column(
            "artifact_id",
            sa.String(length=128),
            nullable=False,
            comment="Identifier of bound SQL artifact.",
        ),
        sa.Column(
            "artifact_fingerprint",
            sa.String(length=64),
            nullable=False,
            comment="SHA-256 fingerprint of approved artifact.",
        ),
        sa.Column(
            "risk_report_fingerprint",
            sa.String(length=64),
            nullable=False,
            comment="SHA-256 fingerprint of source risk assessment.",
        ),
        sa.Column(
            "requester_id",
            sa.String(length=128),
            nullable=False,
            comment="Authenticated user ID who requested review.",
        ),
        sa.Column(
            "status",
            sa.String(length=32),
            server_default="SUBMITTED",
            nullable=False,
            comment="Review lifecycle status.",
        ),
        sa.Column(
            "title",
            sa.String(length=256),
            nullable=False,
            comment="Review title or reference.",
        ),
        sa.Column(
            "description",
            sa.Text(),
            server_default="",
            nullable=False,
            comment="Migration rationale and context.",
        ),
        sa.Column(
            "required_approvals",
            sa.Integer(),
            server_default="1",
            nullable=False,
            comment="Required approvals quorum from policy.",
        ),
        sa.Column(
            "policy_version",
            sa.String(length=32),
            server_default="v1.0",
            nullable=False,
            comment="Version of governance policy.",
        ),
        sa.Column(
            "is_invalidated",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
            comment="True if artifact changes invalidated approvals.",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["workspace_id"],
            ["dera_workspaces.id"],
            name=op.f("fk_dera_migration_reviews_workspace_id_dera_workspaces"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_dera_migration_reviews")),
        sa.UniqueConstraint("review_id", name=op.f("uq_dera_migration_reviews_review_id")),
    )
    op.create_index(
        op.f("ix_dera_migration_reviews_workspace_id"),
        "dera_migration_reviews",
        ["workspace_id"],
        unique=False,
    )

    # 2. dera_migration_review_decisions
    op.create_table(
        "dera_migration_review_decisions",
        sa.Column("id", sa.Uuid(), nullable=False, comment="Internal primary key UUID."),
        sa.Column(
            "review_record_id",
            sa.Uuid(),
            nullable=False,
            comment="FK to dera_migration_reviews.id.",
        ),
        sa.Column(
            "reviewer_id",
            sa.String(length=128),
            nullable=False,
            comment="Server-authenticated reviewer identity.",
        ),
        sa.Column(
            "reviewer_role",
            sa.String(length=64),
            nullable=False,
            comment="Authoritative workspace role.",
        ),
        sa.Column(
            "decision_type",
            sa.String(length=32),
            nullable=False,
            comment="APPROVE, REJECT, REQUEST_CHANGES, ABSTAIN.",
        ),
        sa.Column(
            "rationale",
            sa.Text(),
            nullable=False,
            comment="Technical justification for decision.",
        ),
        sa.Column(
            "decided_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["review_record_id"],
            ["dera_migration_reviews.id"],
            name=op.f("fk_dera_migration_review_decisions_review_record_id_dera_migration_reviews"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_dera_migration_review_decisions")),
        sa.UniqueConstraint(
            "review_record_id",
            "reviewer_id",
            name="uq_migration_review_decision_reviewer",
        ),
    )
    op.create_index(
        op.f("ix_dera_migration_review_decisions_review_record_id"),
        "dera_migration_review_decisions",
        ["review_record_id"],
        unique=False,
    )

    # 3. dera_migration_audit_events
    op.create_table(
        "dera_migration_audit_events",
        sa.Column("id", sa.Uuid(), nullable=False, comment="Internal primary key UUID."),
        sa.Column(
            "review_record_id",
            sa.Uuid(),
            nullable=False,
            comment="FK to dera_migration_reviews.id.",
        ),
        sa.Column(
            "workspace_id",
            sa.Uuid(),
            nullable=False,
            comment="Workspace owning this audit entry.",
        ),
        sa.Column(
            "event_id",
            sa.String(length=128),
            nullable=False,
            comment="Domain event identifier.",
        ),
        sa.Column(
            "actor_id",
            sa.String(length=128),
            nullable=False,
            comment="Identity of actor performing action.",
        ),
        sa.Column(
            "event_type",
            sa.String(length=64),
            nullable=False,
            comment="Audit event type.",
        ),
        sa.Column(
            "previous_state",
            sa.String(length=32),
            nullable=True,
            comment="Lifecycle status prior to event.",
        ),
        sa.Column(
            "new_state",
            sa.String(length=32),
            nullable=False,
            comment="Lifecycle status after event.",
        ),
        sa.Column(
            "timestamp",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "event_hash",
            sa.String(length=64),
            nullable=False,
            comment="Cryptographic SHA-256 event hash.",
        ),
        sa.Column(
            "payload_json",
            sa.Text(),
            nullable=True,
            comment="Serialized event payload.",
        ),
        sa.ForeignKeyConstraint(
            ["review_record_id"],
            ["dera_migration_reviews.id"],
            name=op.f("fk_dera_migration_audit_events_review_record_id_dera_migration_reviews"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["workspace_id"],
            ["dera_workspaces.id"],
            name=op.f("fk_dera_migration_audit_events_workspace_id_dera_workspaces"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_dera_migration_audit_events")),
    )
    op.create_index(
        op.f("ix_dera_migration_audit_events_review_record_id"),
        "dera_migration_audit_events",
        ["review_record_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_dera_migration_audit_events_workspace_id"),
        "dera_migration_audit_events",
        ["workspace_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_table("dera_migration_audit_events")
    op.drop_table("dera_migration_review_decisions")
    op.drop_table("dera_migration_reviews")
