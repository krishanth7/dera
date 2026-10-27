"""DERA Database — Security Audit Event Model.

Defines the SecurityAuditEvent model for DERA Phase 4.4.
Enforces immutable audit event recording for authentication, authorization,
and workspace administration actions with non-sensitive metadata.
"""

import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from dera_api.db.base import Base


class SecurityAuditEvent(Base):
    """Immutable security-relevant operational audit log entry."""

    __tablename__ = "dera_security_audit_events"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
        doc="Authoritative unique audit event identifier (UUIDv4).",
    )
    event_type: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
        doc="Security action category (e.g., auth.login.success, auth.login.failure, member.role.change).",
    )
    actor_user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid,
        nullable=True,
        index=True,
        doc="User UUID who triggered the event, or None for unauthenticated actions.",
    )
    workspace_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid,
        nullable=True,
        index=True,
        doc="Workspace UUID context if event was workspace-scoped.",
    )
    target_type: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        doc="Type of the affected resource (user, session, workspace, membership).",
    )
    target_id: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        doc="Identifier string of the affected resource.",
    )
    request_id: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        doc="Correlation request ID from HTTP request header.",
    )
    ip_address: Mapped[str | None] = mapped_column(
        String(45),
        nullable=True,
        doc="Client IP address where request originated.",
    )
    metadata_json: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="Sanitized JSON metadata payload (never contains passwords or tokens).",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
        index=True,
        doc="UTC timestamp when the audit event was recorded.",
    )

    def __repr__(self) -> str:
        return f"<SecurityAuditEvent(id={self.id}, type='{self.event_type}', actor={self.actor_user_id})>"
