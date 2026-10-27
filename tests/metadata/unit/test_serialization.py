"""Tests for Canonical Database serialization and hashing."""

from __future__ import annotations

import json
import unittest
from datetime import UTC, datetime

from dera.metadata.enums import CanonicalTypeCategory, ObjectKind
from dera.metadata.identity import compute_stable_object_id
from dera.metadata.models import (
    CanonicalColumn,
    CanonicalDatabase,
    CanonicalNamespace,
    CanonicalTable,
)
from dera.metadata.provenance import MetadataProvenance
from dera.metadata.serialization import (
    compute_canonical_database_hash,
    serialize_canonical_database,
)


class TestSerialization(unittest.TestCase):
    """Test suite ensuring deterministic JSON serialization and hashing."""

    def setUp(self) -> None:
        self.fixed_dt = datetime(2026, 10, 27, 12, 0, 0, 0, tzinfo=UTC)
        self.prov = MetadataProvenance(
            source_engine="sqlite",
            native_identifier="users",
            collection_timestamp=self.fixed_dt,
        )

        db_id = compute_stable_object_id("sqlite", ObjectKind.DATABASE, "main")
        ns_id = compute_stable_object_id("sqlite", ObjectKind.NAMESPACE, "main", parent_id=db_id)
        tbl_id = compute_stable_object_id("sqlite", ObjectKind.TABLE, "users", parent_id=ns_id)
        col_id = compute_stable_object_id("sqlite", ObjectKind.COLUMN, "id", parent_id=tbl_id)

        col = CanonicalColumn(
            id=col_id,
            parent_table_id=tbl_id,
            name="id",
            ordinal_position=1,
            native_data_type="INTEGER",
            canonical_type=CanonicalTypeCategory.INTEGER,
            provenance=self.prov,
        )

        tbl = CanonicalTable(
            id=tbl_id,
            namespace_id=ns_id,
            name="users",
            columns=(col,),
            provenance=self.prov,
        )

        ns = CanonicalNamespace(
            id=ns_id,
            name="main",
            tables=(tbl,),
            provenance=self.prov,
        )

        self.db = CanonicalDatabase(
            id=db_id,
            name="main",
            engine="sqlite",
            namespaces=(ns,),
            provenance=self.prov,
        )

    def test_deterministic_json_output(self) -> None:
        """Verify serialization is deterministic across repeated runs."""
        json1 = serialize_canonical_database(self.db)
        json2 = serialize_canonical_database(self.db)
        self.assertEqual(json1, json2)

        parsed = json.loads(json1)
        self.assertEqual(parsed["contract_version"], "1.0.0")
        self.assertEqual(parsed["engine"], "sqlite")
        self.assertEqual(len(parsed["namespaces"]), 1)

    def test_canonical_hash_stability(self) -> None:
        """Verify hash is 64 hex characters and identical for equal structures."""
        h1 = compute_canonical_database_hash(self.db)
        h2 = compute_canonical_database_hash(self.db)
        self.assertEqual(h1, h2)
        self.assertEqual(len(h1), 64)


if __name__ == "__main__":
    unittest.main()
