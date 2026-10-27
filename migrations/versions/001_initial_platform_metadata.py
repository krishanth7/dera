"""initial_platform_metadata

Revision ID: 001_platform_metadata
Revises:
Create Date: 2026-10-27 12:00:00.000000+00:00

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "001_platform_metadata"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "dera_platform_metadata",
        sa.Column(
            "key",
            sa.String(length=64),
            nullable=False,
            comment="Unique identifier key for platform metadata entry.",
        ),
        sa.Column(
            "value",
            sa.Text(),
            nullable=False,
            comment="Persisted value string (JSON/text) for the metadata entry.",
        ),
        sa.Column(
            "description",
            sa.String(length=255),
            nullable=True,
            comment="Optional human-readable description of this operational key.",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
            comment="Timestamp in UTC when this record was initially created.",
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
            comment="Timestamp in UTC when this record was last modified.",
        ),
        sa.PrimaryKeyConstraint("key", name=op.f("pk_dera_platform_metadata")),
    )
    op.create_index(
        op.f("ix_dera_platform_metadata_key"),
        "dera_platform_metadata",
        ["key"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_dera_platform_metadata_key"),
        table_name="dera_platform_metadata",
    )
    op.drop_table("dera_platform_metadata")
