"""DERA Canonical Metadata Normalization & Identity — Table Model.

Defines the strongly-typed CanonicalTable model representing relational tables
with complete structural columns, constraints, foreign keys, indexes, and triggers.
"""

from __future__ import annotations

from typing import Any

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, model_validator

from dera.metadata.enums import ConstraintType, TableType
from dera.metadata.models.column import CanonicalColumn
from dera.metadata.models.constraint import CanonicalConstraint
from dera.metadata.models.index import CanonicalIndex
from dera.metadata.models.relationship import CanonicalForeignKey
from dera.metadata.models.trigger import CanonicalTrigger
from dera.metadata.provenance import MetadataProvenance


class CanonicalTable(BaseModel):
    """Canonical model for relational tables with hierarchical children."""

    model_config = ConfigDict(frozen=True)

    @model_validator(mode="before")
    @classmethod
    def _coerce_table_data(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "table_type" in data and isinstance(data["table_type"], str):
                tt = data["table_type"].upper().replace(" ", "_")
                if tt in ("BASE_TABLE", "TABLE"):
                    data["table_type"] = TableType.TABLE
            if "constraints" in data:
                constraints = data.get("constraints") or ()
                uqs = list(data.get("unique_constraints") or ())
                cks = list(data.get("check_constraints") or ())
                for c in constraints:
                    ctype = getattr(c, "constraint_type", None) or (
                        c.get("constraint_type") if isinstance(c, dict) else None
                    )
                    if ctype == ConstraintType.UNIQUE:
                        uqs.append(c)
                    elif ctype == ConstraintType.CHECK:
                        cks.append(c)
                data["unique_constraints"] = tuple(uqs)
                data["check_constraints"] = tuple(cks)
        return data

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
    schema_name: str | None = Field(
        default=None,
        validation_alias=AliasChoices("schema_name", "namespace", "schema"),
        description="Native schema or namespace identifier.",
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
    extra_metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Engine-specific or custom table metadata.",
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
