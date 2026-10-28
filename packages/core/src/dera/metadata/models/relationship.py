"""DERA Canonical Metadata Normalization & Identity — Relationship Model.

Defines strongly-typed models for FOREIGN KEY referential constraints and
relationship graphs.
"""

from __future__ import annotations

from typing import Any

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, model_validator

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

    @model_validator(mode="before")
    @classmethod
    def _coerce_mappings_and_names(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "source_table_name" not in data and "source_table" in data:
                data["source_table_name"] = data["source_table"]
            elif "source_table_name" not in data:
                data["source_table_name"] = ""

            src_cols = tuple(
                data.get("source_columns")
                or data.get("source_column_names")
                or data.get("column_names")
                or data.get("columns")
                or ()
            )
            ref_cols = tuple(
                data.get("referenced_columns")
                or data.get("referenced_column_names")
                or ()
            )
            if "declared_source_columns" not in data and src_cols:
                data["declared_source_columns"] = src_cols
            if "declared_referenced_columns" not in data and ref_cols:
                data["declared_referenced_columns"] = ref_cols

            if "column_mappings" not in data:
                if src_cols and ref_cols and len(src_cols) == len(ref_cols):
                    data["column_mappings"] = tuple(
                        ForeignKeyMapping(source_column=s, referenced_column=r)
                        for s, r in zip(src_cols, ref_cols, strict=True)
                    )
                elif src_cols and not ref_cols:
                    data["column_mappings"] = tuple(
                        ForeignKeyMapping(source_column=s, referenced_column=s)
                        for s in src_cols
                    )
                elif src_cols and ref_cols:
                    data["column_mappings"] = ()
        return data

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
        validation_alias=AliasChoices("source_table_id", "table_id"),
        description="ObjectId of the child table declaring this foreign key.",
    )
    source_table_name: str = Field(
        default="",
        validation_alias=AliasChoices("source_table_name", "source_table"),
        description="Native name of the child table.",
    )
    referenced_table_id: str | None = Field(
        default=None,
        description="ObjectId of referenced target table if resolved in metadata report.",
    )
    referenced_table_name: str = Field(
        ...,
        validation_alias=AliasChoices("referenced_table_name", "referenced_table"),
        description="Native name of referenced parent table.",
    )
    referenced_schema: str | None = Field(
        default=None,
        description="Schema owning the referenced table.",
    )
    column_mappings: tuple[ForeignKeyMapping, ...] = Field(
        default_factory=tuple,
        description="Ordered tuple of child-to-parent column pairings.",
    )
    declared_source_columns: tuple[str, ...] = Field(
        default_factory=tuple,
        description="Explicit declared child column names.",
    )
    declared_referenced_columns: tuple[str, ...] = Field(
        default_factory=tuple,
        description="Explicit declared referenced parent column names.",
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
    extra_metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Engine-specific foreign key metadata.",
    )
    provenance: MetadataProvenance = Field(
        ...,
        description="Source extraction provenance and audit information.",
    )

    @property
    def source_columns(self) -> tuple[str, ...]:
        """Convenience tuple of source column names."""
        if self.declared_source_columns:
            return self.declared_source_columns
        return tuple(m.source_column for m in self.column_mappings)

    @property
    def column_names(self) -> tuple[str, ...]:
        """Alias for source_columns."""
        return self.source_columns

    @property
    def referenced_columns(self) -> tuple[str, ...]:
        """Convenience tuple of referenced column names."""
        if self.declared_referenced_columns:
            return self.declared_referenced_columns
        return tuple(m.referenced_column for m in self.column_mappings)

    @property
    def referenced_column_names(self) -> tuple[str, ...]:
        """Alias for referenced_columns."""
        return self.referenced_columns

    @property
    def referenced_schema_name(self) -> str | None:
        """Alias for referenced_schema."""
        return self.referenced_schema
