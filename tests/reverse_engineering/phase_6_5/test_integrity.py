"""Tests for Phase 6.5 Snapshot Integrity Verification.

Verifies:
- Detection of authentic, unmodified snapshots (status=VALID).
- Detection of fingerprint mismatches when payload or digest is altered (status=MISMATCH).
- Handling of unsupported format versions or algorithm domains.
- Diagnostic reporting with detailed explanations.
"""

from __future__ import annotations

import unittest

from dera.reverse_engineering.snapshots.integrity import (
    IntegrityVerificationStatus,
    verify_snapshot_integrity,
)
from dera.reverse_engineering.snapshots.models import (
    SnapshotTablePayload,
)

from tests.reverse_engineering.phase_6_5.fixtures import (
    build_snapshot_from_database,
    make_single_table_database,
)


class TestSnapshotIntegrity(unittest.TestCase):
    """Test suite for snapshot integrity verification."""

    def setUp(self) -> None:
        db = make_single_table_database()
        self.snapshot = build_snapshot_from_database(db)

    def test_authentic_snapshot_passes_verification(self) -> None:
        """Verify an unmodified snapshot passes integrity verification."""
        report = verify_snapshot_integrity(self.snapshot)
        self.assertEqual(report.status, IntegrityVerificationStatus.VALID)
        self.assertTrue(report.is_valid)
        self.assertEqual(report.expected_fingerprint, self.snapshot.fingerprint)
        self.assertEqual(report.computed_fingerprint, self.snapshot.fingerprint)

    def test_fingerprint_mismatch_detected(self) -> None:
        """Verify modifying the recorded fingerprint triggers MISMATCH."""
        tampered_snapshot = self.snapshot.model_copy(update={"fingerprint": "f" * 64})
        report = verify_snapshot_integrity(tampered_snapshot)
        self.assertEqual(report.status, IntegrityVerificationStatus.MISMATCH)
        self.assertFalse(report.is_valid)
        self.assertEqual(report.expected_fingerprint, "f" * 64)
        self.assertEqual(report.computed_fingerprint, self.snapshot.fingerprint)

    def test_tampered_structural_payload_detected(self) -> None:
        """Verify modifying the structural payload triggers MISMATCH."""
        tampered_table = SnapshotTablePayload(
            table_id="tbl:tampered",
            namespace="public",
            name="injected_table",
        )
        tampered_payload = self.snapshot.payload.model_copy(update={"tables": (tampered_table,)})
        tampered_snapshot = self.snapshot.model_copy(update={"payload": tampered_payload})

        report = verify_snapshot_integrity(tampered_snapshot)
        self.assertEqual(report.status, IntegrityVerificationStatus.MISMATCH)
        self.assertFalse(report.is_valid)
        self.assertNotEqual(report.computed_fingerprint, self.snapshot.fingerprint)

    def test_unsupported_format_version(self) -> None:
        """Verify unsupported snapshot format versions are flagged."""
        unsupported_snapshot = self.snapshot.model_copy(
            update={"format_version": "dera.schema.snapshot.v999"}
        )
        report = verify_snapshot_integrity(unsupported_snapshot)
        self.assertEqual(report.status, IntegrityVerificationStatus.UNSUPPORTED_VERSION)
        self.assertFalse(report.is_valid)

    def test_unsupported_domain_separation(self) -> None:
        """Verify unknown domain separation strings are rejected."""
        unsupported_domain = self.snapshot.model_copy(
            update={"fingerprint_domain": "CORRUPT:DOMAIN:V1"}
        )
        report = verify_snapshot_integrity(unsupported_domain)
        self.assertEqual(report.status, IntegrityVerificationStatus.UNSUPPORTED_VERSION)
        self.assertFalse(report.is_valid)


if __name__ == "__main__":
    unittest.main()
