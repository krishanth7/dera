"""Unit and Contract tests for TypedRef and ForeignKeyReference."""

from __future__ import annotations

import unittest

from dera.metadata.enums import ObjectKind
from dera.reverse_engineering.builder import SchemaBuilder
from dera.reverse_engineering.references import (
    ForeignKeyReference,
    ResolutionStatus,
    TypedRef,
)

from tests.reverse_engineering.phase_6_1.fixtures import build_enterprise_fixture


class TestReferences(unittest.TestCase):
    """Test suite for typed object references and foreign key references."""

    def setUp(self) -> None:
        self.enterprise_db = build_enterprise_fixture()
        self.schema = SchemaBuilder.from_canonical_database(self.enterprise_db)
        self.registry = self.schema.registry

    def test_typed_ref_immutability_and_defaults(self) -> None:
        """Verify TypedRef is immutable (frozen) and defaults to MISSING."""
        ref = TypedRef[str](
            target_id="dera:table:123456789012345678901234",
            expected_kind=ObjectKind.TABLE,
        )
        self.assertEqual(ref.status, ResolutionStatus.MISSING)
        self.assertTrue(ref.is_missing)
        self.assertFalse(ref.is_resolved)

        from pydantic import ValidationError

        # Immutability check
        with self.assertRaises((ValidationError, TypeError)):
            ref.status = ResolutionStatus.RESOLVED  # type: ignore

    def test_typed_ref_status_transitions(self) -> None:
        """Verify functional transition methods return new instances."""
        ref = TypedRef[str](
            target_id="dera:table:123456789012345678901234",
            expected_kind=ObjectKind.TABLE,
        )
        resolved_ref = ref.resolve()
        self.assertEqual(resolved_ref.status, ResolutionStatus.RESOLVED)
        self.assertTrue(resolved_ref.is_resolved)
        self.assertEqual(ref.status, ResolutionStatus.MISSING)  # Original unchanged

        restricted_ref = ref.mark_restricted()
        self.assertEqual(restricted_ref.status, ResolutionStatus.RESTRICTED)

        invalid_ref = ref.mark_invalid()
        self.assertEqual(invalid_ref.status, ResolutionStatus.INVALID)

    def test_registry_resolve_ref(self) -> None:
        """Verify ObjectRegistry.resolve_ref against registered objects."""
        tbl = self.schema.find_table("public", "organizations")
        self.assertIsNotNone(tbl)

        valid_ref = TypedRef[str](
            target_id=tbl.id,
            expected_kind=ObjectKind.TABLE,
        )
        resolved = self.registry.resolve_ref(valid_ref)
        self.assertEqual(resolved.status, ResolutionStatus.RESOLVED)

        missing_ref = TypedRef[str](
            target_id="dera:table:000000000000000000000000",
            expected_kind=ObjectKind.TABLE,
        )
        missing_res = self.registry.resolve_ref(missing_ref)
        self.assertEqual(missing_res.status, ResolutionStatus.MISSING)

        mismatched_ref = TypedRef[str](
            target_id=tbl.id,
            expected_kind=ObjectKind.COLUMN,
        )
        mismatched_res = self.registry.resolve_ref(mismatched_ref)
        self.assertEqual(mismatched_res.status, ResolutionStatus.INVALID)

    def test_foreign_key_reference_in_schema(self) -> None:
        """Verify foreign key references built by SchemaBuilder are resolved."""
        fk_refs = self.schema.foreign_key_references
        self.assertEqual(len(fk_refs), 1)

        fk = fk_refs[0]
        self.assertIsInstance(fk, ForeignKeyReference)
        self.assertEqual(fk.foreign_key_name, "fk_users_org")
        self.assertEqual(fk.source_table_name, "users")
        self.assertEqual(fk.referenced_table_name, "organizations")
        self.assertEqual(fk.source_columns, ("org_id",))
        self.assertEqual(fk.referenced_columns, ("org_id",))
        self.assertEqual(fk.status, ResolutionStatus.RESOLVED)
        self.assertTrue(fk.is_resolved)
        self.assertIsNotNone(fk.referenced_table_id)


if __name__ == "__main__":
    unittest.main()
