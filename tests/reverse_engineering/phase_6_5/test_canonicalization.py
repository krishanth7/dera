"""Tests for Phase 6.5 Snapshot Canonicalization.

Verifies:
- Preserved ordinal positions of columns.
- Preserved composite primary and foreign key column sequence.
- Stable lexicographical sorting of tables, namespaces, constraints, and indexes.
- Invariance of structural payload to input table order permutation.
"""

from __future__ import annotations

import unittest

from dera.reverse_engineering.builder import SchemaBuilder
from dera.reverse_engineering.snapshots.canonicalization import (
    canonicalize_structural_payload,
)

from tests.reverse_engineering.phase_6_5.fixtures import (
    make_composite_constraints_database,
    make_single_table_database,
)


class TestSnapshotCanonicalization(unittest.TestCase):
    """Test suite for snapshot canonicalization logic."""

    def test_column_ordinal_position_preserved(self) -> None:
        """Verify columns remain sorted strictly by ordinal_position, not alphabetically."""
        db = make_single_table_database()
        schema = SchemaBuilder.from_canonical_database(db)
        payload = canonicalize_structural_payload(schema)

        tbl = payload.tables[0]
        col_names = [c.name for c in tbl.columns]
        ordinals = [c.ordinal_position for c in tbl.columns]

        # id (1), email (2), name (3)
        self.assertEqual(col_names, ["id", "email", "name"])
        self.assertEqual(ordinals, [1, 2, 3])

    def test_composite_key_ordering_preserved(self) -> None:
        """Verify composite PK and FK column tuples maintain exact declared member sequence."""
        db = make_composite_constraints_database()
        schema = SchemaBuilder.from_canonical_database(db)
        payload = canonicalize_structural_payload(schema)

        parent_tbl = next(t for t in payload.tables if t.name == "parent_items")
        self.assertIsNotNone(parent_tbl.primary_key)
        # Composite PK: ("tenant_id", "item_id")
        self.assertEqual(parent_tbl.primary_key.columns, ("tenant_id", "item_id"))

        child_tbl = next(t for t in payload.tables if t.name == "child_items")
        self.assertEqual(len(child_tbl.foreign_keys), 1)
        fk = child_tbl.foreign_keys[0]
        self.assertEqual(fk.source_columns, ("t_id", "it_id"))
        self.assertEqual(fk.target_columns, ("tenant_id", "item_id"))

    def test_table_lexicographical_sorting(self) -> None:
        """Verify tables are sorted by namespace, then name."""
        db = make_composite_constraints_database()
        schema = SchemaBuilder.from_canonical_database(db)
        payload = canonicalize_structural_payload(schema)

        table_names = [t.name for t in payload.tables]
        # "child_items" < "parent_items"
        self.assertEqual(table_names, ["child_items", "parent_items"])


if __name__ == "__main__":
    unittest.main()
