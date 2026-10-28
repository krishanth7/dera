"""DERA Canonical Metadata Normalization & Identity — Provenance Model.

Records comprehensive audit trails, origin metadata, connector version,
collection timestamps, and source-specific diagnostics without leaking credentials.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from pydantic import AliasChoices, BaseModel, ConfigDict, Field

from dera.metadata.enums import MetadataCompleteness


class MetadataProvenance(BaseModel):
    """Immutable audit trail capturing source metadata origins and extraction details."""

    model_config = ConfigDict(frozen=True)

    source_engine: str = Field(
        ...,
        description="Origin database engine type (e.g. postgresql, sqlite, mysql, mariadb).",
    )
    source_version: str | None = Field(
        default=None,
        description="Version string reported by the source database server.",
    )
    connector_version: str = Field(
        default="0.1.0-dev",
        description="Version of the DERA connector adapter that extracted the metadata.",
    )
    collection_timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        validation_alias=AliasChoices("collection_timestamp", "extracted_at"),
        description="RFC 3339 UTC timestamp when metadata was extracted.",
    )
    completeness: MetadataCompleteness = Field(
        default=MetadataCompleteness.COMPLETE,
        description="Confidence or completeness classification for this metadata entity.",
    )
    source_location: str | None = Field(
        default=None,
        validation_alias=AliasChoices("source_location", "location"),
        description="Safe, sanitized location descriptor (e.g. schema name or sanitized database path).",
    )
    native_identifier: str = Field(
        default="unknown",
        validation_alias=AliasChoices("native_identifier", "identifier"),
        description="Original, unmutated identifier as extracted from catalog tables.",
    )
    capability_status: str | None = Field(
        default=None,
        description="Optional capability assessment flag explaining partial or restricted visibility.",
    )
    engine_specific: dict[str, Any] = Field(
        default_factory=dict,
        description="Engine-specific un-normalized metadata attributes preserved for lossless fidelity.",
    )


ProvenanceRecord = MetadataProvenance
