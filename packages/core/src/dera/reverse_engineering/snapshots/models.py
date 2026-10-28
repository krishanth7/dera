"""DERA Reverse Engineering — Phase 6.5 Snapshot Domain Models.

Defines strongly typed, immutable Pydantic v2 domain models for schema snapshots,
structural payloads, capture envelopes, and deterministic structural content.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from dera.metadata.enums import (
    CanonicalTypeCategory,
    ForeignKeyAction,
    MetadataCompleteness,
    TableType,
)
from dera.metadata.identity import ObjectId
from dera.reverse_engineering.snapshots.provenance import SnapshotProvenance

SNAPSHOT_FORMAT_VERSION = "dera.schema.snapshot.v1"
FINGERPRINT_ALGORITHM_NAME = "SHA-256"
FINGERPRINT_CONTRACT_VERSION = "dera.fingerprint.v1"
FINGERPRINT_DOMAIN = "DERA:SCHEMA:STRUCTURAL:V1"


class SnapshotColumnPayload(BaseModel):
    """Normalized structural representation of a column in a snapshot table."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    column_id: ObjectId = Field(description="Canonical ObjectId of the column.")
    name: str = Field(description="Exact native column name.")
    ordinal_position: int = Field(
        description="1-based ordinal position preserving column ordering."
    )
    native_data_type: str = Field(description="Engine-specific declared native type string.")
    canonical_type: CanonicalTypeCategory = Field(description="Normalized canonical type category.")
    is_nullable: bool = Field(default=True, description="True if column accepts NULL values.")
    default_expression: str | None = Field(
        default=None, description="Inert default expression string."
    )
    character_maximum_length: int | None = Field(
        default=None, description="Max char length if applicable."
    )
    numeric_precision: int | None = Field(
        default=None, description="Numeric precision if applicable."
    )
    numeric_scale: int | None = Field(default=None, description="Numeric scale if applicable.")
    comment: str | None = Field(default=None, description="Column comment or documentation string.")


class SnapshotPrimaryKeyPayload(BaseModel):
    """Normalized structural representation of a primary key constraint."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    constraint_id: ObjectId = Field(description="Canonical ObjectId of the primary key constraint.")
    name: str = Field(description="Constraint name in source catalog.")
    columns: tuple[str, ...] = Field(description="Ordered list of member column names.")


class SnapshotForeignKeyPayload(BaseModel):
    """Normalized structural representation of a foreign key constraint."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    constraint_id: ObjectId = Field(description="Canonical ObjectId of the foreign key constraint.")
    name: str = Field(description="Constraint name in source catalog.")
    source_columns: tuple[str, ...] = Field(description="Ordered source column names.")
    target_namespace: str = Field(description="Referenced schema or namespace.")
    target_table: str = Field(description="Referenced table name.")
    target_columns: tuple[str, ...] = Field(description="Ordered referenced column names.")
    on_update: ForeignKeyAction = Field(
        default=ForeignKeyAction.NO_ACTION, description="ON UPDATE action."
    )
    on_delete: ForeignKeyAction = Field(
        default=ForeignKeyAction.NO_ACTION, description="ON DELETE action."
    )
    is_deferrable: bool = Field(default=False, description="True if constraint is deferrable.")
    initially_deferred: bool = Field(
        default=False, description="True if deferrable state is deferred."
    )


class SnapshotUniqueConstraintPayload(BaseModel):
    """Normalized structural representation of a unique constraint."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    constraint_id: ObjectId = Field(description="Canonical ObjectId of the unique constraint.")
    name: str = Field(description="Constraint name in source catalog.")
    columns: tuple[str, ...] = Field(description="Ordered list of constrained column names.")


class SnapshotCheckConstraintPayload(BaseModel):
    """Normalized structural representation of a check constraint."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    constraint_id: ObjectId = Field(description="Canonical ObjectId of the check constraint.")
    name: str = Field(description="Constraint name in source catalog.")
    expression: str = Field(description="Inert check expression string.")


