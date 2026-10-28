"""DERA Reverse Engineering — Phase 6.1 Canonical Schema Representation.

Defines the root SchemaRepresentation model encapsulating one authorized database
schema inspection result. Integrates:
- Database identity and provenance.
- Namespaces and hierarchical database structure.
- ObjectRegistry for O(1) kind-verified lookup.
- SchemaHierarchy for deterministic structural traversal.
- Typed object references and foreign key relationship references.
- Capability-aware completeness information.
- Referential integrity validation state.
- Deterministic serialization and cryptographic hashing.

Free of plain database credentials. Does not reconnect to source databases.
"""

from __future__ import annotations

import hashlib
import json
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, ConfigDict, Field, PrivateAttr
from pydantic_core import to_jsonable_python

from dera.metadata.enums import MetadataCompleteness
from dera.metadata.models.column import CanonicalColumn
from dera.metadata.models.constraint import CanonicalConstraint
from dera.metadata.models.database import CanonicalDatabase
from dera.metadata.models.index import CanonicalIndex
from dera.metadata.models.namespace import CanonicalNamespace
from dera.metadata.models.relationship import CanonicalForeignKey
from dera.metadata.models.table import CanonicalTable
from dera.metadata.models.trigger import CanonicalTrigger
from dera.metadata.models.view import CanonicalView
from dera.metadata.provenance import MetadataProvenance
from dera.metadata.serialization import _canonical_default_serializer
from dera.reverse_engineering.capabilities import SchemaCapabilityProfile
from dera.reverse_engineering.hierarchy import SchemaHierarchy
from dera.reverse_engineering.references import ForeignKeyReference
from dera.reverse_engineering.registry import ObjectRegistry

if TYPE_CHECKING:
    pass

SCHEMA_REPRESENTATION_CONTRACT_VERSION: str = "1.0.0"


def _normalize_sets(value: Any) -> Any:
    """Order unordered collections before JSON conversion erases their set type."""
    if isinstance(value, dict):
        return {key: _normalize_sets(item) for key, item in value.items()}
    if isinstance(value, (set, frozenset)):
        return sorted(
            (_normalize_sets(item) for item in value),
            key=lambda item: json.dumps(
                to_jsonable_python(item), sort_keys=True, ensure_ascii=False, separators=(",", ":")
            ),
        )
    if isinstance(value, (tuple, list)):
        return [_normalize_sets(item) for item in value]
    return value


