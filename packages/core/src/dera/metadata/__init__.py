"""DERA Canonical Metadata Normalization & Identity Package.

Provides engine-agnostic normalization, cryptographic object identity,
deterministic sorting, and byte-level serialization for database metadata.
"""

from dera.metadata.contracts import CANONICAL_METADATA_CONTRACT_VERSION
from dera.metadata.enums import (
    CanonicalTypeCategory,
    ConstraintType,
    ForeignKeyAction,
    GenerationMode,
    IdentityScope,
    IndexType,
    MetadataCompleteness,
    ObjectKind,
    TableType,
    TriggerEvent,
    TriggerTiming,
)
from dera.metadata.errors import (
    DuplicateIdentityError,
    IdentityConflictError,
    InvalidConnectorMetadataError,
    InvalidReferenceError,
    MetadataLimitExceededError,
    MetadataNormalizationError,
    MetadataSerializationError,
    MissingRequiredMetadataError,
    UnsupportedMappingError,
)
from dera.metadata.identity import (
    compute_stable_object_id,
    generate_unnamed_constraint_name,
)
from dera.metadata.models import (
    CanonicalColumn,
    CanonicalConstraint,
    CanonicalDatabase,
    CanonicalForeignKey,
    CanonicalIndex,
    CanonicalIndexTerm,
    CanonicalNamespace,
    CanonicalTable,
    CanonicalTrigger,
    CanonicalView,
    ForeignKeyMapping,
)
from dera.metadata.normalization import MetadataNormalizer
from dera.metadata.ordering import (
    sort_columns,
    sort_constraints,
    sort_foreign_keys,
    sort_indexes,
    sort_namespaces,
    sort_tables,
    sort_triggers,
    sort_views,
)
from dera.metadata.provenance import MetadataProvenance
from dera.metadata.serialization import (
    compute_canonical_database_hash,
    serialize_canonical_database,
)
from dera.metadata.validation import validate_canonical_database

__all__ = [
    "CANONICAL_METADATA_CONTRACT_VERSION",
    "CanonicalColumn",
    "CanonicalConstraint",
    "CanonicalDatabase",
    "CanonicalForeignKey",
    "CanonicalIndex",
    "CanonicalIndexTerm",
    "CanonicalNamespace",
    "CanonicalTable",
    "CanonicalTrigger",
    "CanonicalTypeCategory",
    "CanonicalView",
    "ConstraintType",
    "DuplicateIdentityError",
    "ForeignKeyAction",
    "ForeignKeyMapping",
    "GenerationMode",
    "IdentityConflictError",
    "IdentityScope",
    "IndexType",
    "InvalidConnectorMetadataError",
    "InvalidReferenceError",
    "MetadataCompleteness",
    "MetadataLimitExceededError",
    "MetadataNormalizationError",
    "MetadataNormalizer",
    "MetadataProvenance",
    "MetadataSerializationError",
    "MissingRequiredMetadataError",
    "ObjectKind",
    "TableType",
    "TriggerEvent",
    "TriggerTiming",
    "UnsupportedMappingError",
    "compute_canonical_database_hash",
    "compute_stable_object_id",
    "generate_unnamed_constraint_name",
    "serialize_canonical_database",
    "sort_columns",
    "sort_constraints",
    "sort_foreign_keys",
    "sort_indexes",
    "sort_namespaces",
    "sort_tables",
    "sort_triggers",
    "sort_views",
    "validate_canonical_database",
]
