"""DERA Reverse Engineering — Phase 6.3 Foreign Key Edge Representation.

Defines strongly typed edge and column pairing models representing verified relational
foreign key constraints in the relationship directed multigraph.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from dera.metadata.enums import ForeignKeyAction
from dera.metadata.identity import ObjectId
from dera.metadata.provenance import MetadataProvenance
from dera.reverse_engineering.references import ResolutionStatus


class ColumnPairMapping(BaseModel):
    """Immutable mapping between an ordered source child column and its referenced parent column.

    Preserves exact declared ordinal sequencing for single and composite foreign keys.
    """

    model_config = ConfigDict(frozen=True)

    source_column_name: str = Field(
        ...,
        description="Declared native column identifier in the referencing (child) table.",
    )
    referenced_column_name: str = Field(
        ...,
        description="Declared native column identifier in the referenced (parent) table.",
    )
    source_column_id: ObjectId | None = Field(
        default=None,
        description="Canonical ObjectId of the source column, if resolved.",
    )
    referenced_column_id: ObjectId | None = Field(
        default=None,
        description="Canonical ObjectId of the referenced column, if resolved.",
    )
    ordinal_position: int = Field(
        ...,
        ge=1,
        description="1-based ordinal position of this column pair within the composite key declaration.",
    )

    def __repr__(self) -> str:
        return f"ColumnPairMapping({self.source_column_name} -> {self.referenced_column_name}, ord={self.ordinal_position})"


class ForeignKeyEdge(BaseModel):
    """Immutable directed multigraph edge representing an actual verified foreign key constraint.

    Canonical Direction Convention:
        Source foreign key child table (declaring FK) ---> Referenced parent table (holding PK/UQ)

    Example:
        `orders (customer_id)` ---> `customers (id)`

    Guarantees:
    - Keyed by unique constraint ObjectId; never identified solely by source/target endpoints.
    - Fully supports parallel edges (distinct FKs between same tables) and self-loops.
    - Preserves ordered column pairings, referential actions, deferrability, and enforcement.
    - Strictly immutable (frozen).
    """

    model_config = ConfigDict(frozen=True)

    object_id: ObjectId = Field(
        ...,
        description="Deterministic canonical ObjectId uniquely identifying this foreign key constraint.",
    )
    native_name: str = Field(
        ...,
        description="Native foreign key constraint name from database catalog, or deterministic surrogate.",
    )
    source_table_id: ObjectId = Field(
        ...,
        description="ObjectId of the child table declaring this foreign key.",
    )
    referenced_table_id: ObjectId | None = Field(
        default=None,
        description="ObjectId of the referenced parent table, or None if unresolved in metadata.",
    )
    source_namespace: str = Field(
        default="public",
        description="Native schema or namespace owning the source table.",
    )
    source_table_name: str = Field(
        ...,
        description="Native name of the child table declaring the constraint.",
    )
    referenced_namespace: str = Field(
        default="public",
        description="Native schema or namespace owning the referenced parent table.",
    )
    referenced_table_name: str = Field(
        ...,
        description="Native name of the referenced parent table.",
    )
    column_pairs: tuple[ColumnPairMapping, ...] = Field(
        default_factory=tuple,
        description="Ordered sequence of source-to-referenced column mappings.",
    )
    on_delete: ForeignKeyAction = Field(
        default=ForeignKeyAction.NO_ACTION,
        description="Referential action triggered upon parent row DELETE.",
    )
    on_update: ForeignKeyAction = Field(
        default=ForeignKeyAction.NO_ACTION,
        description="Referential action triggered upon parent key UPDATE.",
    )
    match_type: str | None = Field(
        default=None,
        description="SQL MATCH clause (e.g. FULL, PARTIAL, SIMPLE) where reported by engine.",
    )
    is_deferrable: bool = Field(
        default=False,
        description="True if constraint evaluation can be deferred to transaction end.",
    )
    is_enforced: bool = Field(
        default=True,
        description="True if database engine actively validates and enforces referential integrity.",
    )
    is_composite: bool = Field(
        default=False,
        description="True if constraint spans two or more column pairs.",
    )
    is_self_referencing: bool = Field(
        default=False,
        description="True if source and referenced table are the identical table (self-loop).",
    )
    is_cross_namespace: bool = Field(
        default=False,
        description="True if relationship spans two distinct schemas or namespaces.",
    )
    resolution_status: ResolutionStatus = Field(
        default=ResolutionStatus.RESOLVED,
        description="Referential resolution state: RESOLVED, MISSING, or INVALID.",
    )
    provenance: MetadataProvenance = Field(
        ...,
        description="Extraction provenance and audit record identifying source database origin.",
    )
    extra_metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Engine-specific referential attributes (e.g. SQLite FK id, MySQL storage engine flags).",
    )

    @property
    def source_columns(self) -> tuple[str, ...]:
        """Convenience tuple of source column names in declared sequence."""
        return tuple(p.source_column_name for p in self.column_pairs)

    @property
    def referenced_columns(self) -> tuple[str, ...]:
        """Convenience tuple of referenced column names in declared sequence."""
        return tuple(p.referenced_column_name for p in self.column_pairs)

    @property
    def source_fully_qualified_name(self) -> str:
        """Fully qualified source table name: `<schema>.<table_name>`."""
        return f"{self.source_namespace}.{self.source_table_name}"

    @property
    def referenced_fully_qualified_name(self) -> str:
        """Fully qualified referenced table name: `<schema>.<table_name>`."""
        return f"{self.referenced_namespace}.{self.referenced_table_name}"

    def __repr__(self) -> str:
        return (
            f"ForeignKeyEdge({self.source_fully_qualified_name} -> {self.referenced_fully_qualified_name}, "
            f"name={self.native_name!r}, id={self.object_id!r})"
        )