class SnapshotIndexPayload(BaseModel):
    """Normalized structural representation of an index."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    index_id: ObjectId = Field(description="Canonical ObjectId of the index.")
    name: str = Field(description="Index name in source catalog.")
    columns: tuple[str, ...] = Field(description="Ordered column names or indexed expressions.")
    is_unique: bool = Field(default=False, description="True if index enforces uniqueness.")
    index_type: str = Field(
        default="BTREE", description="Index access method (BTREE, HASH, GIN, etc.)."
    )
    predicate: str | None = Field(
        default=None, description="Partial index WHERE predicate expression."
    )


class SnapshotTablePayload(BaseModel):
    """Normalized structural representation of a database table."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    table_id: ObjectId = Field(description="Canonical ObjectId of the table.")
    namespace: str = Field(description="Namespace / schema name.")
    name: str = Field(description="Table name.")
    table_type: TableType = Field(default=TableType.TABLE, description="Table classification.")
    columns: tuple[SnapshotColumnPayload, ...] = Field(
        default_factory=tuple,
        description="Columns strictly ordered by ordinal_position.",
    )
    primary_key: SnapshotPrimaryKeyPayload | None = Field(
        default=None,
        description="Primary key constraint definition if present.",
    )
    foreign_keys: tuple[SnapshotForeignKeyPayload, ...] = Field(
        default_factory=tuple,
        description="Foreign key constraints ordered deterministically.",
    )
    unique_constraints: tuple[SnapshotUniqueConstraintPayload, ...] = Field(
        default_factory=tuple,
        description="Unique constraints ordered deterministically.",
    )
    check_constraints: tuple[SnapshotCheckConstraintPayload, ...] = Field(
        default_factory=tuple,
        description="Check constraints ordered deterministically.",
    )
    indexes: tuple[SnapshotIndexPayload, ...] = Field(
        default_factory=tuple,
        description="Indexes ordered deterministically.",
    )
    comment: str | None = Field(default=None, description="Table comment or documentation.")


class SnapshotViewPayload(BaseModel):
    """Normalized structural representation of a view."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    view_id: ObjectId = Field(description="Canonical ObjectId of the view.")
    namespace: str = Field(description="Namespace / schema name.")
    name: str = Field(description="View name.")
    definition: str | None = Field(default=None, description="Inert SQL view query definition.")
    is_materialized: bool = Field(default=False, description="True if view is materialized.")


class SnapshotTriggerPayload(BaseModel):
    """Normalized structural representation of a trigger."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    trigger_id: ObjectId = Field(description="Canonical ObjectId of the trigger.")
    namespace: str = Field(description="Namespace / schema name.")
    name: str = Field(description="Trigger name.")
    table_name: str = Field(description="Target table name.")
    timing: str = Field(default="AFTER", description="Trigger timing (BEFORE, AFTER, INSTEAD OF).")
    events: tuple[str, ...] = Field(
        default_factory=tuple, description="Trigger events (INSERT, UPDATE, DELETE)."
    )
    action_statement: str | None = Field(default=None, description="Inert trigger body statement.")


class SnapshotRelationshipPayload(BaseModel):
    """Normalized structural foreign key relationship edge between tables."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    edge_id: str = Field(description="Unique edge identifier.")
    source_table_id: ObjectId = Field(description="Child table holding foreign key.")
    target_table_id: ObjectId = Field(description="Referenced parent table.")
    constraint_name: str = Field(description="Foreign key constraint name.")
    source_columns: tuple[str, ...] = Field(description="Source column names.")
    target_columns: tuple[str, ...] = Field(description="Target column names.")


class SnapshotDependencySummary(BaseModel):
    """High-level summary of dependency analysis and cycle metrics."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    total_edges: int = Field(default=0, description="Total directed dependency edges.")
    has_cycles: bool = Field(
        default=False, description="True if graph contains cyclic dependencies."
    )
    cycle_count: int = Field(default=0, description="Total detected elementary cycles.")
    scc_count: int = Field(default=0, description="Total strongly connected components.")
    cyclic_scc_count: int = Field(default=0, description="Count of cyclic SCCs.")
    topological_levels_count: int = Field(
        default=0, description="Count of parallel execution stages."
    )