class SchemaRepresentation(BaseModel):
    """Immutable, strongly typed root representation of an authorized database schema.

    Encapsulates:
    - Canonical database model and hierarchy.
    - O(1) ObjectRegistry for lookup and duplicate protection.
    - SchemaHierarchy for stable structural navigation.
    - Verified foreign key relationship references.
    - Capability profile and completeness assessment.
    - Integrity validation state and diagnostic issues.
    """

    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)

    contract_version: str = Field(
        default=SCHEMA_REPRESENTATION_CONTRACT_VERSION,
        description="Version string of the canonical schema representation contract.",
    )
    database_id: str = Field(
        ...,
        description="Deterministic canonical ObjectId of the database root.",
    )
    database_name: str = Field(
        ...,
        description="Logical database identifier or connection database name.",
    )
    engine: str = Field(
        ...,
        description="Database engine type (e.g. 'postgresql', 'sqlite', 'mysql', 'mariadb').",
    )
    engine_version: str | None = Field(
        default=None,
        description="Reported server version string, if available.",
    )
    source_reference: str = Field(
        ...,
        description="Authorized source label or database name (no credentials).",
    )
    provenance: MetadataProvenance = Field(
        ...,
        description="Extraction provenance and audit metadata.",
    )
    database: CanonicalDatabase = Field(
        ...,
        description="Underlying CanonicalDatabase model containing all namespaces.",
    )
    namespaces: tuple[CanonicalNamespace, ...] = Field(
        default_factory=tuple,
        description="Deterministically ordered namespaces belonging to this database.",
    )
    foreign_key_references: tuple[ForeignKeyReference, ...] = Field(
        default_factory=tuple,
        description="Deterministically ordered, resolution-aware foreign key references.",
    )
    capability_profile: SchemaCapabilityProfile | None = Field(
        default=None,
        description="Engine capability assessment and completeness report.",
    )
    completeness: MetadataCompleteness = Field(
        default=MetadataCompleteness.COMPLETE,
        description="Overall metadata completeness status.",
    )
    is_validated: bool = Field(
        default=False,
        description="True if referential integrity validation passed without error.",
    )
    validation_issues: tuple[str, ...] = Field(
        default_factory=tuple,
        description="Diagnostic messages from structural validation.",
    )
    resource_metrics: dict[str, Any] = Field(
        default_factory=dict,
        description="Resource bounded metrics (object counts, depth, timing).",
    )

    # Backing private attributes not serialized directly
    _registry: ObjectRegistry = PrivateAttr()
    _hierarchy: SchemaHierarchy = PrivateAttr()
    _build_duration_ms: float | None = PrivateAttr(default=None)

    def __init__(
        self,
        registry: ObjectRegistry | None = None,
        build_duration_ms: float | None = None,
        **data: Any,
    ) -> None:
        """Initialise SchemaRepresentation with backing ObjectRegistry and SchemaHierarchy."""
        super().__init__(**data)
        self._build_duration_ms = build_duration_ms
        if registry is not None:
            self._registry = registry
        else:
            # Reconstruct registry from database if not explicitly passed
            from dera.reverse_engineering.builder import SchemaBuilder

            rebuilt = SchemaBuilder.from_canonical_database(self.database, strict_validation=False)
            self._registry = rebuilt.registry

        self._hierarchy = SchemaHierarchy(self._registry)

    @property
    def build_duration_ms(self) -> float | None:
        """Elapsed schema construction time in milliseconds."""
        return self._build_duration_ms

    # ------------------------------------------------------------------
    # Backing services
    # ------------------------------------------------------------------

    @property
    def registry(self) -> ObjectRegistry:
        """The backing ObjectRegistry providing O(1) typed lookup."""
        return self._registry

    @property
    def hierarchy(self) -> SchemaHierarchy:
        """The SchemaHierarchy navigator providing stable hierarchical traversal."""
        return self._hierarchy

    # ------------------------------------------------------------------
    # Object lookup API
    # ------------------------------------------------------------------

    def get_object(self, object_id: str) -> Any | None:
        """Look up any registered schema object by its canonical ObjectId."""
        return self._registry.get_object(object_id)

    def contains(self, object_id: str) -> bool:
        """Return True if the canonical ObjectId is registered."""
        return self._registry.contains(object_id)

    def get_database(self, object_id: str) -> CanonicalDatabase:
        """Return CanonicalDatabase by ObjectId, or raise InvalidSchemaReferenceError."""
        return self._registry.get_database(object_id)

    def get_namespace(self, object_id: str) -> CanonicalNamespace:
        """Return CanonicalNamespace by ObjectId, or raise InvalidSchemaReferenceError."""
        return self._registry.get_namespace(object_id)

    def get_table(self, object_id: str) -> CanonicalTable:
        """Return CanonicalTable by ObjectId, or raise InvalidSchemaReferenceError."""
        return self._registry.get_table(object_id)

    def get_column(self, object_id: str) -> CanonicalColumn:
        """Return CanonicalColumn by ObjectId, or raise InvalidSchemaReferenceError."""
        return self._registry.get_column(object_id)

    def get_constraint(self, object_id: str) -> CanonicalConstraint:
        """Return CanonicalConstraint by ObjectId, or raise InvalidSchemaReferenceError."""
        return self._registry.get_constraint(object_id)

    def get_foreign_key(self, object_id: str) -> CanonicalForeignKey:
        """Return CanonicalForeignKey by ObjectId, or raise InvalidSchemaReferenceError."""
        return self._registry.get_foreign_key(object_id)

    def get_index(self, object_id: str) -> CanonicalIndex:
        """Return CanonicalIndex by ObjectId, or raise InvalidSchemaReferenceError."""
        return self._registry.get_index(object_id)

    def get_view(self, object_id: str) -> CanonicalView:
        """Return CanonicalView by ObjectId, or raise InvalidSchemaReferenceError."""
        return self._registry.get_view(object_id)

    def get_trigger(self, object_id: str) -> CanonicalTrigger:
        """Return CanonicalTrigger by ObjectId, or raise InvalidSchemaReferenceError."""
        return self._registry.get_trigger(object_id)

    # ------------------------------------------------------------------
    # Convenience hierarchical queries
    # ------------------------------------------------------------------

    def find_table(self, schema_name: str, table_name: str) -> CanonicalTable | None:
        """Look up a table by schema name and table name."""
        return self.database.find_table(schema_name, table_name)

    def find_column(
        self, schema_name: str, table_name: str, column_name: str
    ) -> CanonicalColumn | None:
        """Look up a column by schema, table, and column names."""
        tbl = self.find_table(schema_name, table_name)
        if tbl is None:
            return None
        return tbl.get_column(column_name)

    def all_tables(self) -> tuple[CanonicalTable, ...]:
        """Return all tables across all namespaces in deterministic order."""
        return self._hierarchy.all_tables_in_database(self.database_id)

    def all_views(self) -> tuple[CanonicalView, ...]:
        """Return all views across all namespaces in deterministic order."""
        return self._hierarchy.all_views_in_database(self.database_id)

    def all_foreign_keys(self) -> tuple[CanonicalForeignKey, ...]:
        """Return all foreign keys across all tables in deterministic order."""
        return self._hierarchy.all_foreign_keys_in_database(self.database_id)

    @property
    def total_objects(self) -> int:
        """Total number of objects registered in the schema."""
        return self._registry.total_objects

    # ------------------------------------------------------------------
    # Deterministic serialization
    # ------------------------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        """Dump schema representation to a plain dictionary."""
        return to_jsonable_python(_normalize_sets(self.model_dump(mode="python")))

    def to_json(self, indent: int | None = 2) -> str:
        """Serialize to deterministic, sorted-key UTF-8 JSON string."""
        raw_dict = self.to_dict()
        return json.dumps(
            raw_dict,
            indent=indent,
            sort_keys=True,
            ensure_ascii=False,
            default=_canonical_default_serializer,
        )

    def compute_hash(self) -> str:
        """Compute a deterministic SHA-256 fingerprint over the compact JSON bytes."""
        compact_json = json.dumps(
            self.to_dict(),
            indent=None,
            separators=(",", ":"),
            sort_keys=True,
            ensure_ascii=False,
            default=_canonical_default_serializer,
        )
        return hashlib.sha256(compact_json.encode("utf-8")).hexdigest()

    def __repr__(self) -> str:
        return (
            f"SchemaRepresentation(db={self.database_name!r}, engine={self.engine!r}, "
            f"namespaces={len(self.namespaces)}, total_objects={self.total_objects}, "
            f"validated={self.is_validated})"
        )


__all__ = [
    "SCHEMA_REPRESENTATION_CONTRACT_VERSION",
    "SchemaRepresentation",
]
