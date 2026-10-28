"""Unit and Contract tests for deterministic serialization and safe deserialization."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import unittest

from dera.metadata.enums import MetadataCompleteness
from dera.reverse_engineering.builder import SchemaBuilder, SchemaResourceLimits
from dera.reverse_engineering.errors import (
    SchemaResourceLimitError,
    SchemaSerializationError,
    UnsupportedSchemaContractError,
)
from dera.reverse_engineering.schema import SchemaRepresentation
from dera.reverse_engineering.serialization import (
    compute_schema_hash,
    deserialize_schema_representation,
    serialize_schema_representation,
)

from tests.reverse_engineering.phase_6_1.fixtures import build_enterprise_fixture


class TestSerialization(unittest.TestCase):
    """Test suite for deterministic serialization and safe deserialization."""

    def setUp(self) -> None:
        self.enterprise_db = build_enterprise_fixture()
        self.schema = SchemaBuilder.from_canonical_database(self.enterprise_db)

    def test_serialize_schema_representation(self) -> None:
        """Verify deterministic serialization to UTF-8 JSON string."""
        serialized = serialize_schema_representation(self.schema)
        self.assertIsInstance(serialized, str)
        self.assertIn('"contract_version": "1.0.0"', serialized)
        self.assertIn('"database_name": "enterprise_db"', serialized)

        # Parse back to check structure
        data = json.loads(serialized)
        self.assertEqual(data["contract_version"], "1.0.0")
        self.assertEqual(data["database_id"], self.enterprise_db.id)
        self.assertIn("namespaces", data)
        self.assertIn("foreign_key_references", data)
        self.assertIn("capability_profile", data)

    def test_compute_schema_hash(self) -> None:
        """Verify SHA-256 cryptographic digest computation."""
        digest = compute_schema_hash(self.schema)
        self.assertIsInstance(digest, str)
        self.assertEqual(len(digest), 64)
        # Verify hex format
        int(digest, 16)

    def test_round_trip_deserialization(self) -> None:
        """Verify round-trip serialization and safe reconstruction."""
        json_str = serialize_schema_representation(self.schema)
        reconstructed = deserialize_schema_representation(json_str)

        self.assertIsInstance(reconstructed, SchemaRepresentation)
        self.assertEqual(reconstructed.database_id, self.schema.database_id)
        self.assertEqual(reconstructed.engine, self.schema.engine)
        self.assertEqual(len(reconstructed.namespaces), len(self.schema.namespaces))
        self.assertEqual(len(reconstructed.all_tables()), len(self.schema.all_tables()))

        # Verify ObjectRegistry and Hierarchy are reconstructed and operational
        retrieved_tbl = reconstructed.registry.get_table(
            self.schema.find_table("public", "organizations").id
        )
        self.assertEqual(retrieved_tbl.name, "organizations")

        # Verify hash match
        self.assertEqual(reconstructed.compute_hash(), self.schema.compute_hash())

    def test_round_trip_preserves_restricted_capabilities_and_completeness(self) -> None:
        schema = SchemaBuilder.from_canonical_database(
            self.enterprise_db, capabilities={"views": "restricted"}
        )
        rebuilt = deserialize_schema_representation(schema.to_json())
        self.assertEqual(rebuilt.capability_profile, schema.capability_profile)
        self.assertEqual(rebuilt.completeness, MetadataCompleteness.RESTRICTED)
        self.assertEqual(rebuilt.compute_hash(), schema.compute_hash())

    def test_deserialization_validates_capability_profile_and_completeness(self) -> None:
        for updates in (
            {"completeness": "invalid"},
            {"capability_profile": {"engine": "postgresql", "features": {"views": "invalid"}}},
            {"capability_profile": {"engine": "sqlite"}},
            {"completeness": "RESTRICTED"},
        ):
            with self.subTest(updates=updates):
                data = self.schema.to_dict()
                data.update(updates)
                with self.assertRaises(SchemaSerializationError):
                    deserialize_schema_representation(json.dumps(data))

    def test_sets_are_deterministic_across_hash_seeds(self) -> None:
        script = """
import json
from tests.reverse_engineering.phase_6_1.fixtures import build_enterprise_fixture
from dera.reverse_engineering.builder import SchemaBuilder
from dera.reverse_engineering.serialization import compute_schema_hash, serialize_schema_representation
db = build_enterprise_fixture()
prov = db.provenance.model_copy(update={"engine_specific": {
    "tags": {"gamma", "alpha", "beta"},
    "nested": [{"values": frozenset({"zeta", "delta"})}],
    "mixed": {1, "one", ("tuple", 2)},
}})
schema = SchemaBuilder.from_canonical_database(db.model_copy(update={"provenance": prov}))
assert json.loads(schema.to_json()) == json.loads(serialize_schema_representation(schema))
assert schema.compute_hash() == compute_schema_hash(schema)
print(schema.to_json())
print(schema.compute_hash())
"""
        outputs = [
            subprocess.check_output(
                [sys.executable, "-c", script],
                env={**os.environ, "PYTHONHASHSEED": seed},
                text=True,
            )
            for seed in ("1", "2", "3")
        ]
        self.assertEqual(outputs[0], outputs[1])
        self.assertEqual(outputs[0], outputs[2])

    def test_deserialization_malformed_json_raises_error(self) -> None:
        """Verify SchemaSerializationError on invalid JSON syntax."""
        with self.assertRaises(SchemaSerializationError):
            deserialize_schema_representation("{malformed json")

    def test_deserialization_unsupported_contract_version(self) -> None:
        """Verify UnsupportedSchemaContractError on contract version mismatch."""
        data = self.schema.to_dict()
        data["contract_version"] = "99.9.9"
        bad_json = json.dumps(data)
        with self.assertRaises(UnsupportedSchemaContractError):
            deserialize_schema_representation(bad_json)

    def test_deserialization_missing_database_raises_error(self) -> None:
        """Verify SchemaSerializationError when 'database' key is missing."""
        data = self.schema.to_dict()
        del data["database"]
        bad_json = json.dumps(data)
        with self.assertRaises(SchemaSerializationError):
            deserialize_schema_representation(bad_json)

    def test_deserialization_oversized_payload_rejected(self) -> None:
        """Verify SchemaResourceLimitError on excessively large serialized payload."""
        limits = SchemaResourceLimits(max_definition_bytes=10)
        json_str = serialize_schema_representation(self.schema)
        with self.assertRaises(SchemaResourceLimitError):
            deserialize_schema_representation(json_str, limits=limits)


if __name__ == "__main__":
    unittest.main()
