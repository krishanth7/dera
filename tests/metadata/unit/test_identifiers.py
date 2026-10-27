"""Tests for DERA Identifier normalization and case-folding rules."""

from __future__ import annotations

import unittest

from dera.metadata.identifiers import Identifier, qualify_identifier


class TestIdentifiers(unittest.TestCase):
    """Unit test suite for Identifier parsing and dialect case-folding."""

    def test_unquoted_identifier(self) -> None:
        """Verify standard unquoted identifier parsing."""
        ident = Identifier.parse("users", engine="postgresql")
        self.assertEqual(ident.raw_name, "users")
        self.assertFalse(ident.is_quoted)
        self.assertIsNone(ident.quote_char)
        self.assertEqual(ident.canonical_name, "users")

    def test_double_quoted_identifier(self) -> None:
        """Verify ANSI double-quoted identifier parsing."""
        ident = Identifier.parse('"Order Details"', engine="postgresql")
        self.assertEqual(ident.raw_name, "Order Details")
        self.assertTrue(ident.is_quoted)
        self.assertEqual(ident.quote_char, '"')
        self.assertEqual(ident.canonical_name, "Order Details")

    def test_backtick_quoted_identifier(self) -> None:
        """Verify MySQL backtick-quoted identifier parsing."""
        ident = Identifier.parse("`order_items`", engine="mysql")
        self.assertEqual(ident.raw_name, "order_items")
        self.assertTrue(ident.is_quoted)
        self.assertEqual(ident.quote_char, "`")

    def test_bracket_quoted_identifier(self) -> None:
        """Verify bracket-quoted identifier parsing."""
        ident = Identifier.parse("[system_log]", engine="sqlite")
        self.assertEqual(ident.raw_name, "system_log")
        self.assertTrue(ident.is_quoted)
        self.assertEqual(ident.quote_char, "[")

    def test_case_folding_postgresql(self) -> None:
        """Verify PostgreSQL folds unquoted to lowercase but preserves quoted."""
        unquoted = Identifier.parse("UsersTable", engine="postgresql")
        self.assertEqual(unquoted.lookup_key(), "userstable")

        quoted = Identifier.parse('"UsersTable"', engine="postgresql")
        self.assertEqual(quoted.lookup_key(), "UsersTable")

    def test_case_folding_sqlite(self) -> None:
        """Verify SQLite folds ASCII identifiers to lower case."""
        ident = Identifier.parse("Customers", engine="sqlite")
        self.assertEqual(ident.lookup_key(), "customers")

    def test_qualify_identifier(self) -> None:
        """Verify fully qualified identifier naming."""
        self.assertEqual(qualify_identifier("public", "accounts"), "public.accounts")
        self.assertEqual(qualify_identifier(None, "accounts"), "accounts")
        self.assertEqual(qualify_identifier("", "accounts"), "accounts")


if __name__ == "__main__":
    unittest.main()
