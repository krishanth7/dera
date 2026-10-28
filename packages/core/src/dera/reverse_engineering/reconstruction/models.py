"""Strongly typed, immutable domain models for Phase 6.2 Structural Reconstruction.

These models encapsulate reconstructed tables, columns, primary keys, foreign keys,
unique constraints, and check constraints preserving exact database semantics,
ordered key references, and provenance without inventing missing attributes.
"""

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, PrivateAttr

from dera.metadata.enums import (
    CanonicalTypeCategory,
    ForeignKeyAction,
    GenerationMode,
    MetadataCompleteness,
    TableType,
)
from dera.metadata.identity import ObjectId
from dera.metadata.provenance import ProvenanceRecord
from dera.reverse_engineering.capabilities import SchemaCapabilityProfile
from dera.reverse_engineering.references import ResolutionStatus


class NullabilityState(StrEnum):
    """Explicit nullability state of a column."""

    NULLABLE = "nullable"
    NOT_NULLABLE = "not_nullable"
    UNKNOWN = "unknown"


class DefaultKind(StrEnum):
    """Categorization of column default values."""

    NO_DEFAULT = "no_default"
    LITERAL = "literal"
    EXPRESSION = "expression"
    GENERATED = "generated"
    UNKNOWN = "unknown"


class ReconstructionMode(StrEnum):
    """Reconstruction execution mode controlling tolerance of incomplete metadata."""

    STRICT = "strict"
    PARTIAL = "partial"


class ValidationSeverity(StrEnum):
    """Severity classification for structural validation findings."""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class ConstraintValidationStatus(StrEnum):
    """Validation status of a constraint in the underlying database."""

    VALIDATED = "validated"
    NOT_VALIDATED = "not_validated"
    UNKNOWN = "unknown"


class ConstraintEnforcementStatus(StrEnum):
    """Enforcement state of a constraint."""

    ENFORCED = "enforced"
    NOT_ENFORCED = "not_enforced"
    UNKNOWN = "unknown"


class DefaultValueMetadata(BaseModel):
    """Metadata representing a column's declared default value."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    kind: DefaultKind
    raw_expression: str | None = None
    is_inert: bool = True


class GeneratedColumnMetadata(BaseModel):
    """Metadata describing a generated or computed column."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    is_generated: bool = False
    generation_mode: GenerationMode | None = None
    expression: str | None = None
    is_stored: bool = False


class IdentityMetadata(BaseModel):
    """Metadata for identity, auto-increment, and sequence-backed columns."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    is_identity: bool = False
    is_auto_increment: bool = False
    strategy: str | None = None
    sequence_name: str | None = None


class ReconstructedColumn(BaseModel):
    """A strongly typed, validated representation of a database column."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    object_id: ObjectId
    parent_table_id: ObjectId
    native_name: str
    ordinal_position: int
    native_type: str
    canonical_type: CanonicalTypeCategory
    nullability: NullabilityState
    default_value: DefaultValueMetadata
    generated_column: GeneratedColumnMetadata
    identity: IdentityMetadata
    collation: str | None = None
    comment: str | None = None
    provenance: ProvenanceRecord


class ReconstructedPrimaryKey(BaseModel):
    """A reconstructed primary key constraint with strict ordered column preservation."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    object_id: ObjectId
    owning_table_id: ObjectId
    native_name: str | None = None
    is_composite: bool
    column_ids: tuple[ObjectId, ...]
    column_names: tuple[str, ...]
    provenance: ProvenanceRecord


class ReconstructedForeignKey(BaseModel):
    """A reconstructed foreign key constraint preserving source and referenced pairs."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    object_id: ObjectId
    source_table_id: ObjectId
    native_name: str | None = None
    source_column_ids: tuple[ObjectId, ...]
    source_column_names: tuple[str, ...]
    referenced_table_id: ObjectId | None = None
    referenced_namespace: str | None = None
    referenced_table_name: str
    referenced_column_names: tuple[str, ...]
    referenced_column_ids: tuple[ObjectId, ...] = ()
    is_composite: bool
    on_update: ForeignKeyAction
    on_delete: ForeignKeyAction
    match_type: str | None = None
    deferrability: str | None = None
    enforcement_status: ConstraintEnforcementStatus = ConstraintEnforcementStatus.ENFORCED
    validation_status: ConstraintValidationStatus = ConstraintValidationStatus.VALIDATED
    resolution_status: ResolutionStatus = ResolutionStatus.MISSING
    is_cross_namespace: bool = False
    provenance: ProvenanceRecord


