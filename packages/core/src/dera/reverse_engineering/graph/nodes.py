"""DERA Reverse Engineering — Phase 6.3 Table Node Representation.

Defines the strongly typed TableNode model representing real relational database tables
within the foreign key relationship graph.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from dera.metadata.enums import MetadataCompleteness, TableType
from dera.metadata.identity import ObjectId
from dera.metadata.provenance import MetadataProvenance


class TableNode(BaseModel):
    """Immutable graph node representing a real verified relational table.

    Guarantees:
    - Never constructed from inferred, guessed, or synthetic table names.
    - Preserves stable Phase 5.5 and 6.1 canonical ObjectId identity.
    - Retains namespace scope and full dialect provenance.
    - Strictly immutable (frozen).
    """

    model_config = ConfigDict(frozen=True)

    object_id: ObjectId = Field(
        ...,
        description="Deterministic canonical ObjectId uniquely identifying this table.",
    )
    namespace_id: ObjectId | None = Field(
        default=None,
        description="ObjectId of the namespace or schema owning this table.",
    )
    native_name: str = Field(
        ...,
        description="Exact declared native table identifier in the catalog.",
    )
    namespace_name: str = Field(
        default="public",
        description="Exact declared native schema or namespace identifier.",
    )
    table_type: TableType = Field(
        default=TableType.TABLE,
        description="Table entity classification (e.g. TABLE, SYSTEM_TABLE, PARTITIONED_TABLE).",
    )
    column_count: int = Field(
        default=0,
        ge=0,
        description="Total number of declared columns belonging to this table.",
    )
    primary_key_columns: tuple[str, ...] = Field(
        default_factory=tuple,
        description="Ordered column names participating in the table's primary key constraint.",
    )
    completeness: MetadataCompleteness = Field(
        default=MetadataCompleteness.COMPLETE,
        description="Completeness and confidence level of inspected table metadata.",
    )
    native_attributes: dict[str, Any] = Field(
        default_factory=dict,
        description="Dialect-specific storage or execution attributes (e.g. WITHOUT ROWID, STRICT).",
    )
    provenance: MetadataProvenance = Field(
        ...,
        description="Extraction provenance and audit record identifying source database origin.",
    )

    @property
    def fully_qualified_name(self) -> str:
        """Fully qualified native identifier: `<namespace>.<table_name>`."""
        return f"{self.namespace_name}.{self.native_name}"

    def __repr__(self) -> str:
        return f"TableNode({self.fully_qualified_name!r}, id={self.object_id!r})"
