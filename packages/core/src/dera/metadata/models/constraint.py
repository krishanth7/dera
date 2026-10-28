"""DERA Canonical Metadata Normalization & Identity — Constraint Model.

Defines strongly-typed models for PRIMARY KEY, UNIQUE, and CHECK constraints.
"""

from __future__ import annotations

from typing import Any

from pydantic import AliasChoices, BaseModel, ConfigDict, Field

from dera.metadata.enums import ConstraintType
from dera.metadata.provenance import MetadataProvenance


class CanonicalConstraint(BaseModel):
    """Canonical model for relational table constraints (PK, UNIQUE, CHECK)."""

    model_config = ConfigDict(frozen=True)

    id: str = Field(
        ...,
        description="Deterministic canonical ObjectId for this constraint.",
    )
    parent_table_id: str = Field(
        ...,
        validation_alias=AliasChoices("parent_table_id", "table_id"),
        description="ObjectId of the owning parent table.",
    )
    name: str = Field(
        ...,
        description="Native constraint identifier, or deterministic surrogate for unnamed constraints.",
    )
    constraint_type: ConstraintType = Field(
        ...,
        description="Relational constraint classification: PRIMARY_KEY, UNIQUE, or CHECK.",
    )
    columns: tuple[str, ...] = Field(
        default_factory=tuple,
        validation_alias=AliasChoices("columns", "column_names"),
        description="Ordered tuple of column names participating in this constraint.",
    )

    @property
    def column_names(self) -> tuple[str, ...]:
        """Convenience property matching ReconstructedPrimaryKey."""
        return self.columns
    check_clause: str | None = Field(
        default=None,
        validation_alias=AliasChoices("check_clause", "expression"),
        description="SQL boolean expression text for CHECK constraints.",
    )
    is_enforced: bool = Field(
        default=True,
        description="True if database server actively enforces this constraint.",
    )
    is_synthetic_name: bool = Field(
        default=False,
        description="True if the constraint name is a generated surrogate (e.g. for SQLite unnamed CHECK).",
    )
    extra_metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Engine-specific or custom constraint metadata.",
    )
    provenance: MetadataProvenance = Field(
        ...,
        description="Source extraction provenance and audit information.",
    )
