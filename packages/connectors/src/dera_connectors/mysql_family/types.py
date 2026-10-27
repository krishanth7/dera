"""DERA MySQL-Family Connectors — Data Type Classification & Normalization.

Preserves native engine column types (e.g. `tinyint(1) unsigned`, `varchar(255)`, `enum(...)`)
while providing structured classification across MySQL and MariaDB dialect variations.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Any


class MySqlTypeCategory(StrEnum):
    """Categorical classification of MySQL/MariaDB data types."""

    INTEGER = "integer"
    DECIMAL = "decimal"
    FLOAT = "float"
    BOOLEAN = "boolean"
    STRING = "string"
    BINARY = "binary"
    DATETIME = "datetime"
    TEMPORAL = "temporal"
    JSON = "json"
    ENUM = "enum"
    SET = "set"
    SPATIAL = "spatial"
    OTHER = "other"


_TYPE_CATEGORY_MAP: dict[str, MySqlTypeCategory] = {
    # Integers
    "tinyint": MySqlTypeCategory.INTEGER,
    "smallint": MySqlTypeCategory.INTEGER,
    "mediumint": MySqlTypeCategory.INTEGER,
    "int": MySqlTypeCategory.INTEGER,
    "integer": MySqlTypeCategory.INTEGER,
    "bigint": MySqlTypeCategory.INTEGER,
    "bit": MySqlTypeCategory.INTEGER,
    # Decimals & Floats
    "decimal": MySqlTypeCategory.DECIMAL,
    "numeric": MySqlTypeCategory.DECIMAL,
    "dec": MySqlTypeCategory.DECIMAL,
    "fixed": MySqlTypeCategory.DECIMAL,
    "float": MySqlTypeCategory.FLOAT,
    "double": MySqlTypeCategory.FLOAT,
    "double precision": MySqlTypeCategory.FLOAT,
    "real": MySqlTypeCategory.FLOAT,
    # Strings
    "char": MySqlTypeCategory.STRING,
    "varchar": MySqlTypeCategory.STRING,
    "tinytext": MySqlTypeCategory.STRING,
    "text": MySqlTypeCategory.STRING,
    "mediumtext": MySqlTypeCategory.STRING,
    "longtext": MySqlTypeCategory.STRING,
    # Binaries
    "binary": MySqlTypeCategory.BINARY,
    "varbinary": MySqlTypeCategory.BINARY,
    "tinyblob": MySqlTypeCategory.BINARY,
    "blob": MySqlTypeCategory.BINARY,
    "mediumblob": MySqlTypeCategory.BINARY,
    "longblob": MySqlTypeCategory.BINARY,
    # Temporals
    "date": MySqlTypeCategory.DATETIME,
    "time": MySqlTypeCategory.DATETIME,
    "datetime": MySqlTypeCategory.DATETIME,
    "timestamp": MySqlTypeCategory.DATETIME,
    "year": MySqlTypeCategory.DATETIME,
    # Complex
    "json": MySqlTypeCategory.JSON,
    "enum": MySqlTypeCategory.ENUM,
    "set": MySqlTypeCategory.SET,
    # Spatial
    "geometry": MySqlTypeCategory.SPATIAL,
    "point": MySqlTypeCategory.SPATIAL,
    "linestring": MySqlTypeCategory.SPATIAL,
    "polygon": MySqlTypeCategory.SPATIAL,
    "multipoint": MySqlTypeCategory.SPATIAL,
    "multilinestring": MySqlTypeCategory.SPATIAL,
    "multipolygon": MySqlTypeCategory.SPATIAL,
    "geomcollection": MySqlTypeCategory.SPATIAL,
    "geometrycollection": MySqlTypeCategory.SPATIAL,
}


def categorize_mysql_type(data_type: str) -> MySqlTypeCategory:
    """Classify a MySQL or MariaDB data type into a standard category.

    Parameters
    ----------
    data_type : str
        Data type expression or type name.

    Returns
    -------
    MySqlTypeCategory
        Identified type category.
    """
    clean = data_type.strip().lower()
    if clean.startswith("tinyint(1)"):
        return MySqlTypeCategory.BOOLEAN

    # Remove modifiers and parenthesized lengths/precisions
    base_type = clean.split("(")[0].split()[0]
    return _TYPE_CATEGORY_MAP.get(base_type, MySqlTypeCategory.OTHER)


def classify_mysql_type(data_type: str) -> MySqlTypeCategory:
    """Alias for categorize_mysql_type."""
    return categorize_mysql_type(data_type)


def parse_column_type_attributes(
    col_type_or_data_type: str,
    data_type_or_col_type: str | None = None,
    extra: str | None = None,
) -> dict[str, Any]:
    """Extract structured dialect attributes from MySQL column metadata.

    Accepts arguments in either (column_type, data_type) or (data_type, column_type) order.
    """
    # Detect which argument is the full column type (containing parentheses or extra keywords)
    arg1 = col_type_or_data_type.strip().lower()
    arg2 = (data_type_or_col_type or "").strip().lower()

    if "(" in arg1 or "unsigned" in arg1 or "zerofill" in arg1 or not arg2:
        column_type = col_type_or_data_type
        data_type = data_type_or_col_type or arg1.split("(")[0].split()[0]
    else:
        column_type = data_type_or_col_type or col_type_or_data_type
        data_type = col_type_or_data_type

    clean_col_type = column_type.strip().lower()
    is_unsigned = "unsigned" in clean_col_type
    is_zerofill = "zerofill" in clean_col_type
    is_auto_increment = "auto_increment" in (extra or "").lower()
    is_boolean_alias = clean_col_type.startswith("tinyint(1)")

    # Parse enum / set members
    enum_values: list[str] = []
    set_members: list[str] = []
    if clean_col_type.startswith(("enum(", "set(")) and clean_col_type.endswith(")"):
        is_enum = clean_col_type.startswith("enum(")
        inner = column_type[clean_col_type.find("(") + 1 : -1]
        for part in inner.split(","):
            part_str = part.strip()
            if part_str.startswith(("'", '"')) and part_str.endswith(("'", '"')):
                val = part_str[1:-1]
            else:
                val = part_str
            if is_enum:
                enum_values.append(val)
            else:
                set_members.append(val)

    category = categorize_mysql_type(data_type if not is_boolean_alias else "tinyint(1)")

    return {
        "category": category.value,
        "is_unsigned": is_unsigned,
        "is_zerofill": is_zerofill,
        "is_auto_increment": is_auto_increment,
        "is_boolean_alias": is_boolean_alias,
        "enum_values": enum_values if enum_values else None,
        "set_members": set_members if set_members else None,
        "allowed_values": (enum_values or set_members) or None,
    }
