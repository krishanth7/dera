"""DERA Canonical Metadata Normalization & Identity — Index Model.

Defines strongly-typed models for table indexes and ordered index terms.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from dera.metadata.enums import IndexType
from dera.metadata.provenance import MetadataProvenance


class CanonicalIndexTerm(BaseModel):
    """Represents a single indexed term (column or expression) within an index."""

    model_config = ConfigDict(frozen=True)

    column_name: str | None = Field(
        default=None,
        description="Name of indexed column if standard column reference.",
    )
    expression: str | None = Field(
        default=None,
        description="SQL expression text if functional/expression index term.",
    )
    ordinal_position: int = Field(
        ...,
        description="1-based ordinal position of term within the index key definition.",
    )
    is_descending: bool = Field(
        default=False,
        description="True if term sort ordering is DESC; False if ASC.",
    )
    nulls_first: bool = Field(
        default=False,
        description="True if NULLS FIRST sort ordering was explicitly specified.",
    )
    is_expression: bool = Field(
        default=False,
        description="True if this term is an expression rather than a plain column.",
    )


class CanonicalIndex(BaseModel):
    """Canonical model for relational table indexes."""

    model_config = ConfigDict(frozen=True)

    id: str = Field(
        ...,
        description="Deterministic canonical ObjectId for this index.",
    )
    parent_table_id: str = Field(
        ...,
        description="ObjectId of the owning parent table.",
    )
    name: str = Field(
        ...,
        description="Native index identifier.",
    )
    is_unique: bool = Field(
        default=False,
        description="True if index enforces unique values.",
    )
    is_primary: bool = Field(
        default=False,
        description="True if this index backs the table's PRIMARY KEY.",
    )
    index_type: IndexType = Field(
        default=IndexType.BTREE,
        description="Access method or physical storage structure of index.",
    )
    terms: tuple[CanonicalIndexTerm, ...] = Field(
        ...,
        description="Ordered tuple of indexed columns and expressions.",
    )
    predicate: str | None = Field(
        default=None,
        description="Partial index WHERE predicate expression, if applicable.",
    )
    provenance: MetadataProvenance = Field(
        ...,
        description="Source extraction provenance and audit information.",
    )

    @property
    def column_names(self) -> tuple[str, ...]:
        """Convenience tuple of standard column names in index terms."""
        return tuple(term.column_name for term in self.terms if term.column_name is not None)
