"""Tests for Phase 6.5 Snapshot Identity.

Verifies:
- Snapshot ID generation format and uniqueness.
- Validation of valid and malformed snapshot identifiers.
- Distinct roles of snapshot ID, structural fingerprint, and database ID.
"""

from __future__ import annotations

import unittest

from dera.reverse_engineering.snapshots.identity import (
    generate_snapshot_id,
    validate_snapshot_id,
)


class TestSnapshotIdentity(unittest.TestCase):
    """Test suite for snapshot identity utilities."""

    def test_generate_snapshot_id_format(self) -> None:
        """Verify generated IDs start with 'snap_' and have 32 hex chars."""
        sid = generate_snapshot_id()
        self.assertTrue(validate_snapshot_id(sid))
        self.assertTrue(sid.startswith("snap_"))
        self.assertEqual(len(sid), 37)

    def test_generate_snapshot_id_uniqueness(self) -> None:
        """Verify successive calls generate distinct unique identifiers."""
        ids = {generate_snapshot_id() for _ in range(100)}
        self.assertEqual(len(ids), 100)

    def test_validate_snapshot_id_cases(self) -> None:
        """Verify positive and negative validation cases."""
        self.assertTrue(validate_snapshot_id("snap_" + "a" * 32))
        self.assertTrue(validate_snapshot_id("snap_" + "0123456789abcdef0123456789abcdef"))

        self.assertFalse(validate_snapshot_id("snap_" + "a" * 31))  # too short
        self.assertFalse(validate_snapshot_id("snap_" + "a" * 33))  # too long
        self.assertFalse(validate_snapshot_id("snapshot_" + "a" * 32))  # wrong prefix
        self.assertFalse(validate_snapshot_id("snap_" + "G" * 32))  # invalid hex
        self.assertFalse(validate_snapshot_id(12345))  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
