"""Unit and Integrity tests for referential integrity validation."""

from __future__ import annotations

import unittest

from dera.metadata.enums import CanonicalTypeCategory, ConstraintType
from dera.metadata.models.column import CanonicalColumn
from dera.metadata.models.constraint import CanonicalConstraint
from dera.reverse_engineering.builder import SchemaBuilder
from dera.reverse_engineering.errors import MissingParentError, SchemaValidationError
from dera.reverse_engineering.references import ResolutionStatus
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

    def test_registry_missing_objects_raise_only_in_strict_mode(self) -> None:
        table = self.schema.find_table("public", "users")
        objects = (
            table.columns[0],
            table.primary_key,
            table.unique_constraints[0],
            table.check_constraints[0],
            table.indexes[0],
            table.triggers[0],
            table.foreign_keys[0],
            self.schema.all_views()[0],
        )
        for obj in objects:
            with self.subTest(object_id=obj.id):
                schema = SchemaBuilder.from_canonical_database(self.enterprise_db)
                del schema.registry._objects[obj.id]
                issues = validate_schema_representation(schema)
                self.assertTrue(any(obj.id in issue and "registry" in issue for issue in issues))
                with self.assertRaisesRegex(SchemaValidationError, "registry"):
                    validate_schema_representation(schema, strict=True)

    def test_invalid_database_id_raises_in_strict_mode(self) -> None:
        db = self.enterprise_db.model_copy(update={"id": "invalid"})
        schema = SchemaBuilder.from_canonical_database(db)
        self.assertTrue(
            any("Invalid database ObjectId" in issue for issue in schema.validation_issues)
        )
        with self.assertRaisesRegex(SchemaValidationError, "Invalid database ObjectId"):
            validate_schema_representation(schema, strict=True)

    def test_duplicate_ordinals_remain_diagnostic_in_strict_mode(self) -> None:
        public = self.enterprise_db.get_namespace("public")
        table = public.get_table("organizations")
        col = table.columns[1].model_copy(
            update={"ordinal_position": table.columns[0].ordinal_position}
        )
        table = table.model_copy(update={"columns": (table.columns[0], col) + table.columns[2:]})
        public = public.model_copy(update={"tables": (table,)})
        schema = SchemaBuilder.from_canonical_database(
            self.enterprise_db.model_copy(update={"namespaces": (public,)}), strict_validation=True
        )
        self.assertTrue(any("Duplicate ordinal" in issue for issue in schema.validation_issues))

    def test_name_resolved_foreign_key_checks_parent_columns(self) -> None:
        public = self.enterprise_db.get_namespace("public")
        parent = public.get_table("organizations")
        child = public.get_table("users")
        fk = child.foreign_keys[0].model_copy(update={"referenced_table_id": None})
        child = child.model_copy(update={"foreign_keys": (fk,)})
        parent = parent.model_copy(update={"columns": (), "primary_key": None, "indexes": ()})
        public = public.model_copy(update={"tables": (parent, child)})
        schema = SchemaBuilder.from_canonical_database(
            self.enterprise_db.model_copy(update={"namespaces": (public,)})
        )
        self.assertTrue(
            any("parent column 'org_id'" in issue for issue in schema.validation_issues)
        )
        with self.assertRaisesRegex(SchemaValidationError, "parent column"):
            validate_schema_representation(schema, strict=True)

    def test_foreign_key_target_status_and_kind_are_respected(self) -> None:
        ref = self.schema.foreign_key_references[0]
        column = self.schema.find_table("public", "users").columns[0]
        for target_id, status in (
            ("dera:table:missing", ResolutionStatus.MISSING),
            (None, ResolutionStatus.MISSING),
            (ref.referenced_table_id, ResolutionStatus.RESTRICTED),
            (column.id, ResolutionStatus.RESOLVED),
        ):
            with self.subTest(target=target_id, status=status):
                changed_ref = ref.model_copy(
                    update={"referenced_table_id": target_id, "status": status}
                )
                schema = self.schema.model_copy(update={"foreign_key_references": (changed_ref,)})
                issues = validate_schema_representation(schema, strict=False)
                if target_id == column.id:
                    self.assertTrue(any("not a table" in issue for issue in issues))
                    with self.assertRaises(SchemaValidationError):
                        validate_schema_representation(schema, strict=True)
                else:
                    self.assertEqual(issues, ())
                    self.assertEqual(validate_schema_representation(schema, strict=True), ())
                self.assertTrue(validate_schema_representation(schema, strict_foreign_keys=True))
                with self.assertRaises(SchemaValidationError):
                    validate_schema_representation(schema, strict=True, strict_foreign_keys=True)


if __name__ == "__main__":
    unittest.main()
