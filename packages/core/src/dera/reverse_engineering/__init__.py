"""DERA Reverse Engineering — Phase 6.1 Canonical Schema Representation.

Top-level package for the DERA Reverse Engineering Core Engine.

This package transforms validated Phase 5.5 canonical metadata into a strongly-typed,
navigable, registry-backed schema representation suitable for exploration, dependency
analysis, diagnostics, snapshots, and export.

Reuses:
  - dera.metadata canonical models (CanonicalDatabase, CanonicalTable, etc.)
  - dera.metadata identity (compute_stable_object_id)
  - dera.metadata enums (ObjectKind, MetadataCompleteness, etc.)
  - dera.metadata ordering (sort_* functions)
  - dera.metadata serialization conventions

Does NOT:
  - Reconnect to source databases.
  - Execute customer SQL.
  - Invent tables, columns, constraints, or relationships.
  - Introduce AI/LLM/ML inference.
"""

from __future__ import annotations

from dera.reverse_engineering.builder import SchemaBuilder, SchemaResourceLimits
from dera.reverse_engineering.capabilities import (
    CapabilityState,
    SchemaCapabilityProfile,
    assess_schema_capabilities,
)
from dera.reverse_engineering.errors import (
    DuplicateRegistrationError,
    InvalidSchemaInputError,
    InvalidSchemaReferenceError,
    MissingParentError,
    SchemaBuilderError,
    SchemaRepresentationError,
    SchemaResourceLimitError,
    SchemaSerializationError,
    SchemaValidationError,
    UnsupportedSchemaContractError,
)
from dera.reverse_engineering.exports import (
    ExportArtifact,
    ExportFormat,
    ExportOptions,
    ExportService,
)
from dera.reverse_engineering.hierarchy import SchemaHierarchy
from dera.reverse_engineering.ordering import (
    sort_columns,
    sort_constraints,
    sort_foreign_key_references,
    sort_foreign_keys,
    sort_indexes,
    sort_namespaces,
    sort_object_ids,
    sort_references,
    sort_tables,
    sort_triggers,
    sort_views,
)
from dera.reverse_engineering.references import (
    ForeignKeyReference,
    ResolutionStatus,
    TypedRef,
)
from dera.reverse_engineering.registry import ObjectRegistry
from dera.reverse_engineering.schema import (
    SCHEMA_REPRESENTATION_CONTRACT_VERSION,
    SchemaRepresentation,
)
from dera.reverse_engineering.serialization import (
    compute_schema_hash,
    deserialize_schema_representation,
    serialize_schema_representation,
)
from dera.reverse_engineering.snapshots import (
    SchemaSnapshot,
    SchemaSnapshotBuilder,
)
from dera.reverse_engineering.validation import validate_schema_representation

__all__ = [
    "SCHEMA_REPRESENTATION_CONTRACT_VERSION",
    "CapabilityState",
    "DuplicateRegistrationError",
    "ForeignKeyReference",
    "InvalidSchemaInputError",
    "InvalidSchemaReferenceError",
    "MissingParentError",
    "ObjectRegistry",
    "ResolutionStatus",
    "SchemaBuilder",
    "SchemaBuilderError",
    "SchemaCapabilityProfile",
    "SchemaHierarchy",
    "SchemaRepresentation",
    "SchemaRepresentationError",
    "SchemaResourceLimitError",
    "SchemaResourceLimits",
    "SchemaSerializationError",
    "SchemaValidationError",
    "TypedRef",
    "UnsupportedSchemaContractError",
    "assess_schema_capabilities",
    "compute_schema_hash",
    "deserialize_schema_representation",
    "serialize_schema_representation",
    "sort_columns",
    "sort_constraints",
    "sort_foreign_key_references",
    "sort_foreign_keys",
    "sort_indexes",
    "sort_namespaces",
    "sort_object_ids",
    "sort_references",
    "sort_tables",
    "sort_triggers",
    "sort_views",
    "validate_schema_representation",
    "SchemaSnapshot",
    "SchemaSnapshotBuilder",
    "ExportArtifact",
    "ExportFormat",
    "ExportOptions",
    "ExportService",
]
