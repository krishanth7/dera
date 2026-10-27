"""Tests for Cross-Engine Type Normalization taxonomy."""

from __future__ import annotations

import unittest

from dera.metadata.adapters import (
    MariaDbMetadataAdapter,
    MySqlMetadataAdapter,
    PostgresqlMetadataAdapter,
    SqliteMetadataAdapter,
)
from dera.metadata.enums import CanonicalTypeCategory


class TestTypeNormalization(unittest.TestCase):
    """Test suite ensuring correct type mapping across all supported database engines."""

    def test_postgresql_types(self) -> None:
        """Verify PostgreSQL native type categorization."""
        self.assertEqual(
            PostgresqlMetadataAdapter.categorize_type("bigint"), CanonicalTypeCategory.INTEGER
        )
        self.assertEqual(
            PostgresqlMetadataAdapter.categorize_type("numeric(12,2)"),
            CanonicalTypeCategory.DECIMAL,
        )
        self.assertEqual(
            PostgresqlMetadataAdapter.categorize_type("double precision"),
            CanonicalTypeCategory.FLOAT,
        )
        self.assertEqual(
            PostgresqlMetadataAdapter.categorize_type("boolean"), CanonicalTypeCategory.BOOLEAN
        )
        self.assertEqual(
            PostgresqlMetadataAdapter.categorize_type("varchar(100)"), CanonicalTypeCategory.TEXT
        )
        self.assertEqual(
            PostgresqlMetadataAdapter.categorize_type("bytea"), CanonicalTypeCategory.BINARY
        )
        self.assertEqual(
            PostgresqlMetadataAdapter.categorize_type("date"), CanonicalTypeCategory.DATE
        )
        self.assertEqual(
            PostgresqlMetadataAdapter.categorize_type("timestamptz"),
            CanonicalTypeCategory.TIMESTAMP,
        )
        self.assertEqual(
            PostgresqlMetadataAdapter.categorize_type("jsonb"), CanonicalTypeCategory.JSON
        )
        self.assertEqual(
            PostgresqlMetadataAdapter.categorize_type("uuid"), CanonicalTypeCategory.UUID
        )
        self.assertEqual(
            PostgresqlMetadataAdapter.categorize_type("integer[]"), CanonicalTypeCategory.ARRAY
        )
        self.assertEqual(
            PostgresqlMetadataAdapter.categorize_type("geometry"), CanonicalTypeCategory.SPATIAL
        )

    def test_sqlite_types(self) -> None:
        """Verify SQLite declared type and affinity categorization."""
        self.assertEqual(
            SqliteMetadataAdapter.categorize_type("INT"), CanonicalTypeCategory.INTEGER
        )
        self.assertEqual(
            SqliteMetadataAdapter.categorize_type("INTEGER"), CanonicalTypeCategory.INTEGER
        )
        self.assertEqual(
            SqliteMetadataAdapter.categorize_type("VARCHAR(255)"), CanonicalTypeCategory.TEXT
        )
        self.assertEqual(SqliteMetadataAdapter.categorize_type("TEXT"), CanonicalTypeCategory.TEXT)
        self.assertEqual(
            SqliteMetadataAdapter.categorize_type("BLOB"), CanonicalTypeCategory.BINARY
        )
        self.assertEqual(SqliteMetadataAdapter.categorize_type("REAL"), CanonicalTypeCategory.FLOAT)
        self.assertEqual(
            SqliteMetadataAdapter.categorize_type("BOOLEAN"), CanonicalTypeCategory.BOOLEAN
        )
        self.assertEqual(
            SqliteMetadataAdapter.categorize_type("DECIMAL(10,2)"), CanonicalTypeCategory.DECIMAL
        )
        self.assertEqual(SqliteMetadataAdapter.categorize_type("JSON"), CanonicalTypeCategory.JSON)

    def test_mysql_types(self) -> None:
        """Verify MySQL native type categorization."""
        self.assertEqual(
            MySqlMetadataAdapter.categorize_type("bigint"), CanonicalTypeCategory.INTEGER
        )
        self.assertEqual(
            MySqlMetadataAdapter.categorize_type("tinyint", "tinyint(1)"),
            CanonicalTypeCategory.BOOLEAN,
        )
        self.assertEqual(
            MySqlMetadataAdapter.categorize_type("decimal"), CanonicalTypeCategory.DECIMAL
        )
        self.assertEqual(
            MySqlMetadataAdapter.categorize_type("double"), CanonicalTypeCategory.FLOAT
        )
        self.assertEqual(
            MySqlMetadataAdapter.categorize_type("longtext"), CanonicalTypeCategory.TEXT
        )
        self.assertEqual(
            MySqlMetadataAdapter.categorize_type("longblob"), CanonicalTypeCategory.BINARY
        )
        self.assertEqual(
            MySqlMetadataAdapter.categorize_type("datetime"), CanonicalTypeCategory.TIMESTAMP
        )
        self.assertEqual(MySqlMetadataAdapter.categorize_type("json"), CanonicalTypeCategory.JSON)
        self.assertEqual(MySqlMetadataAdapter.categorize_type("enum"), CanonicalTypeCategory.ENUM)
        self.assertEqual(MySqlMetadataAdapter.categorize_type("set"), CanonicalTypeCategory.SET)
        self.assertEqual(
            MySqlMetadataAdapter.categorize_type("point"), CanonicalTypeCategory.SPATIAL
        )

    def test_mariadb_types(self) -> None:
        """Verify MariaDB type categorization."""
        self.assertEqual(
            MariaDbMetadataAdapter.categorize_type("int"), CanonicalTypeCategory.INTEGER
        )
        self.assertEqual(
            MariaDbMetadataAdapter.categorize_type("varchar"), CanonicalTypeCategory.TEXT
        )
        self.assertEqual(MariaDbMetadataAdapter.categorize_type("json"), CanonicalTypeCategory.JSON)


if __name__ == "__main__":
    unittest.main()
