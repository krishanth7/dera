"""identity_and_workspaces

Revision ID: 002_identity_and_workspaces
Revises: 001_platform_metadata
Create Date: 2026-10-27 14:00:00.000000+00:00

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "002_identity_and_workspaces"
down_revision: str | None = "001_platform_metadata"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. dera_users
    op.create_table(
        "dera_users",
        sa.Column(
            "id",
            sa.Uuid(),
            nullable=False,
            comment="Authoritative unique user identifier (UUIDv4).",
        ),
        sa.Column(
            "email",
            sa.String(length=255),
            nullable=False,
            comment="Normalized unique user email address.",
        ),
        sa.Column(
            "password_hash",
            sa.String(length=255),
            nullable=False,
            comment="Argon2id password hash string.",
        ),
        sa.Column(
            "status",
            sa.String(length=32),
            server_default="active",
            nullable=False,
            comment="Account state: active, disabled, pending_verification.",
        ),
        sa.Column(
            "email_verified_at",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="UTC timestamp when email verification succeeded.",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
            comment="UTC timestamp when the user account was created.",
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
            comment="UTC timestamp when the user account was last updated.",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_dera_users")),
        sa.UniqueConstraint("email", name=op.f("uq_dera_users_email")),
    )
    op.create_index(
        op.f("ix_dera_users_email"),
        "dera_users",
        ["email"],
        unique=False,
    )

    # 2. dera_user_sessions
    op.create_table(
        "dera_user_sessions",
        sa.Column(
            "id",
            sa.Uuid(),
            nullable=False,
            comment="Authoritative unique session record identifier (UUIDv4).",
        ),
        sa.Column(
            "user_id",
            sa.Uuid(),
            nullable=False,
            comment="Owning user UUID reference.",
        ),
        sa.Column(
            "token_hash",
            sa.String(length=64),
            nullable=False,
            comment="SHA-256 hash of opaque 64-char session secret.",
        ),
        sa.Column(
            "ip_address",
            sa.String(length=45),
            nullable=True,
            comment="Client IP address recorded at session issuance/activity.",
        ),
        sa.Column(
            "user_agent",
            sa.String(length=255),
            nullable=True,
            comment="Truncated client User-Agent header string.",
        ),
        sa.Column(
            "expires_at",
            sa.DateTime(timezone=True),
            nullable=False,
            comment="UTC timestamp when this session expires.",
        ),
        sa.Column(
            "revoked_at",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="UTC timestamp when this session was explicitly revoked.",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
            comment="UTC timestamp when this session was issued.",
        ),
        sa.Column(
            "last_seen_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
            comment="UTC timestamp when this session was last used.",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["dera_users.id"],
            name=op.f("fk_dera_user_sessions_user_id_dera_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_dera_user_sessions")),
        sa.UniqueConstraint("token_hash", name=op.f("uq_dera_user_sessions_token_hash")),
    )
    op.create_index(
        op.f("ix_dera_user_sessions_user_id"),
        "dera_user_sessions",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_dera_user_sessions_token_hash"),
        "dera_user_sessions",
        ["token_hash"],
        unique=False,
    )
    op.create_index(
        op.f("ix_dera_user_sessions_expires_at"),
        "dera_user_sessions",
        ["expires_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_dera_user_sessions_revoked_at"),
        "dera_user_sessions",
        ["revoked_at"],
        unique=False,
    )

    # 3. dera_workspaces
    op.create_table(
        "dera_workspaces",
        sa.Column(
            "id",
            sa.Uuid(),
            nullable=False,
            comment="Authoritative unique workspace identifier (UUIDv4).",
        ),
        sa.Column(
            "name",
            sa.String(length=100),
            nullable=False,
            comment="Human-readable workspace display name.",
        ),
        sa.Column(
            "slug",
            sa.String(length=64),
            nullable=False,
            comment="URL-safe unique workspace identifier slug.",
        ),
        sa.Column(
            "status",
            sa.String(length=32),
            server_default="active",
            nullable=False,
            comment="Workspace state: active, archived, suspended.",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
            comment="UTC timestamp when the workspace was created.",
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
            comment="UTC timestamp when the workspace was last updated.",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_dera_workspaces")),
        sa.UniqueConstraint("slug", name=op.f("uq_dera_workspaces_slug")),
    )
    op.create_index(
        op.f("ix_dera_workspaces_slug"),
        "dera_workspaces",
        ["slug"],
        unique=False,
    )

    # 4. dera_workspace_memberships
    op.create_table(
        "dera_workspace_memberships",
        sa.Column(
            "id",
            sa.Uuid(),
            nullable=False,
            comment="Authoritative unique membership identifier (UUIDv4).",
        ),
        sa.Column(
            "workspace_id",
            sa.Uuid(),
            nullable=False,
            comment="Referenced workspace UUID.",
        ),
        sa.Column(
            "user_id",
            sa.Uuid(),
            nullable=False,
            comment="Referenced member user UUID.",
        ),
        sa.Column(
            "role",
            sa.String(length=32),
            server_default="viewer",
            nullable=False,
            comment="Assigned workspace role: owner, admin, editor, viewer.",
        ),
        sa.Column(
            "status",
            sa.String(length=32),
            server_default="active",
            nullable=False,
            comment="Membership status: active, invited, suspended.",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
            comment="UTC timestamp when this membership was established.",
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
            comment="UTC timestamp when this membership was last modified.",
        ),
        sa.ForeignKeyConstraint(
            ["workspace_id"],
            ["dera_workspaces.id"],
            name=op.f("fk_dera_workspace_memberships_workspace_id_dera_workspaces"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["dera_users.id"],
            name=op.f("fk_dera_workspace_memberships_user_id_dera_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_dera_workspace_memberships")),
        sa.UniqueConstraint(
            "workspace_id",
            "user_id",
            name=op.f("uq_dera_workspace_memberships_workspace_id_user_id"),
        ),
    )
    op.create_index(
        op.f("ix_dera_workspace_memberships_workspace_id"),
        "dera_workspace_memberships",
        ["workspace_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_dera_workspace_memberships_user_id"),
        "dera_workspace_memberships",
        ["user_id"],
        unique=False,
    )

    # 5. dera_security_audit_events
    op.create_table(
        "dera_security_audit_events",
        sa.Column(
            "id",
            sa.Uuid(),
            nullable=False,
            comment="Authoritative unique audit event identifier (UUIDv4).",
        ),
        sa.Column(
            "event_type",
            sa.String(length=64),
            nullable=False,
            comment="Security action category (e.g. auth.login.success, member.role.change).",
        ),
        sa.Column(
            "actor_user_id",
            sa.Uuid(),
            nullable=True,
            comment="User UUID who triggered the event, or None.",
        ),
        sa.Column(
            "workspace_id",
            sa.Uuid(),
            nullable=True,
            comment="Workspace UUID context if event was workspace-scoped.",
        ),
        sa.Column(
            "target_type",
            sa.String(length=64),
            nullable=True,
            comment="Type of affected resource.",
        ),
        sa.Column(
            "target_id",
            sa.String(length=64),
            nullable=True,
            comment="Identifier string of affected resource.",
        ),
        sa.Column(
            "request_id",
            sa.String(length=64),
            nullable=True,
            comment="Correlation request ID from HTTP request header.",
        ),
        sa.Column(
            "ip_address",
            sa.String(length=45),
            nullable=True,
            comment="Client IP address where request originated.",
        ),
        sa.Column(
            "metadata_json",
            sa.Text(),
            nullable=True,
            comment="Sanitized JSON metadata payload.",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
            comment="UTC timestamp when the audit event was recorded.",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_dera_security_audit_events")),
    )
    op.create_index(
        op.f("ix_dera_security_audit_events_event_type"),
        "dera_security_audit_events",
        ["event_type"],
        unique=False,
    )
    op.create_index(
        op.f("ix_dera_security_audit_events_actor_user_id"),
        "dera_security_audit_events",
        ["actor_user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_dera_security_audit_events_workspace_id"),
        "dera_security_audit_events",
        ["workspace_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_dera_security_audit_events_created_at"),
        "dera_security_audit_events",
        ["created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_table("dera_security_audit_events")
    op.drop_table("dera_workspace_memberships")
    op.drop_table("dera_workspaces")
    op.drop_table("dera_user_sessions")
    op.drop_table("dera_users")
