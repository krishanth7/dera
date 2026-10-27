"""Tests for DERA Deterministic Ordering algorithms."""

from __future__ import annotations

import unittest

from dera.metadata.enums import CanonicalTypeCategory
from dera.metadata.models import (
    CanonicalColumn,
    CanonicalIndex,
    CanonicalTable,
)
from dera.metadata.ordering import (
    sort_columns,
    sort_indexes,
    sort_tables,
)
from dera.metadata.provenance import MetadataProvenance


class TestOrdering(unittest.TestCase):
    """Test suite ensuring deterministic sorting across metadata collections."""

    def setUp(self) -> None:
        self.prov = MetadataProvenance(
            source_engine="sqlite",
            native_identifier="test",
        )

    def test_sort_columns_by_ordinal_and_name(self) -> None:
        """Verify columns sort strictly by ordinal position first, then name."""
        c1 = CanonicalColumn(
            id="col1",
            parent_table_id="tbl1",
            name="z_name",
            ordinal_position=1,
            native_data_type="TEXT",
            canonical_type=CanonicalTypeCategory.TEXT,
            provenance=self.prov,
        )
        c2 = CanonicalColumn(
            id="col2",
            parent_table_id="tbl1",
            name="a_name",
            ordinal_position=1,
            native_data_type="TEXT",
            canonical_type=CanonicalTypeCategory.TEXT,
            provenance=self.prov,
        )
        c3 = CanonicalColumn(
            id="col3",
            parent_table_id="tbl1",
            name="id",
            ordinal_position=2,
            native_data_type="INTEGER",
            canonical_type=CanonicalTypeCategory.INTEGER,
            provenance=self.prov,
        )
        sorted_cols = sort_columns([c3, c1, c2])
        self.assertEqual([c.name for c in sorted_cols], ["a_name", "z_name", "id"])

    def test_sort_tables_alphabetical(self) -> None:
        """Verify tables sort alphabetically regardless of input ordering."""
        t1 = CanonicalTable(
            id="t1",
            namespace_id="ns1",
            name="users",
            provenance=self.prov,
        )
        t2 = CanonicalTable(
            id="t2",
            namespace_id="ns1",
            name="accounts",
            provenance=self.prov,
        )
        t3 = CanonicalTable(
            id="t3",
            namespace_id="ns1",
            name="orders",
            provenance=self.prov,
        )
        sorted_tbls = sort_tables([t1, t2, t3])
        self.assertEqual([t.name for t in sorted_tbls], ["accounts", "orders", "users"])

    def test_sort_indexes_primary_first_then_unique(self) -> None:
        """Verify indexes sort primary first, unique second, then alphabetical."""
        idx_normal = CanonicalIndex(
            id="idx1",
            parent_table_id="t1",
            name="idx_users_email",
            is_unique=False,
            is_primary=False,
            terms=(),
            provenance=self.prov,
        )
        idx_unique = CanonicalIndex(
            id="idx2",
            parent_table_id="t1",
            name="idx_users_username",
            is_unique=True,
            is_primary=False,
            terms=(),
            provenance=self.prov,
        )
        idx_pk = CanonicalIndex(
            id="idx3",
            parent_table_id="t1",
            name="pk_users",
            is_unique=True,
            is_primary=True,
            terms=(),
            provenance=self.prov,
        )
        sorted_idxs = sort_indexes([idx_normal, idx_unique, idx_pk])
        self.assertEqual(
            [i.name for i in sorted_idxs], ["pk_users", "idx_users_username", "idx_users_email"]
        )


if __name__ == "__main__":
    unittest.main()
