"""Unit Tests for DERA MySQL-Family Type Categorization & Parsing.

Validates:
- Type category classification across MySQL and MariaDB data types
- Unsigned, zerofill, and boolean alias (tinyint(1)) extraction
- ENUM and SET member parsing
"""

import unittest

from dera_connectors.mysql_family.types import (
    MySqlTypeCategory,
    categorize_mysql_type,
    parse_column_type_attributes,
)


class TestMySqlFamilyTypes(unittest.TestCase):
    """Test suite validating data type categorization and column attribute parsing."""

    def test_type_categorization(self) -> None:
        """Verify categorization of standard and extended MySQL/MariaDB types."""
        self.assertEqual(categorize_mysql_type("int"), MySqlTypeCategory.INTEGER)
        self.assertEqual(categorize_mysql_type("bigint unsigned"), MySqlTypeCategory.INTEGER)
        self.assertEqual(categorize_mysql_type("decimal(10,2)"), MySqlTypeCategory.DECIMAL)
        self.assertEqual(categorize_mysql_type("double"), MySqlTypeCategory.FLOAT)
        self.assertEqual(categorize_mysql_type("varchar(255)"), MySqlTypeCategory.STRING)
        self.assertEqual(categorize_mysql_type("longtext"), MySqlTypeCategory.STRING)
        self.assertEqual(categorize_mysql_type("blob"), MySqlTypeCategory.BINARY)
        self.assertEqual(categorize_mysql_type("datetime"), MySqlTypeCategory.DATETIME)
        self.assertEqual(categorize_mysql_type("json"), MySqlTypeCategory.JSON)
        self.assertEqual(categorize_mysql_type("enum('a','b')"), MySqlTypeCategory.ENUM)
        self.assertEqual(categorize_mysql_type("set('r','w')"), MySqlTypeCategory.SET)
        self.assertEqual(categorize_mysql_type("point"), MySqlTypeCategory.SPATIAL)

    def test_boolean_alias_detection(self) -> None:
        """Verify tinyint(1) is recognized as boolean alias and boolean category."""
        self.assertEqual(categorize_mysql_type("tinyint(1)"), MySqlTypeCategory.BOOLEAN)

        attrs = parse_column_type_attributes("tinyint(1)", "tinyint")
        self.assertTrue(attrs["is_boolean_alias"])
        self.assertFalse(attrs["is_unsigned"])

    def test_unsigned_and_zerofill_parsing(self) -> None:
        """Verify unsigned and zerofill attributes are correctly parsed."""
        attrs = parse_column_type_attributes("int(10) unsigned zerofill", "int")
        self.assertTrue(attrs["is_unsigned"])
        self.assertTrue(attrs["is_zerofill"])
        self.assertFalse(attrs["is_boolean_alias"])

    def test_enum_member_parsing(self) -> None:
        """Verify enum literal items are parsed with unescaping."""
        attrs = parse_column_type_attributes("enum('draft','published','archived')", "enum")
        self.assertEqual(attrs["enum_values"], ["draft", "published", "archived"])

    def test_set_member_parsing(self) -> None:
        """Verify set member tokens are extracted accurately."""
        attrs = parse_column_type_attributes("set('read','write','execute')", "set")
        self.assertEqual(attrs["set_members"], ["read", "write", "execute"])
