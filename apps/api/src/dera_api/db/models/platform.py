"""DERA Database — Platform Operational Models.

Defines minimal, justified platform operational models for DERA Milestone 4.3.
Stores internal configuration, migration state, and platform metadata.
Strictly separated from customer database inspection structures (Phase 5+).
"""

from datetime import UTC, datetime

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from dera_api.db.base import Base


class PlatformMetadata(Base):
    """Platform operational metadata and system state configuration.

    Represents key-value operational records for internal platform operations,
    such as schema baseline version, installation timestamp, and platform flags.
    """

    __tablename__ = "dera_platform_metadata"

    key: Mapped[str] = mapped_column(
        String(64),
        primary_key=True,
        index=True,
        doc="Unique identifier key for platform metadata entry.",
    )
    value: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc="Persisted value string (JSON/text) for the metadata entry.",
    )
    description: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        doc="Optional human-readable description of this operational key.",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
        doc="Timestamp in UTC when this record was initially created.",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
        doc="Timestamp in UTC when this record was last modified.",
    )

    def __repr__(self) -> str:
        return f"<PlatformMetadata(key='{self.key}', updated_at='{self.updated_at.isoformat()}')>"
