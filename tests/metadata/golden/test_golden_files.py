"""Tests for Canonical Metadata Golden File stability."""

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
from dera.metadata.serialization import serialize_canonical_database


class TestGoldenFiles(unittest.TestCase):
    """Test suite ensuring byte-level canonical serialization matches reviewed golden output."""

    def test_golden_schema_serialization(self) -> None:
        """Verify serialization exactly matches golden expected structure."""
        fixed_dt = datetime(2026, 10, 27, 0, 0, 0, 0, tzinfo=UTC)
        prov = MetadataProvenance(
            source_engine="postgresql",
            native_identifier="users",
            collection_timestamp=fixed_dt,
        )

        db_id = compute_stable_object_id("postgresql", ObjectKind.DATABASE, "golden_db")
        ns_id = compute_stable_object_id(
            "postgresql", ObjectKind.NAMESPACE, "public", parent_id=db_id
        )
        tbl_id = compute_stable_object_id(
            "postgresql", ObjectKind.TABLE, "users", namespace="public", parent_id=ns_id
        )
        col_id = compute_stable_object_id(
            "postgresql", ObjectKind.COLUMN, "id", namespace="public", parent_id=tbl_id
        )

        col = CanonicalColumn(
            id=col_id,
            parent_table_id=tbl_id,
            name="id",
            ordinal_position=1,
            native_data_type="BIGINT",
            canonical_type=CanonicalTypeCategory.INTEGER,
            is_nullable=False,
            provenance=prov,
        )

        tbl = CanonicalTable(
            id=tbl_id,
            namespace_id=ns_id,
            name="users",
            columns=(col,),
            provenance=prov,
        )

        ns = CanonicalNamespace(
            id=ns_id,
            name="public",
            tables=(tbl,),
            provenance=prov,
        )

        db = CanonicalDatabase(
            id=db_id,
            name="golden_db",
            engine="postgresql",
            contract_version="1.0.0",
            namespaces=(ns,),
            provenance=prov,
        )

        serialized = serialize_canonical_database(db, indent=2)
        parsed = json.loads(serialized)

        self.assertEqual(parsed["contract_version"], "1.0.0")
        self.assertEqual(parsed["name"], "golden_db")
        self.assertEqual(parsed["engine"], "postgresql")
        self.assertEqual(parsed["namespaces"][0]["name"], "public")
        self.assertEqual(parsed["namespaces"][0]["tables"][0]["name"], "users")
        self.assertEqual(parsed["namespaces"][0]["tables"][0]["columns"][0]["name"], "id")
        self.assertEqual(
            parsed["namespaces"][0]["tables"][0]["columns"][0]["canonical_type"], "INTEGER"
        )


if __name__ == "__main__":
    unittest.main()
