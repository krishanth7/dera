"""DERA Database — Migration Artifacts Persistence Models.

Defines persistent SQLAlchemy models for Schema Comparisons, Risk Assessments,
Migration Plans, Compiled SQL Artifacts, and Export Records.
Enforces multi-tenant isolation, cryptographic fingerprint binding,
and durable survivability across application restarts and multiple worker instances.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    Uuid,
)
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Mapped, mapped_column

from dera_api.db.base import Base


class MigrationComparisonRecord(Base):
    """Authoritative durable record for a schema comparison report."""

    __tablename__ = "dera_migration_comparisons"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
        doc="Authoritative unique comparison record ID.",
    )
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("dera_workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Tenant workspace boundary owning this comparison.",
    )
    report_id_str: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        unique=True,
        index=True,
        doc="Canonical domain comparison report ID string (e.g., rpt_...).",
    )
    baseline_snapshot_id: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
        doc="Baseline snapshot ID.",
    )
    target_snapshot_id: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
        doc="Target snapshot ID.",
    )
    baseline_fingerprint: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        doc="Cryptographic fingerprint of baseline snapshot.",
    )
    target_fingerprint: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        doc="Cryptographic fingerprint of target snapshot.",
    )
    report_fingerprint: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        index=True,
        doc="SHA-256 fingerprint over complete comparison report content.",
    )
    engine: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        doc="Baseline database engine dialect.",
    )
    target_engine: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        doc="Target database engine dialect.",
    )
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        doc="Comparison status (e.g., IDENTICAL, DIFFERENCES_FOUND).",
    )
    report_json: Mapped[dict[str, Any]] = mapped_column(
        JSON().with_variant(postgresql.JSONB, "postgresql"),
        nullable=False,
        default=dict,
        doc="Canonical serialized ComparisonReport payload.",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
        doc="UTC timestamp when comparison was computed.",
    )


class MigrationRiskRecord(Base):
    """Authoritative durable record for a migration risk assessment report."""

    __tablename__ = "dera_migration_risks"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
        doc="Authoritative unique risk record ID.",
    )
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("dera_workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Tenant workspace boundary owning this risk assessment.",
    )
    report_id_str: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        unique=True,
        index=True,
        doc="Canonical domain risk report ID (e.g., risk_...).",
    )
    comparison_report_id: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
        doc="Underlying comparison report ID.",
    )
    comparison_fingerprint: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        doc="Cryptographic fingerprint of source comparison report.",
    )
    report_fingerprint: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        index=True,
        doc="Cryptographic fingerprint of risk report.",
    )
    risk_level: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        doc="Overall risk classification (LOW, MEDIUM, HIGH, CRITICAL).",
    )
    has_breaking_changes: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        doc="Flag indicating presence of breaking schema changes.",
    )
    has_destructive_changes: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        doc="Flag indicating presence of destructive schema changes.",
    )
    report_json: Mapped[dict[str, Any]] = mapped_column(
        JSON().with_variant(postgresql.JSONB, "postgresql"),
        nullable=False,
        default=dict,
        doc="Canonical serialized MigrationRiskReport payload.",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
        doc="UTC timestamp when risk assessment was computed.",
    )


class MigrationPlanRecord(Base):
    """Authoritative durable record for a migration plan."""

    __tablename__ = "dera_migration_plans"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
        doc="Authoritative unique migration plan record ID.",
    )
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("dera_workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Tenant workspace boundary owning this migration plan.",
    )
    plan_id_str: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        unique=True,
        index=True,
        doc="Canonical domain plan ID (e.g., plan_...).",
    )
    risk_report_id: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
        doc="Underlying risk report ID.",
    )
    risk_report_fingerprint: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        doc="Cryptographic fingerprint of source risk report.",
    )
    plan_fingerprint: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        index=True,
        doc="Cryptographic fingerprint of migration plan.",
    )
    operation_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        doc="Number of planned topological operations.",
    )
    requires_manual_approval: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        doc="Flag indicating if plan contains manual review gates.",
    )
    plan_json: Mapped[dict[str, Any]] = mapped_column(
        JSON().with_variant(postgresql.JSONB, "postgresql"),
        nullable=False,
        default=dict,
        doc="Canonical serialized MigrationPlanReport payload.",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
        doc="UTC timestamp when migration plan was created.",
    )


class MigrationSqlArtifactRecord(Base):
    """Authoritative durable record for a compiled SQL migration artifact."""

    __tablename__ = "dera_migration_sql_artifacts"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
        doc="Authoritative unique SQL artifact record ID.",
    )
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("dera_workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Tenant workspace boundary owning this SQL artifact.",
    )
    artifact_id_str: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        unique=True,
        index=True,
        doc="Canonical domain artifact ID (e.g., art_...).",
    )
    plan_id: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
        doc="Underlying migration plan ID.",
    )
    plan_fingerprint: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        doc="Cryptographic fingerprint of source migration plan.",
    )
    target_dialect: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        doc="Target SQL dialect (postgresql, sqlite, mysql, mariadb).",
    )
    artifact_fingerprint: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        index=True,
        doc="SHA-256 fingerprint of compiled SQL artifact.",
    )
    sql_content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc="Complete forward migration SQL script.",
    )
    rollback_sql: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="Complete rollback migration SQL script.",
    )
    artifact_json: Mapped[dict[str, Any]] = mapped_column(
        JSON().with_variant(postgresql.JSONB, "postgresql"),
        nullable=False,
        default=dict,
        doc="Canonical serialized SqlMigrationArtifact payload.",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
        doc="UTC timestamp when SQL artifact was compiled.",
    )


class MigrationExportRecord(Base):
    """Authoritative durable record of an approved SQL migration export."""

    __tablename__ = "dera_migration_exports"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
        doc="Authoritative unique export record ID.",
    )
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("dera_workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Tenant workspace boundary.",
    )
    export_id_str: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        unique=True,
        index=True,
        doc="Canonical domain export ID (e.g., exp_...).",
    )
    review_id: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
        doc="Associated approved review ID.",
    )
    artifact_id: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
        doc="Associated SQL artifact ID.",
    )
    artifact_fingerprint: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        doc="Fingerprint of exported artifact.",
    )
    exported_by: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        doc="User ID of authorized exporter.",
    )
    exported_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
        doc="UTC timestamp of export.",
    )
    package_json: Mapped[dict[str, Any]] = mapped_column(
        JSON().with_variant(postgresql.JSONB, "postgresql"),
        nullable=False,
        default=dict,
        doc="Export package metadata.",
    )
