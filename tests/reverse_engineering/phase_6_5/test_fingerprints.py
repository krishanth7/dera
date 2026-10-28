"""Tests for Phase 6.5 Deterministic Cryptographic Fingerprints.

Verifies:
- Domain separation prefix binding.
- SHA-256 lowercase 64-hex format.
- Invariance to volatile envelope fields (timestamps, workspace_id, tags).
- Hash sensitivity to any structural change.
"""

from __future__ import annotations

import unittest
from datetime import UTC, datetime

from dera.reverse_engineering.builder import SchemaBuilder
from dera.reverse_engineering.snapshots.builder import SchemaSnapshotBuilder
from dera.reverse_engineering.snapshots.fingerprints import (
    validate_fingerprint_format,
)
from dera.reverse_engineering.snapshots.models import FINGERPRINT_DOMAIN

from tests.reverse_engineering.phase_6_5.fixtures import (
    make_empty_database,
    make_single_table_database,
)


class TestSnapshotFingerprints(unittest.TestCase):
    """Test suite for snapshot fingerprinting and hashing."""

    def test_fingerprint_format_valid(self) -> None:
        """Verify format validation for 64-character hex digests."""
        self.assertTrue(validate_fingerprint_format("0" * 64))
        self.assertTrue(validate_fingerprint_format("abcdef0123456789" * 4))
        self.assertFalse(validate_fingerprint_format("0" * 63))  # too short
        self.assertFalse(validate_fingerprint_format("0" * 65))  # too long
        self.assertFalse(validate_fingerprint_format("ABCDEF" + "0" * 58))  # uppercase invalid
        self.assertFalse(validate_fingerprint_format("xyz" * 21 + "0"))  # invalid hex

    def test_fingerprint_invariance_to_envelope_metadata(self) -> None:
        """Verify fingerprints are invariant to capture timestamp, tags, and workspace."""
        db = make_single_table_database()
        schema = SchemaBuilder.from_canonical_database(db)

        snap1 = SchemaSnapshotBuilder.from_analysis(
            schema=schema,
            workspace_id="ws_1",
            snapshot_id="snap_11111111111111111111111111111111",
            capture_timestamp=datetime(2025, 1, 1, tzinfo=UTC),
            tags={"env": "dev"},
        )
        snap2 = SchemaSnapshotBuilder.from_analysis(
            schema=schema,
            workspace_id="ws_2",
            snapshot_id="snap_22222222222222222222222222222222",
            capture_timestamp=datetime(2027, 12, 31, tzinfo=UTC),
            tags={"env": "prod", "criticality": "high"},
        )

        self.assertEqual(snap1.fingerprint, snap2.fingerprint)
        self.assertEqual(snap1.fingerprint_domain, FINGERPRINT_DOMAIN)
        self.assertTrue(validate_fingerprint_format(snap1.fingerprint))

    def test_fingerprint_sensitivity_to_structural_change(self) -> None:
        """Verify that altering table names or columns changes the structural fingerprint."""
        db1 = make_single_table_database(name="test_db")
        db2 = make_empty_database(name="test_db")

        snap1 = SchemaSnapshotBuilder.from_analysis(SchemaBuilder.from_canonical_database(db1))
        snap2 = SchemaSnapshotBuilder.from_analysis(SchemaBuilder.from_canonical_database(db2))

        self.assertNotEqual(snap1.fingerprint, snap2.fingerprint)


if __name__ == "__main__":
    unittest.main()
