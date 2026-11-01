"""DERA Database — Migration Governance Models.

Defines persistent SQLAlchemy models for Migration Reviews, Review Decisions,
and Audit Events. Enforces multi-tenant isolation, unique decision identity,
foreign key relationships, and durable tamper-evident governance state.
"""

from __future__ import annotations

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
from sqlalchemy.orm import Mapped, mapped_column, relationship

from dera_api.db.base import Base


class MigrationReviewRecord(Base):
    """Authoritative durable record for a migration review request."""

    __tablename__ = "dera_migration_reviews"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
        doc="Authoritative unique review identifier (UUIDv4).",
    )
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("dera_workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Tenant workspace boundary owning this review.",
    )
    review_id_str: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        unique=True,
        index=True,
        doc="Canonical domain review ID string (e.g., rev_...).",
    )
    artifact_id: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
        doc="Identifier of the governed SqlMigrationArtifact.",
    )
    artifact_fingerprint: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        doc="SHA-256 fingerprint of the governed SQL artifact.",
    )
    migration_plan_fingerprint: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        doc="SHA-256 fingerprint of the underlying migration plan.",
    )
    risk_report_fingerprint: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        doc="SHA-256 fingerprint of the underlying risk report.",
    )
    target_dialect: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        doc="Target SQL dialect (postgresql, sqlite, mysql, mariadb).",
    )
    requester_id: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        doc="Identifier of the authenticated user who submitted the review.",
    )
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="Human-readable summary title of the migration review.",
    )
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="",
        doc="Optional detailed description or business justification.",
    )
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="SUBMITTED",
        index=True,
        doc="Review lifecycle status (SUBMITTED, UNDER_REVIEW, APPROVED, REJECTED, etc.).",
    )
    policy_version: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="1.0.0",
        doc="Governance policy version enforced.",
    )
    required_approvals: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        doc="Required approval quorum count derived from policy.",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
        doc="UTC timestamp when review was submitted.",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
        doc="UTC timestamp when review status or decisions last changed.",
    )

    # Relationships
    decisions: Mapped[list[MigrationReviewDecisionRecord]] = relationship(
        "MigrationReviewDecisionRecord",
        back_populates="review",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    audit_events: Mapped[list[MigrationAuditEventRecord]] = relationship(
        "MigrationAuditEventRecord",
        back_populates="review",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<MigrationReviewRecord(id={self.id}, review_id='{self.review_id_str}', status='{self.status}')>"


class MigrationReviewDecisionRecord(Base):
    """Immutable persistent record of an individual reviewer's decision."""

    __tablename__ = "dera_migration_review_decisions"
    __table_args__ = (
        UniqueConstraint(
            "review_record_id",
            "reviewer_id",
            name="uq_dera_migration_review_decisions_review_reviewer",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
        doc="Unique decision record identifier.",
    )
    review_record_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("dera_migration_reviews.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Foreign key to owning migration review.",
    )
    decision_id_str: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        unique=True,
        doc="Canonical domain decision ID (e.g., dec_...).",
    )
    reviewer_id: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        doc="Authoritative user ID of the reviewer.",
    )
    reviewer_role: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        doc="Authoritative verified role of reviewer at decision time.",
    )
    decision_type: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        doc="Decision type: APPROVE, REJECT, REQUEST_CHANGES, ABSTAIN.",
    )
    artifact_fingerprint: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        doc="Artifact fingerprint bound to this decision.",
    )
    rationale: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="",
        doc="Reviewer reasoning and justification.",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
        doc="UTC timestamp when decision was recorded.",
    )

    # Relationships
    review: Mapped[MigrationReviewRecord] = relationship(
        "MigrationReviewRecord",
        back_populates="decisions",
    )


class MigrationAuditEventRecord(Base):
    """Immutable append-only audit event record with cryptographic hash chaining."""

    __tablename__ = "dera_migration_audit_events"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
        doc="Unique audit event row ID.",
    )
    review_record_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("dera_migration_reviews.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Foreign key to owning review.",
    )
    event_id_str: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        unique=True,
        doc="Canonical domain event ID (e.g., evt_...).",
    )
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("dera_workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Owning workspace boundary.",
    )
    actor_id: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        doc="Verified actor who triggered the event.",
    )
    event_type: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        doc="Event category (SUBMIT_REVIEW, RECORD_DECISION, EXPORT_ARTIFACT).",
    )
    previous_state: Mapped[str | None] = mapped_column(
        String(32),
        nullable=True,
        doc="Lifecycle state prior to event.",
    )
    new_state: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        doc="Lifecycle state resulting from event.",
    )
    artifact_fingerprint: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        doc="Bound artifact fingerprint.",
    )
    policy_version: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="1.0.0",
        doc="Policy version.",
    )
    payload_json: Mapped[dict[str, Any]] = mapped_column(
        JSON().with_variant(postgresql.JSONB, "postgresql"),
        nullable=False,
        default=dict,
        doc="Sanitized event metadata.",
    )
    previous_event_hash: Mapped[str | None] = mapped_column(
        String(128),
        nullable=True,
        doc="Hash of preceding event in review chain.",
    )
    event_hash: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        doc="SHA-256 cryptographic digest over this event.",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
        doc="UTC timestamp when audit event was recorded.",
    )

    # Relationships
    review: Mapped[MigrationReviewRecord] = relationship(
        "MigrationReviewRecord",
        back_populates="audit_events",
    )
