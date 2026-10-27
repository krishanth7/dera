"""DERA Database — Workspace and Membership Models.

Defines the Workspace and WorkspaceMembership models for DERA Phase 4.4.
Enforces multi-tenant workspace isolation, unique membership constraints,
and role assignments (owner, admin, editor, viewer).
"""

import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from dera_api.db.base import Base

if TYPE_CHECKING:
    from dera_api.db.models.identity import User


class Workspace(Base):
    """Multi-tenant workspace boundary entity."""

    __tablename__ = "dera_workspaces"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
        doc="Authoritative unique workspace identifier (UUIDv4).",
    )
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        doc="Human-readable workspace display name.",
    )
    slug: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        index=True,
        nullable=False,
        doc="URL-safe unique workspace identifier slug.",
    )
    status: Mapped[str] = mapped_column(
        String(32),
        default="active",
        nullable=False,
        doc="Workspace state: active, archived, suspended.",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
        doc="UTC timestamp when the workspace was created.",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
        doc="UTC timestamp when the workspace was last updated.",
    )

    # Relationships
    memberships: Mapped[list["WorkspaceMembership"]] = relationship(
        "WorkspaceMembership",
        back_populates="workspace",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Workspace(id={self.id}, slug='{self.slug}', status='{self.status}')>"


class WorkspaceMembership(Base):
    """User membership and role assignment within a workspace."""

    __tablename__ = "dera_workspace_memberships"
    __table_args__ = (
        UniqueConstraint(
            "workspace_id",
            "user_id",
            name="uq_dera_workspace_memberships_workspace_id_user_id",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
        doc="Authoritative unique membership identifier (UUIDv4).",
    )
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("dera_workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Referenced workspace UUID.",
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("dera_users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Referenced member user UUID.",
    )
    role: Mapped[str] = mapped_column(
        String(32),
        default="viewer",
        nullable=False,
        doc="Assigned workspace role: owner, admin, editor, viewer.",
    )
    status: Mapped[str] = mapped_column(
        String(32),
        default="active",
        nullable=False,
        doc="Membership status: active, invited, suspended.",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
        doc="UTC timestamp when this membership was established.",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
        doc="UTC timestamp when this membership was last modified.",
    )

    # Relationships
    workspace: Mapped["Workspace"] = relationship(
        "Workspace",
        back_populates="memberships",
        lazy="joined",
    )
    user: Mapped["User"] = relationship(
        "User",
        back_populates="memberships",
        lazy="joined",
    )

    def __repr__(self) -> str:
        return f"<WorkspaceMembership(workspace={self.workspace_id}, user={self.user_id}, role='{self.role}')>"
