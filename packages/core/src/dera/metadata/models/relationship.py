"""DERA Canonical Metadata Normalization & Identity — Relationship Model.

Defines strongly-typed models for FOREIGN KEY referential constraints and
relationship graphs.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from dera.metadata.enums import ForeignKeyAction
from dera.metadata.provenance import MetadataProvenance


class ForeignKeyMapping(BaseModel):
    """Pairing between a source column and its referenced target column."""

    model_config = ConfigDict(frozen=True)

    source_column: str = Field(
        ...,
        description="Column name in the originating child table.",
    )
    referenced_column: str = Field(
        ...,
        description="Referenced primary or unique key column in parent table.",
    )


class CanonicalForeignKey(BaseModel):
    """Canonical model for relational Foreign Key referential constraints."""

    model_config = ConfigDict(frozen=True)

    id: str = Field(
        ...,
        description="Deterministic canonical ObjectId for this foreign key.",
    )
    name: str = Field(
        ...,
        description="Native foreign key identifier or deterministic surrogate.",
    )
    source_table_id: str = Field(
        ...,
        description="ObjectId of the child table declaring this foreign key.",
    )
    source_table_name: str = Field(
        ...,
        description="Native name of the child table.",
    )
    referenced_table_id: str | None = Field(
        default=None,
        description="ObjectId of referenced target table if resolved in metadata report.",
    )
    referenced_table_name: str = Field(
        ...,
        description="Native name of referenced parent table.",
    )
    referenced_schema: str | None = Field(
        default=None,
        description="Schema owning the referenced table.",
    )
    column_mappings: tuple[ForeignKeyMapping, ...] = Field(
        ...,
        description="Ordered tuple of child-to-parent column pairings.",
    )
    on_update: ForeignKeyAction = Field(
        default=ForeignKeyAction.NO_ACTION,
        description="Referential action triggered upon parent key UPDATE.",
    )
    on_delete: ForeignKeyAction = Field(
        default=ForeignKeyAction.NO_ACTION,
        description="Referential action triggered upon parent row DELETE.",
    )
    is_deferrable: bool = Field(
        default=False,
        description="True if constraint evaluation can be deferred to transaction end.",
    )
    is_synthetic_name: bool = Field(
        default=False,
        description="True if constraint name is a generated surrogate.",
    )
    provenance: MetadataProvenance = Field(
        ...,
        description="Source extraction provenance and audit information.",
    )

    @property
    def source_columns(self) -> tuple[str, ...]:
        """Convenience tuple of source column names."""
        return tuple(m.source_column for m in self.column_mappings)

    @property
    def referenced_columns(self) -> tuple[str, ...]:
        """Convenience tuple of referenced column names."""
        return tuple(m.referenced_column for m in self.column_mappings)
