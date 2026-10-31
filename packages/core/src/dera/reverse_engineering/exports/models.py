"""DERA Reverse Engineering — Phase 6.6 Export Models & Contracts.

Defines format enumerations, scope controls, configuration options,
and immutable export artifact representations.
"""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class ExportFormat(StrEnum):
    """Authoritative export formats supported by the DERA Core Engine."""

    JSON = "json"
    CSV = "csv"
    GRAPHML = "graphml"
    DOT = "dot"
    SNAPSHOT = "snapshot"


class ExportScope(StrEnum):
    """Granularity and target domain for export generation."""

    SCHEMA = "schema"
    NAMESPACE = "namespace"
    TABLE = "table"
    RELATIONSHIPS = "relationships"
    DEPENDENCIES = "dependencies"
    SNAPSHOT = "snapshot"


class ExportOptions(BaseModel):
    """Parameters governing export artifact generation."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    format: ExportFormat = Field(
        ...,
        description="Target export format.",
    )
    scope: ExportScope = Field(
        default=ExportScope.SCHEMA,
        description="Structural domain to export.",
    )
    target_id: str | None = Field(
        default=None,
        description="Optional specific object ID (namespace name, table ID) if scoped.",
    )
    safe_mode: bool = Field(
        default=True,
        description="If True, sanitize formula characters in CSV to prevent spreadsheet injection.",
    )
    include_provenance: bool = Field(
        default=True,
        description="Include source metadata provenance where applicable.",
    )
    pretty_print: bool = Field(
        default=False,
        description="Format output with whitespace and indentation for human inspection.",
    )
    max_depth: int = Field(
        default=32,
        ge=1,
        le=128,
        description="Maximum graph traversal depth for relationship/subgraph exports.",
    )


class ExportArtifact(BaseModel):
    """Immutable representation of a generated export artifact."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    format: ExportFormat = Field(
        ...,
        description="Format of the export.",
    )
    mime_type: str = Field(
        ...,
        description="IANA standard MIME type of the artifact.",
    )
    filename: str = Field(
        ...,
        description="Suggested secure download filename with appropriate extension.",
    )
    content_bytes: bytes = Field(
        ...,
        description="Exact raw bytes of the generated export.",
    )
    size_bytes: int = Field(
        ...,
        ge=0,
        description="Byte length of content_bytes.",
    )
    checksum_sha256: str = Field(
        ...,
        description="Hex-encoded SHA-256 digest of content_bytes for client integrity verification.",
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Timestamp when the artifact was generated.",
    )

    @classmethod
    def create(
        cls,
        format: ExportFormat,
        mime_type: str,
        filename: str,
        content_bytes: bytes,
    ) -> ExportArtifact:
        """Construct an ExportArtifact with automatically computed size and SHA-256 checksum."""
        digest = hashlib.sha256(content_bytes).hexdigest()
        return cls(
            format=format,
            mime_type=mime_type,
            filename=filename,
            content_bytes=content_bytes,
            size_bytes=len(content_bytes),
            checksum_sha256=digest,
            created_at=datetime.now(UTC),
        )
