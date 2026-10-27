"""DERA Canonical Metadata Normalization & Identity — Namespace Model.

Defines the strongly-typed CanonicalNamespace model representing schema or catalog namespaces.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from dera.metadata.models.table import CanonicalTable
from dera.metadata.models.view import CanonicalView
from dera.metadata.provenance import MetadataProvenance


class CanonicalNamespace(BaseModel):
    """Canonical model for database namespaces or schemas (e.g. 'public', 'main')."""

    model_config = ConfigDict(frozen=True)

    id: str = Field(
        ...,
        description="Deterministic canonical ObjectId for this namespace.",
    )
    name: str = Field(
        ...,
        description="Native schema or namespace identifier.",
    )
    tables: tuple[CanonicalTable, ...] = Field(
        default_factory=tuple,
        description="Ordered tuple of relational tables residing within this namespace.",
    )
    views: tuple[CanonicalView, ...] = Field(
        default_factory=tuple,
        description="Ordered tuple of views residing within this namespace.",
    )
    comment: str | None = Field(
        default=None,
        description="Documentation or comment describing namespace purpose.",
    )
    provenance: MetadataProvenance = Field(
        ...,
        description="Source extraction provenance and audit information.",
    )

    def get_table(self, name: str) -> CanonicalTable | None:
        """Find table by case-insensitive name match."""
        target = name.strip().lower()
        for tbl in self.tables:
            if tbl.name.strip().lower() == target:
                return tbl
        return None

    def get_view(self, name: str) -> CanonicalView | None:
        """Find view by case-insensitive name match."""
        target = name.strip().lower()
        for v in self.views:
            if v.name.strip().lower() == target:
                return v
        return None
