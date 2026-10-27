"""Unit tests for SQLite Type Affinity rules (specification Section 3.1)."""

import unittest

from dera_connectors.sqlite.types import (
    SQLiteTypeAffinity,
    determine_sqlite_affinity,
    parse_sqlite_column_type,
)


class TestSqliteTypeAffinity(unittest.TestCase):
    """Test suite for SQLite official type affinity rules 1 through 5."""

    def test_rule_1_integer_affinity(self) -> None:
        """Rule 1: If declared type contains INT -> INTEGER affinity (including POINT)."""
        for decl in (
            "INT",
            "INTEGER",
            "TINYINT",
            "SMALLINT",
            "MEDIUMINT",
            "BIGINT",
            "UNSIGNED BIG INT",
            "INT2",
            "POINT",
        ):
            self.assertEqual(
                determine_sqlite_affinity(decl),
                SQLiteTypeAffinity.INTEGER,
                f"Failed for {decl}",
            )

    def test_rule_2_text_affinity(self) -> None:
        """Rule 2: If declared type contains CHAR, CLOB, or TEXT -> TEXT affinity."""
        for decl in (
            "CHARACTER(20)",
            "VARCHAR(255)",
            "VARYING CHARACTER(255)",
            "NCHAR(55)",
            "TEXT",
            "CLOB",
        ):
            self.assertEqual(
                determine_sqlite_affinity(decl),
                SQLiteTypeAffinity.TEXT,
                f"Failed for {decl}",
            )

    def test_rule_3_blob_affinity(self) -> None:
        """Rule 3: If declared type contains BLOB or is omitted -> BLOB affinity."""
        for decl in ("BLOB", None, "", "   "):
            self.assertEqual(
                determine_sqlite_affinity(decl),
                SQLiteTypeAffinity.BLOB,
                f"Failed for {decl}",
            )

    def test_rule_4_real_affinity(self) -> None:
        """Rule 4: If declared type contains REAL, FLOA, or DOUB -> REAL affinity."""
        for decl in ("REAL", "FLOAT", "DOUBLE", "DOUBLE PRECISION"):
            self.assertEqual(
                determine_sqlite_affinity(decl),
                SQLiteTypeAffinity.REAL,
                f"Failed for {decl}",
            )

    def test_rule_5_numeric_affinity(self) -> None:
        """Rule 5: Otherwise -> NUMERIC affinity."""
        for decl in ("NUMERIC", "DECIMAL(10,5)", "BOOLEAN", "DATE", "DATETIME", "JSON"):
            self.assertEqual(
                determine_sqlite_affinity(decl),
                SQLiteTypeAffinity.NUMERIC,
                f"Failed for {decl}",
            )

    def test_parse_sqlite_column_type(self) -> None:
        """Verify parse_sqlite_column_type returns both original declared type and affinity."""
        clean, aff = parse_sqlite_column_type(" VARCHAR(100) ")
        self.assertEqual(clean, "VARCHAR(100)")
        self.assertEqual(aff, SQLiteTypeAffinity.TEXT)
