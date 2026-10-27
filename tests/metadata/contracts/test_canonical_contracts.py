"""Tests for Canonical Metadata Contracts and Immutability."""

from __future__ import annotations

import unittest

from dera.metadata.contracts import (
    CANONICAL_METADATA_CONTRACT_VERSION,
    CanonicalColumn,
    CanonicalDatabase,
    CanonicalNamespace,
    CanonicalTable,
    CanonicalTypeCategory,
)
from dera.metadata.enums import ObjectKind
from dera.metadata.identity import compute_stable_object_id
from dera.metadata.provenance import MetadataProvenance
from pydantic import ValidationError


class TestCanonicalContracts(unittest.TestCase):
    """Test suite ensuring contract versioning and model immutability."""

    def setUp(self) -> None:
        self.prov = MetadataProvenance(
            source_engine="postgresql",
            native_identifier="users",
        )
        self.col = CanonicalColumn(
            id="col1",
            parent_table_id="t1",
            name="email",
            ordinal_position=1,
            native_data_type="VARCHAR(255)",
            canonical_type=CanonicalTypeCategory.TEXT,
            provenance=self.prov,
        )

    def test_contract_version(self) -> None:
        """Verify the public canonical contract version is 1.0.0."""
        self.assertEqual(CANONICAL_METADATA_CONTRACT_VERSION, "1.0.0")

    def test_model_immutability(self) -> None:
        """Verify models are frozen and reject mutation attempts."""
        with self.assertRaises(ValidationError):
            # Attempting to assign to a field on frozen Pydantic model
            self.col.name = "new_name"  # type: ignore[misc]

    def test_canonical_database_helper_methods(self) -> None:
        """Verify table discovery helper methods on CanonicalDatabase."""
        tbl_id = compute_stable_object_id("postgresql", ObjectKind.TABLE, "users")
        tbl = CanonicalTable(
            id=tbl_id,
            namespace_id="ns1",
            name="users",
            columns=(self.col,),
            provenance=self.prov,
        )
        ns = CanonicalNamespace(
            id="ns1",
            name="public",
            tables=(tbl,),
            provenance=self.prov,
        )
        db = CanonicalDatabase(
            id="db1",
            name="corp_db",
            engine="postgresql",
            namespaces=(ns,),
            provenance=self.prov,
        )

        self.assertEqual(len(db.all_tables()), 1)
        found = db.find_table("public", "users")
        self.assertIsNotNone(found)
        self.assertEqual(found.name, "users")

        missing = db.find_table("public", "nonexistent")
        self.assertIsNone(missing)


if __name__ == "__main__":
    unittest.main()
