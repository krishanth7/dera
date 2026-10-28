"""Unit tests for dialect semantics handling in Phase 6.2."""

import unittest

from dera.reverse_engineering.reconstruction.models import DefaultKind
from dera.reverse_engineering.reconstruction.semantics import (
    classify_default_value,
    extract_identity_metadata,
    normalize_engine_name,
)
from tests.reverse_engineering.phase_6_2.fixtures import make_test_column


class TestEngineSemantics(unittest.TestCase):
    """Test dialect normalization, default classification, and identity extraction."""

    def test_normalize_engine_name(self) -> None:
        self.assertEqual(normalize_engine_name("supabase"), "postgresql")
        self.assertEqual(normalize_engine_name("postgres"), "postgresql")
        self.assertEqual(normalize_engine_name("sqlite3"), "sqlite")
        self.assertEqual(normalize_engine_name("aurora-mysql"), "mysql")
        self.assertEqual(normalize_engine_name("mariadb"), "mariadb")

    def test_classify_default_values(self) -> None:
        # No default
        d_none = classify_default_value(None, "postgresql")
        self.assertEqual(d_none.kind, DefaultKind.NO_DEFAULT)

        # Literal string
        d_str = classify_default_value("'active'", "postgresql")
        self.assertEqual(d_str.kind, DefaultKind.LITERAL)
        self.assertEqual(d_str.raw_expression, "'active'")

        # Literal number
        d_num = classify_default_value("42", "sqlite")
        self.assertEqual(d_num.kind, DefaultKind.LITERAL)

        # Standard SQL Expression
        d_now = classify_default_value("CURRENT_TIMESTAMP", "mysql")
        self.assertEqual(d_now.kind, DefaultKind.EXPRESSION)

        # UUID expression
        d_uuid = classify_default_value("gen_random_uuid()", "postgresql")
        self.assertEqual(d_uuid.kind, DefaultKind.EXPRESSION)

        # Parenthesized expression
        d_expr = classify_default_value("(price * tax)", "sqlite")
        self.assertEqual(d_expr.kind, DefaultKind.EXPRESSION)

    def test_extract_identity_metadata_postgres_sequence(self) -> None:
        col = make_test_column("t", "id", 1, default_val="nextval('accounts_id_seq'::regclass)", engine="postgresql")
        ident = extract_identity_metadata(col, "postgresql")
        self.assertFalse(ident.is_identity)
        self.assertTrue(ident.is_auto_increment)
        self.assertEqual(ident.strategy, "SEQUENCE")
        self.assertEqual(ident.sequence_name, "accounts_id_seq")

    def test_extract_identity_metadata_mysql_auto_increment(self) -> None:
        col = make_test_column("t", "id", 1, extra={"is_auto_increment": True}, engine="mysql")
        ident = extract_identity_metadata(col, "mysql")
        self.assertTrue(ident.is_auto_increment)
        self.assertEqual(ident.strategy, "AUTO_INCREMENT")

    def test_extract_identity_metadata_sqlite_rowid(self) -> None:
        col = make_test_column("t", "row_id", 1, extra={"is_rowid_alias": True}, engine="sqlite")
        ident = extract_identity_metadata(col, "sqlite")
        self.assertTrue(ident.is_auto_increment)
        self.assertEqual(ident.strategy, "ROWID")


if __name__ == "__main__":
    unittest.main()
