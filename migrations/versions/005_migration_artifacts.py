"""migration_artifacts_persistence

Revision ID: 005_migration_artifacts
Revises: 004_migration_governance
Create Date: 2026-11-01 16:00:00.000000+00:00

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "005_migration_artifacts"
down_revision: str | None = "004_migration_governance"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. dera_migration_comparisons
    op.create_table(
        "dera_migration_comparisons",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("report_id_str", sa.String(length=64), nullable=False),
        sa.Column("baseline_snapshot_id", sa.String(length=64), nullable=False),
        sa.Column("target_snapshot_id", sa.String(length=64), nullable=False),
        sa.Column("baseline_fingerprint", sa.String(length=128), nullable=False),
        sa.Column("target_fingerprint", sa.String(length=128), nullable=False),
        sa.Column("report_fingerprint", sa.String(length=128), nullable=False),
        sa.Column("engine", sa.String(length=32), nullable=False),
        sa.Column("target_engine", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("report_json", sa.JSON().with_variant(postgresql.JSONB, "postgresql"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["workspace_id"],
            ["dera_workspaces.id"],
            name=op.f("fk_dera_migration_comparisons_workspace_id_dera_workspaces"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_dera_migration_comparisons")),
        sa.UniqueConstraint("report_id_str", name=op.f("uq_dera_migration_comparisons_report_id_str")),
    )
    op.create_index(
        op.f("ix_dera_migration_comparisons_workspace_id"),
        "dera_migration_comparisons",
        ["workspace_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_dera_migration_comparisons_report_id_str"),
        "dera_migration_comparisons",
        ["report_id_str"],
        unique=True,
    )
    op.create_index(
        op.f("ix_dera_migration_comparisons_report_fingerprint"),
        "dera_migration_comparisons",
        ["report_fingerprint"],
        unique=False,
    )
    op.create_index(
        op.f("ix_dera_migration_comparisons_baseline_snapshot_id"),
        "dera_migration_comparisons",
        ["baseline_snapshot_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_dera_migration_comparisons_target_snapshot_id"),
        "dera_migration_comparisons",
        ["target_snapshot_id"],
        unique=False,
    )

    # 2. dera_migration_risks
    op.create_table(
        "dera_migration_risks",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("report_id_str", sa.String(length=64), nullable=False),
        sa.Column("comparison_report_id", sa.String(length=64), nullable=False),
        sa.Column("comparison_fingerprint", sa.String(length=128), nullable=False),
        sa.Column("report_fingerprint", sa.String(length=128), nullable=False),
        sa.Column("risk_level", sa.String(length=32), nullable=False),
        sa.Column("has_breaking_changes", sa.Boolean(), nullable=False),
        sa.Column("has_destructive_changes", sa.Boolean(), nullable=False),
        sa.Column("report_json", sa.JSON().with_variant(postgresql.JSONB, "postgresql"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["workspace_id"],
            ["dera_workspaces.id"],
            name=op.f("fk_dera_migration_risks_workspace_id_dera_workspaces"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_dera_migration_risks")),
        sa.UniqueConstraint("report_id_str", name=op.f("uq_dera_migration_risks_report_id_str")),
    )
    op.create_index(
        op.f("ix_dera_migration_risks_workspace_id"),
        "dera_migration_risks",
        ["workspace_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_dera_migration_risks_report_id_str"),
        "dera_migration_risks",
        ["report_id_str"],
        unique=True,
    )
    op.create_index(
        op.f("ix_dera_migration_risks_report_fingerprint"),
        "dera_migration_risks",
        ["report_fingerprint"],
        unique=False,
    )
    op.create_index(
        op.f("ix_dera_migration_risks_comparison_report_id"),
        "dera_migration_risks",
        ["comparison_report_id"],
        unique=False,
    )

    # 3. dera_migration_plans
    op.create_table(
        "dera_migration_plans",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("plan_id_str", sa.String(length=64), nullable=False),
        sa.Column("risk_report_id", sa.String(length=64), nullable=False),
        sa.Column("risk_report_fingerprint", sa.String(length=128), nullable=False),
        sa.Column("plan_fingerprint", sa.String(length=128), nullable=False),
        sa.Column("operation_count", sa.Integer(), nullable=False),
        sa.Column("requires_manual_approval", sa.Boolean(), nullable=False),
        sa.Column("plan_json", sa.JSON().with_variant(postgresql.JSONB, "postgresql"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["workspace_id"],
            ["dera_workspaces.id"],
            name=op.f("fk_dera_migration_plans_workspace_id_dera_workspaces"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_dera_migration_plans")),
        sa.UniqueConstraint("plan_id_str", name=op.f("uq_dera_migration_plans_plan_id_str")),
    )
    op.create_index(
        op.f("ix_dera_migration_plans_workspace_id"),
        "dera_migration_plans",
        ["workspace_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_dera_migration_plans_plan_id_str"),
        "dera_migration_plans",
        ["plan_id_str"],
        unique=True,
    )
    op.create_index(
        op.f("ix_dera_migration_plans_plan_fingerprint"),
        "dera_migration_plans",
        ["plan_fingerprint"],
        unique=False,
    )
    op.create_index(
        op.f("ix_dera_migration_plans_risk_report_id"),
        "dera_migration_plans",
        ["risk_report_id"],
        unique=False,
    )

    # 4. dera_migration_sql_artifacts
    op.create_table(
        "dera_migration_sql_artifacts",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("artifact_id_str", sa.String(length=64), nullable=False),
        sa.Column("plan_id", sa.String(length=64), nullable=False),
        sa.Column("plan_fingerprint", sa.String(length=128), nullable=False),
        sa.Column("target_dialect", sa.String(length=32), nullable=False),
        sa.Column("artifact_fingerprint", sa.String(length=128), nullable=False),
        sa.Column("sql_content", sa.Text(), nullable=False),
        sa.Column("rollback_sql", sa.Text(), nullable=True),
        sa.Column("artifact_json", sa.JSON().with_variant(postgresql.JSONB, "postgresql"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["workspace_id"],
            ["dera_workspaces.id"],
            name=op.f("fk_dera_migration_sql_artifacts_workspace_id_dera_workspaces"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_dera_migration_sql_artifacts")),
        sa.UniqueConstraint("artifact_id_str", name=op.f("uq_dera_migration_sql_artifacts_artifact_id_str")),
    )
    op.create_index(
        op.f("ix_dera_migration_sql_artifacts_workspace_id"),
        "dera_migration_sql_artifacts",
        ["workspace_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_dera_migration_sql_artifacts_artifact_id_str"),
        "dera_migration_sql_artifacts",
        ["artifact_id_str"],
        unique=True,
    )
    op.create_index(
        op.f("ix_dera_migration_sql_artifacts_artifact_fingerprint"),
        "dera_migration_sql_artifacts",
        ["artifact_fingerprint"],
        unique=False,
    )
    op.create_index(
        op.f("ix_dera_migration_sql_artifacts_plan_id"),
        "dera_migration_sql_artifacts",
        ["plan_id"],
        unique=False,
    )

    # 5. dera_migration_exports
    op.create_table(
        "dera_migration_exports",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("export_id_str", sa.String(length=64), nullable=False),
        sa.Column("review_id", sa.String(length=64), nullable=False),
        sa.Column("artifact_id", sa.String(length=64), nullable=False),
        sa.Column("artifact_fingerprint", sa.String(length=128), nullable=False),
        sa.Column("exported_by", sa.String(length=64), nullable=False),
        sa.Column("exported_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("package_json", sa.JSON().with_variant(postgresql.JSONB, "postgresql"), nullable=False),
        sa.ForeignKeyConstraint(
            ["workspace_id"],
            ["dera_workspaces.id"],
            name=op.f("fk_dera_migration_exports_workspace_id_dera_workspaces"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_dera_migration_exports")),
        sa.UniqueConstraint("export_id_str", name=op.f("uq_dera_migration_exports_export_id_str")),
    )
    op.create_index(
        op.f("ix_dera_migration_exports_workspace_id"),
        "dera_migration_exports",
        ["workspace_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_dera_migration_exports_export_id_str"),
        "dera_migration_exports",
        ["export_id_str"],
        unique=True,
    )
    op.create_index(
        op.f("ix_dera_migration_exports_review_id"),
        "dera_migration_exports",
        ["review_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_dera_migration_exports_artifact_id"),
        "dera_migration_exports",
        ["artifact_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_table("dera_migration_exports")
    op.drop_table("dera_migration_sql_artifacts")
    op.drop_table("dera_migration_plans")
    op.drop_table("dera_migration_risks")
    op.drop_table("dera_migration_comparisons")
