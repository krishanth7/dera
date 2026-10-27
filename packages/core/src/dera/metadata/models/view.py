"""DERA Canonical Metadata Normalization & Identity — View Model.

Defines the strongly-typed CanonicalView model representing relational views.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from dera.metadata.provenance import MetadataProvenance


class CanonicalView(BaseModel):
    """Canonical model for relational views and materialized views."""

    model_config = ConfigDict(frozen=True)

    id: str = Field(
        ...,
        description="Deterministic canonical ObjectId for this view.",
    )
    namespace_id: str = Field(
        ...,
        description="ObjectId of the namespace owning this view.",
    )
    name: str = Field(
        ...,
        description="Native view identifier.",
    )
    is_materialized: bool = Field(
        default=False,
        description="True if view physically materializes rows on disk.",
    )
    definition: str | None = Field(
        default=None,
        description="Raw untrusted SQL query text defining the view logic.",
    )
    check_option: str | None = Field(
        default=None,
        description="View CHECK OPTION setting (e.g. 'LOCAL', 'CASCADED', 'NONE').",
    )
    is_updatable: bool = Field(
        default=False,
        description="True if view satisfies engine updatability rules.",
    )
    comment: str | None = Field(
        default=None,
        description="Documentation or comment describing view purpose.",
    )
    provenance: MetadataProvenance = Field(
        ...,
        description="Source extraction provenance and audit information.",
    )
