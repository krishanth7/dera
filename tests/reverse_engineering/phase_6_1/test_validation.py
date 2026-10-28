"""Unit and Integrity tests for referential integrity validation."""

from __future__ import annotations

import unittest

from dera.metadata.enums import CanonicalTypeCategory, ConstraintType
from dera.metadata.models.column import CanonicalColumn
from dera.metadata.models.constraint import CanonicalConstraint
from dera.reverse_engineering.builder import SchemaBuilder
from dera.reverse_engineering.errors import MissingParentError, SchemaValidationError
from dera.reverse_engineering.validation import validate_schema_representation

from tests.reverse_engineering.phase_6_1.fixtures import (
    build_enterprise_fixture,
    make_provenance,
)


class TestValidation(unittest.TestCase):
    """Test suite for referential integrity and structural validation."""

    def setUp(self) -> None:
        self.enterprise_db = build_enterprise_fixture()
        self.schema = SchemaBuilder.from_canonical_database(self.enterprise_db)

    def test_valid_schema_passes_validation(self) -> None:
        """Verify clean schema has no validation issues."""
        issues = validate_schema_representation(self.schema)
        self.assertEqual(len(issues), 0)
        self.assertTrue(self.schema.is_validated)

    def test_missing_column_in_constraint_detected(self) -> None:
        """Verify that constraint referencing a nonexistent column is detected."""
        prov = make_provenance()
        # Create a table where constraint references 'missing_col'
        table = self.schema.find_table("public", "organizations")
        self.assertIsNotNone(table)

        bad_constraint = CanonicalConstraint(
            id="dera:constraint:bad000000000000000000001",
            parent_table_id=table.id,
            name="chk_invalid_column",
            constraint_type=ConstraintType.CHECK,
            columns=("missing_column",),
            check_clause="missing_column > 0",
            provenance=prov,
        )

        mutated_table = table.model_copy(update={"check_constraints": (bad_constraint,)})

        pub_ns = self.schema.database.get_namespace("public")
        self.assertIsNotNone(pub_ns)
        mutated_ns = pub_ns.model_copy(update={"tables": (mutated_table,)})
        mutated_db = self.enterprise_db.model_copy(update={"namespaces": (mutated_ns,)})

        # In lenient mode, issues are reported in schema.validation_issues
        schema = SchemaBuilder.from_canonical_database(mutated_db, strict_validation=False)
        self.assertFalse(schema.is_validated)
        self.assertGreater(len(schema.validation_issues), 0)
        self.assertTrue(any("missing_column" in issue for issue in schema.validation_issues))

        # In strict mode, SchemaValidationError is raised
        with self.assertRaises(SchemaValidationError):
            SchemaBuilder.from_canonical_database(mutated_db, strict_validation=True)

    def test_missing_parent_table_on_column_detected(self) -> None:
        """Verify column with nonexistent parent_table_id triggers error."""
        prov = make_provenance()
        table = self.schema.find_table("public", "organizations")
        self.assertIsNotNone(table)

        orphan_col = CanonicalColumn(
            id="dera:column:orphan00000000000000001",
            parent_table_id="dera:table:differenttable000000001",
            name="orphan_column",
            ordinal_position=99,
            native_data_type="INT",
            canonical_type=CanonicalTypeCategory.INTEGER,
            provenance=prov,
        )

        mutated_table = table.model_copy(update={"columns": table.columns + (orphan_col,)})
        pub_ns = self.schema.database.get_namespace("public")
        self.assertIsNotNone(pub_ns)
        mutated_ns = pub_ns.model_copy(update={"tables": (mutated_table,)})
        mutated_db = self.enterprise_db.model_copy(update={"namespaces": (mutated_ns,)})

        with self.assertRaises(MissingParentError):
            SchemaBuilder.from_canonical_database(mutated_db, strict_validation=True)


if __name__ == "__main__":
    unittest.main()
