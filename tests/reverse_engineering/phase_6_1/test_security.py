"""Security tests for Phase 6.1 Schema Representation."""

from __future__ import annotations

import unittest

from dera.metadata.enums import CanonicalTypeCategory, ObjectKind
from dera.metadata.identity import compute_stable_object_id
from dera.metadata.models.column import CanonicalColumn
from dera.metadata.models.database import CanonicalDatabase
from dera.metadata.models.namespace import CanonicalNamespace
from dera.metadata.models.table import CanonicalTable
from dera.reverse_engineering.builder import SchemaBuilder, SchemaResourceLimits
from dera.reverse_engineering.errors import (
    SchemaResourceLimitError,
    SchemaSerializationError,
    UnsupportedSchemaContractError,
)
from dera.reverse_engineering.serialization import (
    deserialize_schema_representation,
    serialize_schema_representation,
)

from tests.reverse_engineering.phase_6_1.fixtures import (
    build_enterprise_fixture,
    make_provenance,
)


class TestSecurity(unittest.TestCase):
    """Test suite ensuring strict security, workspace isolation, and zero code execution."""

    def test_workspace_isolation_in_identity(self) -> None:
        """Verify that identical schema names across different workspaces produce distinct ObjectIds."""
        id_ws_a = compute_stable_object_id(
            "postgresql", ObjectKind.TABLE, "users", workspace_id="ws_tenant_a"
        )
        id_ws_b = compute_stable_object_id(
            "postgresql", ObjectKind.TABLE, "users", workspace_id="ws_tenant_b"
        )

        self.assertNotEqual(id_ws_a, id_ws_b)

        # Build two schemas for different workspaces
        db_a = build_enterprise_fixture(workspace_id="ws_tenant_a")
        db_b = build_enterprise_fixture(workspace_id="ws_tenant_b")

        schema_a = SchemaBuilder.from_canonical_database(db_a, workspace_id="ws_tenant_a")
        schema_b = SchemaBuilder.from_canonical_database(db_b, workspace_id="ws_tenant_b")

        self.assertEqual(schema_a.registry.workspace_id, "ws_tenant_a")
        self.assertEqual(schema_b.registry.workspace_id, "ws_tenant_b")
        self.assertNotEqual(schema_a.database_id, schema_b.database_id)

    def test_zero_credentials_in_serialized_schema(self) -> None:
        """Verify serialized schema representations contain zero database credentials or passwords."""
        schema = SchemaBuilder.from_canonical_database(build_enterprise_fixture())
        serialized = serialize_schema_representation(schema)

        forbidden_tokens = ["password", "secret", "auth_token", "private_key", "bearer"]
        for token in forbidden_tokens:
            self.assertNotIn(f'"{token}"', serialized.lower())

    def test_malicious_sql_injection_identifier_treated_as_plain_data(self) -> None:
        """Verify SQL injection strings in table or column names are treated strictly as string literals."""
        injection_name = "users'; DROP TABLE users; --"
        prov = make_provenance(identifier=injection_name)
        db_id = compute_stable_object_id("postgresql", ObjectKind.DATABASE, "test_db")
        ns_id = compute_stable_object_id(
            "postgresql", ObjectKind.NAMESPACE, "public", parent_id=db_id
        )
        tbl_id = compute_stable_object_id(
            "postgresql", ObjectKind.TABLE, injection_name, namespace="public", parent_id=ns_id
        )
        col_id = compute_stable_object_id(
            "postgresql", ObjectKind.COLUMN, "id", namespace="public", parent_id=tbl_id
        )

        col = CanonicalColumn(
            id=col_id,
            parent_table_id=tbl_id,
            name="id",
            ordinal_position=1,
            native_data_type="INT",
            canonical_type=CanonicalTypeCategory.INTEGER,
            provenance=prov,
        )
        tbl = CanonicalTable(
            id=tbl_id,
            namespace_id=ns_id,
            name=injection_name,
            columns=(col,),
            provenance=prov,
        )
        ns = CanonicalNamespace(id=ns_id, name="public", tables=(tbl,), provenance=prov)
        db = CanonicalDatabase(
            id=db_id,
            name="test_db",
            engine="postgresql",
            contract_version="1.0.0",
            namespaces=(ns,),
            provenance=prov,
        )

        schema = SchemaBuilder.from_canonical_database(db)
        found_tbl = schema.find_table("public", injection_name)
        self.assertIsNotNone(found_tbl)
        self.assertEqual(found_tbl.name, injection_name)

    def test_excessive_identifier_length_dos_protection(self) -> None:
        """Verify DoS defense against excessively long identifier names."""
        long_identifier = "x" * 500  # Exceeds default limit of 256
        limits = SchemaResourceLimits(max_identifier_length=256)
        prov = make_provenance(identifier=long_identifier)
        db_id = compute_stable_object_id("postgresql", ObjectKind.DATABASE, long_identifier)

        db = CanonicalDatabase(
            id=db_id,
            name=long_identifier,
            engine="postgresql",
            contract_version="1.0.0",
            namespaces=(),
            provenance=prov,
        )

        with self.assertRaises(SchemaResourceLimitError) as ctx:
            SchemaBuilder.from_canonical_database(db, limits=limits)
        self.assertIn("max_identifier_length", ctx.exception.limit_name)

    def test_unsafe_deserialization_rejection(self) -> None:
        """Verify deserialization rejects non-dict and executable injection attempts."""
        with self.assertRaises(SchemaSerializationError):
            deserialize_schema_representation('"just a string"')

        with self.assertRaises(SchemaSerializationError):
            deserialize_schema_representation("[1, 2, 3]")

        with self.assertRaises((SchemaSerializationError, UnsupportedSchemaContractError)):
            deserialize_schema_representation('{"__class__": "os.system"}')


if __name__ == "__main__":
    unittest.main()
