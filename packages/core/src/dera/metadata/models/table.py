"""DERA Canonical Metadata Normalization & Identity — Table Model.

Defines the strongly-typed CanonicalTable model representing relational tables
with complete structural columns, constraints, foreign keys, indexes, and triggers.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from dera.metadata.enums import TableType
from dera.metadata.models.column import CanonicalColumn
from dera.metadata.models.constraint import CanonicalConstraint
from dera.metadata.models.index import CanonicalIndex
from dera.metadata.models.relationship import CanonicalForeignKey
from dera.metadata.models.trigger import CanonicalTrigger
from dera.metadata.provenance import MetadataProvenance


class CanonicalTable(BaseModel):
    """Canonical model for relational tables with hierarchical children."""

    model_config = ConfigDict(frozen=True)

    id: str = Field(
        ...,
        description="Deterministic canonical ObjectId for this table.",
    )
    namespace_id: str = Field(
        ...,
        description="ObjectId of the namespace owning this table.",
    )
    name: str = Field(
        ...,
        description="Native table identifier.",
    )
    table_type: TableType = Field(
        default=TableType.TABLE,
        description="Relational object type (e.g. TABLE, SYSTEM_TABLE, PARTITIONED_TABLE).",
    )
    columns: tuple[CanonicalColumn, ...] = Field(
        default_factory=tuple,
        description="Ordered tuple of table columns by ordinal position.",
    )
    primary_key: CanonicalConstraint | None = Field(
        default=None,
        description="Primary key constraint definition, if declared on table.",
    )
    foreign_keys: tuple[CanonicalForeignKey, ...] = Field(
        default_factory=tuple,
        description="Ordered tuple of foreign key constraints originating from this table.",
    )
    unique_constraints: tuple[CanonicalConstraint, ...] = Field(
        default_factory=tuple,
        description="Ordered tuple of non-primary UNIQUE constraints.",
    )
    check_constraints: tuple[CanonicalConstraint, ...] = Field(
        default_factory=tuple,
        description="Ordered tuple of CHECK constraints evaluated on table rows.",
    )
    indexes: tuple[CanonicalIndex, ...] = Field(
        default_factory=tuple,
        description="Ordered tuple of secondary indexes defined on this table.",
    )
    triggers: tuple[CanonicalTrigger, ...] = Field(
        default_factory=tuple,
        description="Ordered tuple of procedural triggers attached to this table.",
    )
    comment: str | None = Field(
        default=None,
        description="Documentation or comment describing table purpose.",
    )
    provenance: MetadataProvenance = Field(
        ...,
        description="Source extraction provenance and audit information.",
    )

    @property
    def column_names(self) -> tuple[str, ...]:
        """Convenience tuple of all declared column names."""
        return tuple(col.name for col in self.columns)

    def get_column(self, name: str) -> CanonicalColumn | None:
        """Find a column by case-insensitive name match."""
        target = name.strip().lower()
        for col in self.columns:
            if col.name.strip().lower() == target:
                return col
        return None
