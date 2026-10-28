"""DERA Reverse Engineering — Phase 6.5 Snapshot Provenance.

Captures auditable metadata regarding source database type, versions, capture performance,
consistency guarantees, and connector metadata.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from dera.metadata.enums import MetadataCompleteness


class CaptureConsistency(StrEnum):
    """Guaranteed transactional consistency level of the source metadata capture."""

    TRANSACTIONAL = "transactional"
    POINT_IN_TIME = "point_in_time"
    BEST_EFFORT = "best_effort"
    UNKNOWN = "unknown"


class SnapshotProvenance(BaseModel):
    """Immutable audit provenance for a captured schema snapshot."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    engine: str = Field(
        ...,
        description="Database engine type (e.g. 'postgresql', 'sqlite', 'mysql', 'mariadb').",
    )
    engine_version: str | None = Field(
        default=None,
        description="Reported source database engine version string.",
    )
    connector_version: str | None = Field(
        default=None,
        description="Version of the connector or metadata extraction adapter used.",
    )
    capture_duration_ms: float | None = Field(
        default=None,
        description="Total duration of metadata extraction and snapshot capture in milliseconds.",
    )
    collection_status: str = Field(
        default="completed",
        description="Status of collection execution ('completed', 'partial', 'interrupted').",
    )
    completeness: MetadataCompleteness = Field(
        default=MetadataCompleteness.COMPLETE,
        description="Assessed completeness level of the extracted metadata.",
    )
    source_reference: str = Field(
        ...,
        description="Logical source name or authorized identifier (free of credentials).",
    )
    capture_consistency: CaptureConsistency = Field(
        default=CaptureConsistency.BEST_EFFORT,
        description="Transactional consistency level of the extraction.",
    )
    metadata_properties: dict[str, str] = Field(
        default_factory=dict,
        description="Additional non-sensitive operational environment properties.",
    )