class SnapshotStructuralPayload(BaseModel):
    """The canonical structural schema content included in cryptographic fingerprinting.

    Volatile operational metadata (e.g. timestamps, request IDs, storage details)
    is strictly excluded from this model.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_format: str = Field(
        default="dera.structural.v1",
        description="Version format of the canonical structural schema payload.",
    )
    database_name: str = Field(description="Logical database identifier.")
    engine: str = Field(
        description="Database engine type (e.g. postgresql, sqlite, mysql, mariadb)."
    )
    engine_version: str | None = Field(default=None, description="Engine version string if known.")
    namespaces: tuple[str, ...] = Field(
        default_factory=tuple, description="Lexicographically sorted namespaces."
    )
    tables: tuple[SnapshotTablePayload, ...] = Field(
        default_factory=tuple,
        description="Tables sorted canonically by namespace and name.",
    )
    views: tuple[SnapshotViewPayload, ...] = Field(
        default_factory=tuple,
        description="Views sorted canonically by namespace and name.",
    )
    triggers: tuple[SnapshotTriggerPayload, ...] = Field(
        default_factory=tuple,
        description="Triggers sorted canonically by namespace and name.",
    )
    relationships: tuple[SnapshotRelationshipPayload, ...] = Field(
        default_factory=tuple,
        description="Relationship edges sorted canonically.",
    )
    dependencies: SnapshotDependencySummary | None = Field(
        default=None,
        description="Deterministic dependency graph metrics summary.",
    )
    completeness: MetadataCompleteness = Field(
        default=MetadataCompleteness.COMPLETE,
        description="Metadata completeness state.",
    )


class SnapshotEnvelope(BaseModel):
    """Operational envelope containing capture metadata, provenance, and storage context.

    Fields in this envelope are deliberately excluded from structural fingerprint calculations.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    snapshot_id: str = Field(description="Unique snapshot record identifier (e.g. 'snap_...').")
    workspace_id: str = Field(description="Workspace identifier for tenant isolation.")
    database_id: ObjectId = Field(description="Canonical ObjectId of the root database entity.")
    source_reference: str = Field(description="Logical source name or authorized identifier.")
    capture_timestamp: datetime = Field(description="UTC timestamp when snapshot was captured.")
    provenance: SnapshotProvenance = Field(description="Audit and extraction provenance metadata.")
    validation_status: str = Field(default="VALID", description="Validation status code.")
    tags: dict[str, str] = Field(
        default_factory=dict, description="User or system tags (e.g. 'baseline')."
    )
    storage_metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Operational storage attributes (e.g. byte length, disk location).",
    )


class SchemaSnapshot(BaseModel):
    """Root immutable, versioned schema snapshot with cryptographic fingerprint.

    Contains the separated operational envelope and canonical structural payload.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    format_version: str = Field(
        default=SNAPSHOT_FORMAT_VERSION,
        description="Specification format version of the schema snapshot contract.",
    )
    snapshot_id: str = Field(description="Unique snapshot record identifier.")
    fingerprint: str = Field(
        description="Deterministic SHA-256 fingerprint computed strictly over the canonical structural payload.",
    )
    fingerprint_algorithm: str = Field(
        default=FINGERPRINT_ALGORITHM_NAME,
        description="Cryptographic algorithm used for structural digest (e.g. 'SHA-256').",
    )
    fingerprint_domain: str = Field(
        default=FINGERPRINT_DOMAIN,
        description="Domain separation identifier bound to the fingerprint digest.",
    )
    envelope: SnapshotEnvelope = Field(
        description="Capture envelope with volatile operational metadata.",
    )
    payload: SnapshotStructuralPayload = Field(
        description="Immutable, canonical structural payload.",
    )

    @property
    def database_name(self) -> str:
        """Convenience property for root database name."""
        return self.payload.database_name

    @property
    def engine(self) -> str:
        """Convenience property for source database engine."""
        return self.payload.engine

    @property
    def workspace_id(self) -> str:
        """Convenience property for workspace identifier."""
        return self.envelope.workspace_id

    @property
    def completeness(self) -> MetadataCompleteness:
        """Convenience property for metadata completeness."""
        return self.payload.completeness
