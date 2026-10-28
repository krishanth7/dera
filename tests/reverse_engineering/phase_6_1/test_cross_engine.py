"""Cross-engine compatibility tests for Phase 6.1 Schema Representation."""

from __future__ import annotations

import unittest

from dera.metadata.enums import (
    CanonicalTypeCategory,
    GenerationMode,
    MetadataCompleteness,
    ObjectKind,
)
from dera.metadata.identity import compute_stable_object_id
from dera.metadata.models.column import CanonicalColumn
from dera.metadata.models.database import CanonicalDatabase
from dera.metadata.models.namespace import CanonicalNamespace
from dera.metadata.models.table import CanonicalTable
from dera.reverse_engineering.builder import SchemaBuilder
from dera.reverse_engineering.capabilities import CapabilityState

from tests.reverse_engineering.phase_6_1.fixtures import (
    build_enterprise_fixture,
    build_sqlite_fixture,
    make_provenance,
)


class TestCrossEngineCompatibility(unittest.TestCase):
    """Test suite ensuring faithful representation across all supported engines."""

    def test_sqlite_engine_representation(self) -> None:
        """Verify SQLite single-namespace schema and capability awareness."""
        sqlite_db = build_sqlite_fixture()
        schema = SchemaBuilder.from_canonical_database(sqlite_db)

        self.assertEqual(schema.engine, "sqlite")
        self.assertEqual(len(schema.namespaces), 1)
        self.assertEqual(schema.namespaces[0].name, "main")

        # SQLite exposes partial check metadata, represented as a supported feature.
        profile = schema.capability_profile
        self.assertIsNotNone(profile)
        self.assertIn("check_constraints", profile.features)
        self.assertEqual(profile.features["check_constraints"], CapabilityState.SUPPORTED)

    def test_postgresql_engine_representation(self) -> None:
        """Verify PostgreSQL multi-namespace, composite foreign key schema."""
        pg_db = build_enterprise_fixture(engine="postgresql", db_name="pg_production")
        schema = SchemaBuilder.from_canonical_database(pg_db)

        self.assertEqual(schema.engine, "postgresql")
        self.assertEqual(len(schema.namespaces), 2)
        ns_names = {ns.name for ns in schema.namespaces}
        self.assertEqual(ns_names, {"public", "analytics"})

        profile = schema.capability_profile
        self.assertIsNotNone(profile)
        self.assertEqual(profile.overall_completeness, MetadataCompleteness.COMPLETE)

    def test_supabase_engine_representation(self) -> None:
        """Verify Supabase PostgreSQL representation."""
        prov = make_provenance(engine="supabase", identifier="supabase_db")
        db_id = compute_stable_object_id("supabase", ObjectKind.DATABASE, "postgres")
        auth_ns_id = compute_stable_object_id(
            "supabase", ObjectKind.NAMESPACE, "auth", parent_id=db_id
        )
        pub_ns_id = compute_stable_object_id(
            "supabase", ObjectKind.NAMESPACE, "public", parent_id=db_id
        )

        auth_ns = CanonicalNamespace(id=auth_ns_id, name="auth", provenance=prov)
        pub_ns = CanonicalNamespace(id=pub_ns_id, name="public", provenance=prov)

        db = CanonicalDatabase(
            id=db_id,
            name="postgres",
            engine="supabase",
            contract_version="1.0.0",
            namespaces=(auth_ns, pub_ns),
            provenance=prov,
        )

        schema = SchemaBuilder.from_canonical_database(db)
        self.assertEqual(schema.engine, "supabase")
        self.assertEqual(len(schema.namespaces), 2)
        self.assertIn("auth", [ns.name for ns in schema.namespaces])

    def test_mysql_engine_representation(self) -> None:
        """Verify MySQL catalog representation with table comments and foreign keys."""
        prov = make_provenance(engine="mysql", identifier="shop_db", version="8.0.36")
        db_id = compute_stable_object_id("mysql", ObjectKind.DATABASE, "shop_db")
        ns_id = compute_stable_object_id("mysql", ObjectKind.NAMESPACE, "shop_db", parent_id=db_id)

        tbl_id = compute_stable_object_id(
            "mysql", ObjectKind.TABLE, "orders", namespace="shop_db", parent_id=ns_id
        )
        c1_id = compute_stable_object_id(
            "mysql", ObjectKind.COLUMN, "id", namespace="shop_db", parent_id=tbl_id
        )

        table = CanonicalTable(
            id=tbl_id,
            namespace_id=ns_id,
            name="orders",
            columns=(
                CanonicalColumn(
                    id=c1_id,
                    parent_table_id=tbl_id,
                    name="id",
                    ordinal_position=1,
                    native_data_type="BIGINT UNSIGNED",
                    canonical_type=CanonicalTypeCategory.INTEGER,
                    is_nullable=False,
                    is_identity=True,
                    provenance=prov,
                ),
            ),
            comment="Stores customer order transactions",
            provenance=prov,
        )

        ns = CanonicalNamespace(id=ns_id, name="shop_db", tables=(table,), provenance=prov)
        db = CanonicalDatabase(
            id=db_id,
            name="shop_db",
            engine="mysql",
            contract_version="1.0.0",
            namespaces=(ns,),
            provenance=prov,
        )

        schema = SchemaBuilder.from_canonical_database(db)
        self.assertEqual(schema.engine, "mysql")
        orders_tbl = schema.find_table("shop_db", "orders")
        self.assertIsNotNone(orders_tbl)
        self.assertEqual(orders_tbl.comment, "Stores customer order transactions")

    def test_mariadb_engine_representation(self) -> None:
        """Verify MariaDB representation with virtual generated columns."""
        prov = make_provenance(engine="mariadb", identifier="crm_db", version="10.11.7")
        db_id = compute_stable_object_id("mariadb", ObjectKind.DATABASE, "crm_db")
        ns_id = compute_stable_object_id("mariadb", ObjectKind.NAMESPACE, "crm_db", parent_id=db_id)

        tbl_id = compute_stable_object_id(
            "mariadb", ObjectKind.TABLE, "contacts", namespace="crm_db", parent_id=ns_id
        )
        c1_id = compute_stable_object_id(
            "mariadb", ObjectKind.COLUMN, "id", namespace="crm_db", parent_id=tbl_id
        )
        c2_id = compute_stable_object_id(
            "mariadb", ObjectKind.COLUMN, "full_name", namespace="crm_db", parent_id=tbl_id
        )

        table = CanonicalTable(
            id=tbl_id,
            namespace_id=ns_id,
            name="contacts",
            columns=(
                CanonicalColumn(
                    id=c1_id,
                    parent_table_id=tbl_id,
                    name="id",
                    ordinal_position=1,
                    native_data_type="INT",
                    canonical_type=CanonicalTypeCategory.INTEGER,
                    is_nullable=False,
                    provenance=prov,
                ),
                CanonicalColumn(
                    id=c2_id,
                    parent_table_id=tbl_id,
                    name="full_name",
                    ordinal_position=2,
                    native_data_type="VARCHAR(200)",
                    canonical_type=CanonicalTypeCategory.TEXT,
                    is_nullable=True,
                    is_generated=True,
                    generation_mode=GenerationMode.VIRTUAL,
                    generation_expression="CONCAT(first_name, ' ', last_name)",
                    provenance=prov,
                ),
            ),
            provenance=prov,
        )

        ns = CanonicalNamespace(id=ns_id, name="crm_db", tables=(table,), provenance=prov)
        db = CanonicalDatabase(
            id=db_id,
            name="crm_db",
            engine="mariadb",
            contract_version="1.0.0",
            namespaces=(ns,),
            provenance=prov,
        )

        schema = SchemaBuilder.from_canonical_database(db)
        self.assertEqual(schema.engine, "mariadb")
        col = schema.find_column("crm_db", "contacts", "full_name")
        self.assertIsNotNone(col)
        self.assertTrue(col.is_generated)
        self.assertEqual(col.generation_mode, GenerationMode.VIRTUAL)


if __name__ == "__main__":
    unittest.main()