class ReconstructedUniqueConstraint(BaseModel):
    """A reconstructed unique constraint distinguishing itself from secondary indexes."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    object_id: ObjectId
    owning_table_id: ObjectId
    native_name: str | None = None
    is_composite: bool
    column_ids: tuple[ObjectId, ...]
    column_names: tuple[str, ...]
    enforcement_status: ConstraintEnforcementStatus = ConstraintEnforcementStatus.ENFORCED
    null_distinct: bool | None = None
    provenance: ProvenanceRecord


class ReconstructedCheckConstraint(BaseModel):
    """A reconstructed check constraint preserving inert expression text."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    object_id: ObjectId
    owning_table_id: ObjectId
    native_name: str | None = None
    expression: str
    enforcement_status: ConstraintEnforcementStatus = ConstraintEnforcementStatus.ENFORCED
    validation_status: ConstraintValidationStatus = ConstraintValidationStatus.VALIDATED
    provenance: ProvenanceRecord


class ReconstructedTable(BaseModel):
    """A fully reconstructed table model combining ordered columns and constraints."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    object_id: ObjectId
    namespace: str
    native_name: str
    table_type: TableType = TableType.TABLE
    columns: tuple[ReconstructedColumn, ...]
    primary_key: ReconstructedPrimaryKey | None = None
    foreign_keys: tuple[ReconstructedForeignKey, ...] = ()
    unique_constraints: tuple[ReconstructedUniqueConstraint, ...] = ()
    check_constraints: tuple[ReconstructedCheckConstraint, ...] = ()
    native_attributes: dict[str, Any] = Field(default_factory=dict)
    completeness: MetadataCompleteness = MetadataCompleteness.COMPLETE
    provenance: ProvenanceRecord

    def get_column_by_name(self, name: str) -> ReconstructedColumn | None:
        """Lookup a column by native name within this table."""
        for col in self.columns:
            if col.native_name == name:
                return col
        return None

    def get_column_by_id(self, col_id: ObjectId) -> ReconstructedColumn | None:
        """Lookup a column by ObjectId within this table."""
        for col in self.columns:
            if col.object_id == col_id:
                return col
        return None

    @property
    def has_composite_primary_key(self) -> bool:
        """Return True if table has a composite primary key."""
        return self.primary_key is not None and self.primary_key.is_composite


class StructuralValidationFinding(BaseModel):
    """A diagnostic finding produced during structural validation."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    severity: ValidationSeverity
    code: str
    message: str
    object_id: ObjectId | None = None
    details: dict[str, Any] = Field(default_factory=dict)


class StructuralReconstructionResult(BaseModel):
    """The root output of the Phase 6.2 Structural Reconstruction engine."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    contract_version: str = "1.0.0"
    schema_hash: str
    database_name: str
    engine: str
    reconstruction_mode: ReconstructionMode = ReconstructionMode.STRICT
    tables: tuple[ReconstructedTable, ...]
    findings: tuple[StructuralValidationFinding, ...] = ()
    capability_profile: SchemaCapabilityProfile
    resource_metrics: dict[str, Any] = Field(default_factory=dict)
    provenance: ProvenanceRecord

    _table_index: dict[ObjectId, ReconstructedTable] = PrivateAttr(default_factory=dict)
    _table_name_index: dict[tuple[str, str], ReconstructedTable] = PrivateAttr(default_factory=dict)
    _column_index: dict[ObjectId, ReconstructedColumn] = PrivateAttr(default_factory=dict)

    def model_post_init(self, __context: Any) -> None:
        """Build O(1) in-memory indices for rapid navigation."""
        super().model_post_init(__context)
        table_idx: dict[ObjectId, ReconstructedTable] = {}
        table_name_idx: dict[tuple[str, str], ReconstructedTable] = {}
        col_idx: dict[ObjectId, ReconstructedColumn] = {}

        for tbl in self.tables:
            table_idx[tbl.object_id] = tbl
            table_name_idx[(tbl.namespace, tbl.native_name)] = tbl
            for col in tbl.columns:
                col_idx[col.object_id] = col

        self._table_index = table_idx
        self._table_name_index = table_name_idx
        self._column_index = col_idx

    def get_table(self, table_id: ObjectId) -> ReconstructedTable | None:
        """O(1) table lookup by ObjectId."""
        return self._table_index.get(table_id)

    def get_table_by_name(self, namespace: str, name: str) -> ReconstructedTable | None:
        """O(1) table lookup by namespace and native name."""
        return self._table_name_index.get((namespace, name))

    def get_column(self, col_id: ObjectId) -> ReconstructedColumn | None:
        """O(1) column lookup by ObjectId."""
        return self._column_index.get(col_id)

    @property
    def is_valid(self) -> bool:
        """True if there are zero ERROR-severity findings."""
        return not any(f.severity == ValidationSeverity.ERROR for f in self.findings)

    @property
    def error_count(self) -> int:
        """Total number of ERROR findings."""
        return sum(1 for f in self.findings if f.severity == ValidationSeverity.ERROR)

    @property
    def warning_count(self) -> int:
        """Total number of WARNING findings."""
        return sum(1 for f in self.findings if f.severity == ValidationSeverity.WARNING)
