"""DERA Reverse Engineering — Phase 6.5 Snapshot Integrity Verification.

Provides independent cryptographic integrity verification for SchemaSnapshot instances
by re-computing the domain-separated SHA-256 fingerprint from the canonical structural payload
and comparing it against the recorded fingerprint.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from dera.reverse_engineering.snapshots.fingerprints import (
    compute_structural_fingerprint,
    validate_fingerprint_format,
)
from dera.reverse_engineering.snapshots.limits import SnapshotResourceLimits
from dera.reverse_engineering.snapshots.models import (
    FINGERPRINT_ALGORITHM_NAME,
    FINGERPRINT_DOMAIN,
    SNAPSHOT_FORMAT_VERSION,
    SchemaSnapshot,
)


class IntegrityVerificationStatus(StrEnum):
    """Categorized result of a snapshot integrity verification check."""

    VALID = "valid"
    MISMATCH = "mismatch"
    UNSUPPORTED_VERSION = "unsupported_version"
    INVALID_PAYLOAD = "invalid_payload"
    VERIFICATION_ERROR = "verification_error"


class SnapshotIntegrityReport(BaseModel):
    """Typed evaluation report describing snapshot verification findings."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    status: IntegrityVerificationStatus = Field(description="Integrity status code.")
    is_valid: bool = Field(description="True if snapshot is cryptographically intact and verified.")
    expected_fingerprint: str = Field(description="Recorded fingerprint on the snapshot envelope.")
    computed_fingerprint: str | None = Field(
        default=None,
        description="Freshly re-computed structural fingerprint.",
    )
    details: str = Field(description="Diagnostic explanation of verification outcome.")


def verify_snapshot_integrity(
    snapshot: SchemaSnapshot,
    limits: SnapshotResourceLimits | None = None,
) -> SnapshotIntegrityReport:
    """Verify that a SchemaSnapshot's recorded fingerprint matches its actual structural content.

    Args:
        snapshot: SchemaSnapshot to evaluate.
        limits: Optional resource limits.

    Returns:
        SnapshotIntegrityReport detailing whether the snapshot is authentic and uncorrupted.
    """
    # 1. Format version check
    if snapshot.format_version != SNAPSHOT_FORMAT_VERSION:
        return SnapshotIntegrityReport(
            status=IntegrityVerificationStatus.UNSUPPORTED_VERSION,
            is_valid=False,
            expected_fingerprint=snapshot.fingerprint,
            computed_fingerprint=None,
            details=(
                f"Unsupported snapshot format version '{snapshot.format_version}'. "
                f"Current supported version is '{SNAPSHOT_FORMAT_VERSION}'."
            ),
        )

    # 2. Algorithm & Domain separation check
    if snapshot.fingerprint_algorithm != FINGERPRINT_ALGORITHM_NAME:
        return SnapshotIntegrityReport(
            status=IntegrityVerificationStatus.UNSUPPORTED_VERSION,
            is_valid=False,
            expected_fingerprint=snapshot.fingerprint,
            computed_fingerprint=None,
            details=f"Unsupported fingerprint algorithm '{snapshot.fingerprint_algorithm}'.",
        )

    if snapshot.fingerprint_domain != FINGERPRINT_DOMAIN:
        return SnapshotIntegrityReport(
            status=IntegrityVerificationStatus.UNSUPPORTED_VERSION,
            is_valid=False,
            expected_fingerprint=snapshot.fingerprint,
            computed_fingerprint=None,
            details=f"Unsupported fingerprint domain '{snapshot.fingerprint_domain}'.",
        )

    # 3. Format validation
    if not validate_fingerprint_format(snapshot.fingerprint):
        return SnapshotIntegrityReport(
            status=IntegrityVerificationStatus.INVALID_PAYLOAD,
            is_valid=False,
            expected_fingerprint=snapshot.fingerprint,
            computed_fingerprint=None,
            details="Recorded fingerprint is not a valid 64-character hex SHA-256 digest.",
        )

    # 4. Recompute structural fingerprint
    try:
        computed = compute_structural_fingerprint(snapshot.payload, limits=limits)
        if computed == snapshot.fingerprint.lower():
            return SnapshotIntegrityReport(
                status=IntegrityVerificationStatus.VALID,
                is_valid=True,
                expected_fingerprint=snapshot.fingerprint,
                computed_fingerprint=computed,
                details="Structural fingerprint matches canonical payload bytes exactly.",
            )

        return SnapshotIntegrityReport(
            status=IntegrityVerificationStatus.MISMATCH,
            is_valid=False,
            expected_fingerprint=snapshot.fingerprint,
            computed_fingerprint=computed,
            details=(
                f"Structural fingerprint mismatch: expected '{snapshot.fingerprint}', "
                f"computed '{computed}'. Structural content may have been modified."
            ),
        )
    except Exception as exc:
        return SnapshotIntegrityReport(
            status=IntegrityVerificationStatus.VERIFICATION_ERROR,
            is_valid=False,
            expected_fingerprint=snapshot.fingerprint,
            computed_fingerprint=None,
            details=f"Error during integrity verification: {exc}",
        )
