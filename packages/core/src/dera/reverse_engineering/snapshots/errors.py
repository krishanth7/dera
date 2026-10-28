"""DERA Reverse Engineering — Phase 6.5 Snapshot Error Taxonomy.

Defines strongly typed, categorized exceptions for snapshot construction, canonicalization,
serialization, fingerprint verification, storage, and retention.
"""

from __future__ import annotations


class SnapshotError(Exception):
    """Base exception for all DERA snapshot-related errors."""


class SnapshotValidationError(SnapshotError):
    """Raised when a snapshot violates contract validation rules or integrity checks."""


class SnapshotIntegrityError(SnapshotError):
    """Raised when snapshot integrity check fails or content has been modified."""


class SnapshotFingerprintMismatchError(SnapshotIntegrityError):
    """Raised specifically when a re-computed fingerprint does not match the recorded digest."""

    def __init__(self, expected: str, actual: str, message: str | None = None) -> None:
        self.expected = expected
        self.actual = actual
        super().__init__(
            message
            or f"Structural fingerprint mismatch: expected '{expected}', computed '{actual}'."
        )


class SnapshotSerializationError(SnapshotError):
    """Raised when canonical serialization or deserialization fails."""


class SnapshotDeserializationError(SnapshotSerializationError):
    """Raised when parsing or validating serialized snapshot data fails."""


class SnapshotStorageError(SnapshotError):
    """Raised when storage operations (save, get, list, delete) fail."""


class SnapshotNotFoundError(SnapshotStorageError):
    """Raised when a requested snapshot is not found in storage."""

    def __init__(self, snapshot_id: str, workspace_id: str) -> None:
        self.snapshot_id = snapshot_id
        self.workspace_id = workspace_id
        super().__init__(f"Snapshot '{snapshot_id}' not found in workspace '{workspace_id}'.")


class SnapshotUnauthorizedError(SnapshotStorageError):
    """Raised when an operation attempts to access or mutate a snapshot outside authorized workspace boundaries."""


class SnapshotResourceLimitError(SnapshotError):
    """Raised when a snapshot exceeds configured memory, object count, or byte size bounds."""


class SnapshotIncompatibleVersionError(SnapshotError):
    """Raised when attempting to process an unsupported snapshot contract or format version."""


class SnapshotRetentionPolicyError(SnapshotError):
    """Raised when retention policy evaluation or execution violates constraints."""
