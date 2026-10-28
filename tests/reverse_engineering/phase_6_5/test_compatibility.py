"""Tests for Phase 6.5 Snapshot Compatibility & Equivalence.

Verifies:
- Format version support checks.
- Equivalence level classifications (EXACT_BYTE_IDENTICAL vs STRUCTURAL_FINGERPRINT_MATCH vs NONE).
- Cross-version compatibility boundaries.
"""

from __future__ import annotations

import unittest

from dera.reverse_engineering.snapshots.compatibility import (
    EquivalenceLevel,
    SnapshotCompatibilityChecker,
)
from dera.reverse_engineering.snapshots.models import (
    SNAPSHOT_FORMAT_VERSION,
)

from tests.reverse_engineering.phase_6_5.fixtures import (
    build_snapshot_from_database,
    make_empty_database,
    make_single_table_database,
)


class TestSnapshotCompatibility(unittest.TestCase):
    """Test suite for snapshot version compatibility and equivalence levels."""

    def setUp(self) -> None:
        self.db1 = make_single_table_database()
        self.db2 = make_empty_database()

    def test_version_support_check(self) -> None:
        """Verify recognized vs unsupported format versions."""
        self.assertTrue(SnapshotCompatibilityChecker.is_version_supported(SNAPSHOT_FORMAT_VERSION))
        self.assertTrue(SnapshotCompatibilityChecker.is_version_supported("1.0.0"))
        self.assertFalse(SnapshotCompatibilityChecker.is_version_supported("9.9.9"))
        self.assertFalse(SnapshotCompatibilityChecker.is_version_supported("invalid.version"))

    def test_exact_byte_identical_equivalence(self) -> None:
        """Verify identical snapshots evaluate to EXACT_BYTE_IDENTICAL."""
        snap = build_snapshot_from_database(self.db1)
        level = SnapshotCompatibilityChecker.compare_snapshots(snap, snap)
        self.assertEqual(level, EquivalenceLevel.EXACT_BYTE_IDENTICAL)

    def test_structural_fingerprint_match_equivalence(self) -> None:
        """Verify same structural content but different envelopes evaluate to STRUCTURAL_FINGERPRINT_MATCH."""
        snap_a = build_snapshot_from_database(
            self.db1,
            snapshot_id="snap_" + "a" * 32,
            tags={"env": "dev"},
        )
        snap_b = build_snapshot_from_database(
            self.db1,
            snapshot_id="snap_" + "b" * 32,
            tags={"env": "prod"},
        )

        level = SnapshotCompatibilityChecker.compare_snapshots(snap_a, snap_b)
        self.assertEqual(level, EquivalenceLevel.STRUCTURAL_FINGERPRINT_MATCH)

    def test_distinct_schemas_equivalence_none(self) -> None:
        """Verify different schemas evaluate to NONE."""
        snap_tbl = build_snapshot_from_database(self.db1)
        snap_empty = build_snapshot_from_database(self.db2)

        level = SnapshotCompatibilityChecker.compare_snapshots(snap_tbl, snap_empty)
        self.assertEqual(level, EquivalenceLevel.NONE)


if __name__ == "__main__":
    unittest.main()
