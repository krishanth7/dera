"""DERA Comparison — Phase 9.1 Root Package Initialization.

Exposes the primary comparison engine, models, enums, exceptions, and contracts.
"""

from __future__ import annotations

from dera.comparison.contracts import SchemaComparisonEngineProtocol
from dera.comparison.engine import SchemaComparisonEngine
from dera.comparison.enums import (
    ComparisonChangeType,
    ComparisonObjectType,
    ComparisonStatus,
    DiffGranularity,
    PropertyComparisonStatus,
)
from dera.comparison.errors import (
    ComparisonError,
    ComparisonResourceLimitExceededError,
    IncompatibleSnapshotError,
    InvalidSnapshotError,
    MissingMetadataError,
    UnsupportedEngineComparisonError,
)
from dera.comparison.evidence import ObjectEvidence, PropertyDifference
from dera.comparison.limits import ComparisonResourceLimits
from dera.comparison.models import (
    COMPARATOR_ENGINE_VERSION,
    ComparisonConfig,
    ComparisonReport,
    ComparisonSummary,
    SchemaChange,
)
from dera.comparison.serializers import dumps_canonical_bytes, dumps_canonical_json

__all__ = [
    "COMPARATOR_ENGINE_VERSION",
    "ComparisonChangeType",
    "ComparisonConfig",
    "ComparisonError",
    "ComparisonObjectType",
    "ComparisonReport",
    "ComparisonResourceLimitExceededError",
    "ComparisonResourceLimits",
    "ComparisonStatus",
    "ComparisonSummary",
    "DiffGranularity",
    "IncompatibleSnapshotError",
    "InvalidSnapshotError",
    "MissingMetadataError",
    "ObjectEvidence",
    "PropertyComparisonStatus",
    "PropertyDifference",
    "SchemaChange",
    "SchemaComparisonEngine",
    "SchemaComparisonEngineProtocol",
    "UnsupportedEngineComparisonError",
    "dumps_canonical_bytes",
    "dumps_canonical_json",
]
