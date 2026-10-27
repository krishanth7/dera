"""Tests for Security Boundaries, Limits, and Reference Integrity."""

from __future__ import annotations

import unittest

from dera.metadata.enums import CanonicalTypeCategory, ConstraintType
from dera.metadata.errors import (
    DuplicateIdentityError,
    InvalidReferenceError,
    MetadataLimitExceededError,
)
from dera.metadata.models import (
    CanonicalColumn,
    CanonicalConstraint,
    CanonicalDatabase,
    CanonicalNamespace,
    CanonicalTable,
)
from dera.metadata.provenance import MetadataProvenance
from dera.metadata.validation import (
    MAX_DEFINITION_LENGTH,
    MAX_IDENTIFIER_LENGTH,
    validate_canonical_database,
    validate_definition_length,
    validate_identifier_length,
)


class TestSecurityBounds(unittest.TestCase):
    """Test suite ensuring resource boundaries and multi-tenant isolation."""

    def setUp(self) -> None:
        self.prov = MetadataProvenance(
            source_engine="sqlite",
            native_identifier="test",
        )

    def test_identifier_length_limit(self) -> None:
        """Verify identifiers exceeding MAX_IDENTIFIER_LENGTH are rejected."""
        valid_name = "a" * MAX_IDENTIFIER_LENGTH
        validate_identifier_length(valid_name)

        invalid_name = "a" * (MAX_IDENTIFIER_LENGTH + 1)
        with self.assertRaises(MetadataLimitExceededError):
            validate_identifier_length(invalid_name)

    def test_definition_length_limit(self) -> None:
        """Verify raw SQL definitions exceeding MAX_DEFINITION_LENGTH are rejected."""
        valid_defn = "x" * 1000
        validate_definition_length(valid_defn)

        invalid_defn = "x" * (MAX_DEFINITION_LENGTH + 1)
        with self.assertRaises(MetadataLimitExceededError):
            validate_definition_length(invalid_defn)

    def test_duplicate_identity_detection(self) -> None:
        """Verify validator flags colliding object IDs."""
        col1 = CanonicalColumn(
            id="duplicate_id",
            parent_table_id="t1",
            name="col_a",
            ordinal_position=1,
            native_data_type="INTEGER",
            canonical_type=CanonicalTypeCategory.INTEGER,
            provenance=self.prov,
        )
        col2 = CanonicalColumn(
            id="duplicate_id",  # Collision!
            parent_table_id="t1",
            name="col_b",
            ordinal_position=2,
            native_data_type="TEXT",
            canonical_type=CanonicalTypeCategory.TEXT,
            provenance=self.prov,
        )
        tbl = CanonicalTable(
            id="t1",
            namespace_id="ns1",
            name="users",
            columns=(col1, col2),
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
            name="test_db",
            engine="sqlite",
            namespaces=(ns,),
            provenance=self.prov,
        )

        with self.assertRaises(DuplicateIdentityError):
            validate_canonical_database(db)

    def test_invalid_reference_in_primary_key(self) -> None:
        """Verify PK referencing non-existent column raises InvalidReferenceError."""
        col = CanonicalColumn(
            id="col1",
            parent_table_id="t1",
            name="id",
            ordinal_position=1,
            native_data_type="INTEGER",
            canonical_type=CanonicalTypeCategory.INTEGER,
            provenance=self.prov,
        )
        pk = CanonicalConstraint(
            id="pk1",
            parent_table_id="t1",
            name="pk_users",
            constraint_type=ConstraintType.PRIMARY_KEY,
            columns=("ghost_column",),  # Does not exist!
            provenance=self.prov,
        )
        tbl = CanonicalTable(
            id="t1",
            namespace_id="ns1",
            name="users",
            columns=(col,),
            primary_key=pk,
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
            name="test_db",
            engine="sqlite",
            namespaces=(ns,),
            provenance=self.prov,
        )

        with self.assertRaises(InvalidReferenceError):
            validate_canonical_database(db)


if __name__ == "__main__":
    unittest.main()
