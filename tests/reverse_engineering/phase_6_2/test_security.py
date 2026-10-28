"""Security and resource bounds tests for Phase 6.2 Structural Reconstruction."""

import unittest

from dera.metadata.identity import compute_stable_object_id
from dera.reverse_engineering.builder import SchemaResourceLimits
from dera.reverse_engineering.errors import SchemaResourceLimitError
from dera.reverse_engineering.reconstruction.builder import StructuralReconstructionBuilder

from tests.reverse_engineering.phase_6_2.fixtures import (
    build_postgres_enterprise_fixture,
)


class TestStructuralSecurity(unittest.TestCase):
    """Test resource limits, injection resistance, and tenant isolation."""

    def test_max_tables_resource_limit_enforced(self) -> None:
        db = build_postgres_enterprise_fixture()
        limits = SchemaResourceLimits(max_tables=1)  # fixture has 2 tables
        builder = StructuralReconstructionBuilder(limits=limits)

        with self.assertRaises(SchemaResourceLimitError):
            builder.build_from_canonical(db)

    def test_max_columns_per_table_limit_enforced(self) -> None:
        db = build_postgres_enterprise_fixture()
        limits = SchemaResourceLimits(
            max_columns_per_table=3
        )  # fixture tables have 4 and 6 columns
        builder = StructuralReconstructionBuilder(limits=limits)

        with self.assertRaises(SchemaResourceLimitError):
            builder.build_from_canonical(db)

    def test_sql_injection_in_expression_treated_as_inert_text(self) -> None:
        # A malicious check expression attempting SQL injection or file reads
        malicious_expr = "price > 0); DROP TABLE users; --"
        parent_id = compute_stable_object_id("table", "postgresql", ("public", "items"))
        from dera.metadata.enums import ConstraintType
        from dera.metadata.models import CanonicalConstraint
        from dera.reverse_engineering.reconstruction.check_constraints import (
            reconstruct_check_constraint,
        )

        from tests.reverse_engineering.phase_6_2.fixtures import make_test_provenance

        ck = CanonicalConstraint(
            id=compute_stable_object_id(
                "check_constraint", "postgresql", (str(parent_id), "ck_malicious")
            ),
            table_id=parent_id,
            name="ck_malicious",
            constraint_type=ConstraintType.CHECK,
            expression=malicious_expr,
            provenance=make_test_provenance("postgresql"),
        )
        reconstructed = reconstruct_check_constraint(ck, parent_id)
        # Verify it is preserved verbatim as an inert string without execution
        self.assertEqual(reconstructed.expression, malicious_expr)

    def test_workspace_isolation_produces_distinct_hashes(self) -> None:
        # Two identical schemas under different workspace IDs
        db_tenant_a = build_postgres_enterprise_fixture(workspace_id="tenant-alpha")
        db_tenant_b = build_postgres_enterprise_fixture(workspace_id="tenant-beta")

        builder = StructuralReconstructionBuilder()
        res_a = builder.build_from_canonical(db_tenant_a)
        res_b = builder.build_from_canonical(db_tenant_b)

        # Object identities and schema hashes must differ across workspaces
        self.assertNotEqual(res_a.schema_hash, res_b.schema_hash)
        self.assertNotEqual(res_a.tables[0].object_id, res_b.tables[0].object_id)


if __name__ == "__main__":
    unittest.main()
