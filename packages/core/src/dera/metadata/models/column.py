"""DERA Canonical Metadata Normalization & Identity — Column Model.

Defines the strongly typed CanonicalColumn model representing relational column
metadata with canonical type classification and engine fidelity.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from dera.metadata.enums import CanonicalTypeCategory, GenerationMode
from dera.metadata.provenance import MetadataProvenance


class CanonicalColumn(BaseModel):
    """Canonical, engine-agnostic representation of a relational table column."""

    model_config = ConfigDict(frozen=True)

    id: str = Field(
        ...,
        description="Deterministic canonical ObjectId for this column.",
    )
    parent_table_id: str = Field(
        ...,
        description="ObjectId of the owning parent table.",
    )
    name: str = Field(
        ...,
        description="Exact declared native column identifier.",
    )
    ordinal_position: int = Field(
        ...,
        description="1-based ordinal position of the column within the table definition.",
    )
    native_data_type: str = Field(
        ...,
        description="Full original native type declaration (e.g. 'VARCHAR(255)', 'JSONB').",
    )
    canonical_type: CanonicalTypeCategory = Field(
        ...,
        description="Categorical semantic classification in the DERA type taxonomy.",
    )
    is_nullable: bool = Field(
        default=True,
        description="True if column accepts NULL; False if NOT NULL constraint is enforced.",
    )
    default_expression: str | None = Field(
        default=None,
        description="Raw default value or expression string as declared in source catalog.",
    )
    is_identity: bool = Field(
        default=False,
        description="True if column is marked as auto-increment, serial, or identity.",
    )
    is_generated: bool = Field(
        default=False,
        description="True if column is a stored or virtual generated/computed column.",
    )
    generation_mode: GenerationMode = Field(
        default=GenerationMode.NONE,
        description="Storage mode: STORED, VIRTUAL, or NONE.",
    )
    generation_expression: str | None = Field(
        default=None,
        description="Expression formula defining the generated column value.",
    )
    collation: str | None = Field(
        default=None,
        description="Collation sequence or character set assigned to this column.",
    )
    comment: str | None = Field(
        default=None,
        description="Documentation or comment describing column semantics.",
    )
    provenance: MetadataProvenance = Field(
        ...,
        description="Source extraction provenance and audit information.",
    )
