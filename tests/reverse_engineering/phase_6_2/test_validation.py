"""Unit tests for structural validation in Phase 6.2."""

import unittest

from dera.reverse_engineering.reconstruction.errors import StructuralValidationError
from dera.reverse_engineering.reconstruction.models import (
    ReconstructionMode,
    ValidationSeverity,
)
from dera.reverse_engineering.reconstruction.tables import reconstruct_table
from dera.reverse_engineering.reconstruction.validation import validate_structural_reconstruction

from tests.reverse_engineering.phase_6_2.fixtures import (
    build_postgres_enterprise_fixture,
)


class TestStructuralValidation(unittest.TestCase):
    """Test validation findings, severity levels, and strict vs partial modes."""

    def test_valid_enterprise_schema_passes_strict(self) -> None:
        canonical_db = build_postgres_enterprise_fixture()
        t1 = reconstruct_table(canonical_db.namespaces[0].tables[0], "postgresql")
        t2 = reconstruct_table(canonical_db.namespaces[0].tables[1], "postgresql")

        findings = validate_structural_reconstruction((t1, t2), mode=ReconstructionMode.STRICT)
        self.assertEqual(len(findings), 0)

    def test_duplicate_table_names_raises_in_strict(self) -> None:
        canonical_db = build_postgres_enterprise_fixture()
        t1 = reconstruct_table(canonical_db.namespaces[0].tables[0], "postgresql")
        # Duplicate t1
        with self.assertRaises(StructuralValidationError):
            validate_structural_reconstruction((t1, t1), mode=ReconstructionMode.STRICT)

    def test_partial_mode_collects_findings_without_raising(self) -> None:
        canonical_db = build_postgres_enterprise_fixture()
        t1 = reconstruct_table(canonical_db.namespaces[0].tables[0], "postgresql")

        findings = validate_structural_reconstruction((t1, t1), mode=ReconstructionMode.PARTIAL)
        self.assertGreater(len(findings), 0)
        self.assertTrue(any(f.severity == ValidationSeverity.ERROR for f in findings))
        self.assertEqual(findings[0].code, "DUPLICATE_TABLE_ID")


if __name__ == "__main__":
    unittest.main()
