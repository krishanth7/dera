"""Unit tests for SQLite catalog queries, PRAGMA builders, and DDL parser routines."""

import unittest

from dera_connectors.sqlite.catalog import (
    extract_check_constraints_from_sql,
    parse_table_options,
)
from dera_connectors.sqlite.queries import (
    build_pragma_foreign_key_list,
    build_pragma_index_info,
    build_pragma_index_list,
    build_pragma_index_xinfo,
    build_pragma_table_info,
    build_pragma_table_xinfo,
    quote_sqlite_identifier,
)


class TestSqliteCatalogQueries(unittest.TestCase):
    """Test suite for SQLite query construction and DDL clause extraction."""

    def test_quote_sqlite_identifier(self) -> None:
        """Verify standard and edge-case double-quote identifier escaping."""
        self.assertEqual(quote_sqlite_identifier("simple"), '"simple"')
        self.assertEqual(quote_sqlite_identifier('has"quotes'), '"has""quotes"')
        self.assertEqual(quote_sqlite_identifier("Special Table Name"), '"Special Table Name"')
        self.assertEqual(quote_sqlite_identifier("table-with-dashes"), '"table-with-dashes"')

    def test_pragma_builders(self) -> None:
        """Verify proper identifier quoting in generated PRAGMA statements."""
        tbl = 'my"table'
        self.assertEqual(build_pragma_table_xinfo(tbl), 'PRAGMA table_xinfo("my""table");')
        self.assertEqual(build_pragma_table_info(tbl), 'PRAGMA table_info("my""table");')
        self.assertEqual(
            build_pragma_foreign_key_list(tbl), 'PRAGMA foreign_key_list("my""table");'
        )
        self.assertEqual(build_pragma_index_list(tbl), 'PRAGMA index_list("my""table");')
        self.assertEqual(build_pragma_index_xinfo(tbl), 'PRAGMA index_xinfo("my""table");')
        self.assertEqual(build_pragma_index_info(tbl), 'PRAGMA index_info("my""table");')

    def test_parse_table_options_strict(self) -> None:
        """Verify detection of STRICT table option."""
        sql = "CREATE TABLE users (id INT, name TEXT) STRICT;"
        opts = parse_table_options(sql)
        self.assertTrue(opts["is_strict"])
        self.assertFalse(opts["without_rowid"])

    def test_parse_table_options_without_rowid(self) -> None:
        """Verify detection of WITHOUT ROWID table option."""
        sql = "CREATE TABLE kv (k TEXT PRIMARY KEY, v TEXT) WITHOUT ROWID;"
        opts = parse_table_options(sql)
        self.assertFalse(opts["is_strict"])
        self.assertTrue(opts["without_rowid"])

    def test_parse_table_options_strict_and_without_rowid(self) -> None:
        """Verify detection of combined STRICT, WITHOUT ROWID table options."""
        sql = "CREATE TABLE kv (k TEXT PRIMARY KEY, v TEXT) STRICT, WITHOUT ROWID;"
        opts = parse_table_options(sql)
        self.assertTrue(opts["is_strict"])
        self.assertTrue(opts["without_rowid"])

    def test_extract_check_constraints_simple(self) -> None:
        """Verify extraction of anonymous check constraint."""
        sql = "CREATE TABLE orders (id INT, amount NUMERIC CHECK (amount >= 0));"
        checks = extract_check_constraints_from_sql("main", "orders", sql)
        self.assertEqual(len(checks), 1)
        self.assertEqual(checks[0].check_clause, "amount >= 0")
        self.assertIn("chk_orders", checks[0].constraint_name or "")

    def test_extract_check_constraints_named(self) -> None:
        """Verify extraction of explicitly named check constraint."""
        sql = "CREATE TABLE accounts (id INT, bal NUMERIC, CONSTRAINT chk_positive_bal CHECK (bal > 0));"
        checks = extract_check_constraints_from_sql("main", "accounts", sql)
        self.assertEqual(len(checks), 1)
        self.assertEqual(checks[0].constraint_name, "chk_positive_bal")
        self.assertEqual(checks[0].check_clause, "bal > 0")

    def test_extract_check_constraints_nested_parens(self) -> None:
        """Verify extraction of check constraint with nested function parentheses."""
        sql = "CREATE TABLE items (code TEXT CHECK (length(trim(code)) > 3));"
        checks = extract_check_constraints_from_sql("main", "items", sql)
        self.assertEqual(len(checks), 1)
        self.assertEqual(checks[0].check_clause, "length(trim(code)) > 3")
