"""Tests for Metadata Query Allowlist Registry.

Validates that only registered, engine-compatible catalog queries are permitted,
and unauthorized queries or invalid parameter combinations are rejected.
"""

import unittest

from dera_connectors.security import (
    ApprovedMetadataQueryRegistry,
    QuerySpecification,
    ReadOnlySecurityViolationError,
    UnauthorizedQueryError,
)


class TestQueryAllowlist(unittest.TestCase):
    """Test suite verifying query allowlist enforcement."""

    def setUp(self) -> None:
        self.registry = ApprovedMetadataQueryRegistry()

    def test_default_registry_contains_supported_engines(self) -> None:
        """Verify default registry covers PostgreSQL, SQLite, MySQL, and MariaDB operations."""
        ops = [
            ("postgres.catalog.tables", "postgresql"),
            ("postgres.catalog.columns", "supabase"),
            ("sqlite.catalog.tables", "sqlite"),
            ("sqlite.catalog.columns", "sqlite"),
            ("mysql.catalog.tables", "mysql"),
            ("mysql.catalog.columns", "mariadb"),
        ]
        for op_id, engine in ops:
            spec = self.registry.get(op_id)
            self.assertIsNotNone(spec, f"Operation {op_id} missing from registry")
            self.assertIn(engine, spec.supported_engines)

    def test_valid_operation_passes(self) -> None:
        """Verify authorized operation with legitimate SQL passes validation."""
        sql = "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"
        spec = self.registry.validate_operation(
            operation_id="postgres.catalog.tables",
            engine="postgresql",
            sql=sql,
        )
        self.assertEqual(spec.operation_id, "postgres.catalog.tables")

    def test_unregistered_operation_rejected(self) -> None:
        """Verify unregistered operation IDs raise UnauthorizedQueryError."""
        with self.assertRaises(UnauthorizedQueryError) as ctx:
            self.registry.validate_operation(
                operation_id="custom.unapproved.dump_users",
                engine="postgresql",
                sql="SELECT * FROM users",
            )
        self.assertIn("not in the approved metadata query registry", ctx.exception.message)

    def test_engine_mismatch_rejected(self) -> None:
        """Verify executing an engine's query against an incompatible engine raises UnauthorizedQueryError."""
        with self.assertRaises(UnauthorizedQueryError) as ctx:
            self.registry.validate_operation(
                operation_id="sqlite.catalog.tables",
                engine="postgresql",
                sql="SELECT name FROM sqlite_master",
            )
        self.assertIn("not supported for database engine 'postgresql'", ctx.exception.message)

    def test_mutation_in_approved_operation_rejected(self) -> None:
        """Verify that even with an approved operation ID, mutation SQL is blocked."""
        with self.assertRaises(ReadOnlySecurityViolationError):
            self.registry.validate_operation(
                operation_id="postgres.catalog.tables",
                engine="postgresql",
                sql="DROP TABLE users; SELECT 1",
            )

    def test_rogue_parameter_rejected(self) -> None:
        """Verify parameters outside allowed parameter spec are rejected."""
        custom_registry = ApprovedMetadataQueryRegistry()
        custom_registry.register(
            QuerySpecification(
                operation_id="test.filtered_tables",
                supported_engines=frozenset({"postgresql"}),
                description="Test filtered tables",
                allowed_parameters=("schema_name",),
            )
        )

        # Valid param passes
        custom_registry.validate_operation(
            operation_id="test.filtered_tables",
            engine="postgresql",
            sql="SELECT 1",
            parameters={"schema_name": "public"},
        )

        # Rogue param fails
        with self.assertRaises(UnauthorizedQueryError) as ctx:
            custom_registry.validate_operation(
                operation_id="test.filtered_tables",
                engine="postgresql",
                sql="SELECT 1",
                parameters={"schema_name": "public", "evil_injected": "true"},
            )
        self.assertIn("Unrecognized parameter 'evil_injected'", ctx.exception.message)


if __name__ == "__main__":
    unittest.main()
