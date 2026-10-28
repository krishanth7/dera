"""DERA Reverse Engineering — Phase 6.5 Schema Snapshots & Deterministic Fingerprints.

Production subsystem for capturing, canonicalizing, fingerprinting, storing,
and verifying immutable schema snapshots.
"""

from __future__ import annotations

from dera.reverse_engineering.snapshots.builder import SchemaSnapshotBuilder
from dera.reverse_engineering.snapshots.canonicalization import (
    canonicalize_structural_payload,
)
from dera.reverse_engineering.snapshots.compatibility import (
    EquivalenceLevel,
    SnapshotCompatibilityChecker,
)
from dera.reverse_engineering.snapshots.errors import (
    SnapshotDeserializationError,
    SnapshotError,
    SnapshotFingerprintMismatchError,
    SnapshotIncompatibleVersionError,
    SnapshotIntegrityError,
    SnapshotNotFoundError,
    SnapshotResourceLimitError,
    SnapshotRetentionPolicyError,
    SnapshotSerializationError,
    SnapshotStorageError,
    SnapshotUnauthorizedError,
    SnapshotValidationError,
)
from dera.reverse_engineering.snapshots.fingerprints import (
    compute_snapshot_envelope_hash,
    compute_structural_fingerprint,
    validate_fingerprint_format,
)
from dera.reverse_engineering.snapshots.identity import (
    generate_snapshot_id,
    validate_snapshot_id,
)
from dera.reverse_engineering.snapshots.integrity import (
    IntegrityVerificationStatus,
    SnapshotIntegrityReport,
    verify_snapshot_integrity,
)
from dera.reverse_engineering.snapshots.limits import SnapshotResourceLimits
from dera.reverse_engineering.snapshots.models import (
    FINGERPRINT_ALGORITHM_NAME,
    FINGERPRINT_CONTRACT_VERSION,
    FINGERPRINT_DOMAIN,
    SNAPSHOT_FORMAT_VERSION,
    SchemaSnapshot,
    SnapshotCheckConstraintPayload,
    SnapshotColumnPayload,
    SnapshotDependencySummary,
    SnapshotEnvelope,
    SnapshotForeignKeyPayload,
    SnapshotIndexPayload,
    SnapshotPrimaryKeyPayload,
    SnapshotRelationshipPayload,
    SnapshotStructuralPayload,
    SnapshotTablePayload,
    SnapshotTriggerPayload,
    SnapshotUniqueConstraintPayload,
    SnapshotViewPayload,
)
from dera.reverse_engineering.snapshots.provenance import (
    CaptureConsistency,
    SnapshotProvenance,
)
from dera.reverse_engineering.snapshots.repository import (
    FileSystemSnapshotStorage,
    InMemorySnapshotStorage,
)
from dera.reverse_engineering.snapshots.retention import (
    RetentionActionResult,
    RetentionEvaluationResult,
    RetentionManager,
    SnapshotRetentionPolicy,
)
from dera.reverse_engineering.snapshots.serialization import (
    deserialize_snapshot_from_json,
    deserialize_structural_payload_from_json,
    serialize_snapshot_to_json,
    serialize_structural_payload_to_bytes,
)
from dera.reverse_engineering.snapshots.storage import (
    SnapshotFilter,
    SnapshotStorage,
)
from dera.reverse_engineering.snapshots.validation import (
    validate_snapshot,
    validate_snapshot_strict,
)

__all__ = [
    # Constants
    "FINGERPRINT_ALGORITHM_NAME",
    "FINGERPRINT_CONTRACT_VERSION",
    "FINGERPRINT_DOMAIN",
    "SNAPSHOT_FORMAT_VERSION",
    # Models
    "CaptureConsistency",
    "EquivalenceLevel",
    "IntegrityVerificationStatus",
    "RetentionActionResult",
    "RetentionEvaluationResult",
    "RetentionManager",
    "SchemaSnapshot",
    "SchemaSnapshotBuilder",
    "SnapshotCheckConstraintPayload",
    "SnapshotColumnPayload",
    "SnapshotCompatibilityChecker",
    "SnapshotDependencySummary",
    "SnapshotEnvelope",
    "SnapshotFilter",
    "SnapshotForeignKeyPayload",
    "SnapshotIndexPayload",
    "SnapshotIntegrityReport",
    "SnapshotPrimaryKeyPayload",
    "SnapshotProvenance",
    "SnapshotRelationshipPayload",
    "SnapshotResourceLimits",
    "SnapshotRetentionPolicy",
    "SnapshotStorage",
    "SnapshotStructuralPayload",
    "SnapshotTablePayload",
    "SnapshotTriggerPayload",
    "SnapshotUniqueConstraintPayload",
    "SnapshotViewPayload",
    # Storage
    "FileSystemSnapshotStorage",
    "InMemorySnapshotStorage",
    # Functions
    "canonicalize_structural_payload",
    "compute_snapshot_envelope_hash",
    "compute_structural_fingerprint",
    "deserialize_snapshot_from_json",
    "deserialize_structural_payload_from_json",
    "generate_snapshot_id",
    "serialize_snapshot_to_json",
    "serialize_structural_payload_to_bytes",
    "validate_fingerprint_format",
    "validate_snapshot",
    "validate_snapshot_id",
    "validate_snapshot_strict",
    "verify_snapshot_integrity",
    # Exceptions
    "SnapshotDeserializationError",
    "SnapshotError",
    "SnapshotFingerprintMismatchError",
    "SnapshotIncompatibleVersionError",
    "SnapshotIntegrityError",
    "SnapshotNotFoundError",
    "SnapshotResourceLimitError",
    "SnapshotRetentionPolicyError",
    "SnapshotSerializationError",
    "SnapshotStorageError",
    "SnapshotUnauthorizedError",
    "SnapshotValidationError",
]
