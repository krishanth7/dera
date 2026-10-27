"""DERA Canonical Metadata Normalization & Identity — Contracts.

Public metadata contract definitions, versioning constants, and specification exports.
"""

from __future__ import annotations

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
from dera.metadata.provenance import MetadataProvenance

CANONICAL_METADATA_CONTRACT_VERSION: str = "1.0.0"

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
    "ForeignKeyAction",
    "ForeignKeyMapping",
    "GenerationMode",
    "IdentityScope",
    "IndexType",
    "MetadataCompleteness",
    "MetadataProvenance",
    "ObjectKind",
    "TableType",
    "TriggerEvent",
    "TriggerTiming",
]
