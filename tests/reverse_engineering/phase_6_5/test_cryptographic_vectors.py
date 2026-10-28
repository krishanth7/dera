"""Reviewed Cryptographic SHA-256 Test Vectors for Phase 6.5.

Locks in exact byte lengths and SHA-256 digests computed over domain-separated
canonical RFC 8785 structural payload bytes.
"""

from __future__ import annotations

import unittest

from dera.reverse_engineering.snapshots.integrity import (
    IntegrityVerificationStatus,
    verify_snapshot_integrity,
)
from dera.reverse_engineering.snapshots.serialization import (
    serialize_structural_payload_to_bytes,
)

from tests.reverse_engineering.phase_6_5.fixtures import (
    build_snapshot_from_database,
    make_composite_constraints_database,
    make_empty_database,
    make_single_table_database,
    make_unicode_database,
)

# Reviewed cryptographic test vectors
VECTORS = {
    "empty_db": {
        "expected_fingerprint": "5a341218a5a6965a5c1c4e03720510e0d67d558e56abbb69528634b91017d8df",
        "expected_bytes_len": 349,
    },
    "single_tbl_db": {
        "expected_fingerprint": "0f37c68ee6534cb98f678e6bb57331ed09b898419546a06b25d2113804f12680",
        "expected_bytes_len": 1668,
    },
    "composite_db": {
        "expected_fingerprint": "e63982b1804665c416a0b71d6d129bd97b222ec70eedc616dabef0640a739eb9",
        "expected_bytes_len": 3211,
    },
    "unicode_db": {
        "expected_fingerprint": "d70235206edeebcfc5fb2566ae09162eb9c897d3c9c98ec10e87cbe399246de4",
        "expected_bytes_len": 1463,
    },
}


class TestCryptographicVectors(unittest.TestCase):
    """Test suite validating exact locked cryptographic test vectors."""

    def test_empty_database_vector(self) -> None:
        """Verify empty database SHA-256 digest and payload length."""
        db = make_empty_database()
        snap = build_snapshot_from_database(db)
        payload_bytes = serialize_structural_payload_to_bytes(snap.payload)

        vector = VECTORS["empty_db"]
        self.assertEqual(len(payload_bytes), vector["expected_bytes_len"])
        self.assertEqual(snap.fingerprint, vector["expected_fingerprint"])

        report = verify_snapshot_integrity(snap)
        self.assertEqual(report.status, IntegrityVerificationStatus.VALID)

    def test_single_table_vector(self) -> None:
        """Verify single table database SHA-256 digest and payload length."""
        db = make_single_table_database()
        snap = build_snapshot_from_database(db)
        payload_bytes = serialize_structural_payload_to_bytes(snap.payload)

        vector = VECTORS["single_tbl_db"]
        self.assertEqual(len(payload_bytes), vector["expected_bytes_len"])
        self.assertEqual(snap.fingerprint, vector["expected_fingerprint"])

        report = verify_snapshot_integrity(snap)
        self.assertEqual(report.status, IntegrityVerificationStatus.VALID)

    def test_composite_constraints_vector(self) -> None:
        """Verify composite constraints database SHA-256 digest and payload length."""
        db = make_composite_constraints_database()
        snap = build_snapshot_from_database(db)
        payload_bytes = serialize_structural_payload_to_bytes(snap.payload)

        vector = VECTORS["composite_db"]
        self.assertEqual(len(payload_bytes), vector["expected_bytes_len"])
        self.assertEqual(snap.fingerprint, vector["expected_fingerprint"])

        report = verify_snapshot_integrity(snap)
        self.assertEqual(report.status, IntegrityVerificationStatus.VALID)

    def test_unicode_database_vector(self) -> None:
        """Verify unicode database SHA-256 digest and payload length."""
        db = make_unicode_database()
        snap = build_snapshot_from_database(db)
        payload_bytes = serialize_structural_payload_to_bytes(snap.payload)

        vector = VECTORS["unicode_db"]
        self.assertEqual(len(payload_bytes), vector["expected_bytes_len"])
        self.assertEqual(snap.fingerprint, vector["expected_fingerprint"])

        report = verify_snapshot_integrity(snap)
        self.assertEqual(report.status, IntegrityVerificationStatus.VALID)


if __name__ == "__main__":
    unittest.main()
