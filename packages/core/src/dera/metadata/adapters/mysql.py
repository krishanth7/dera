"""DERA Canonical Metadata Normalization & Identity — MySQL Adapter.

Normalizes MySQL catalog types, signed/unsigned attributes, ENUM/SET elements,
functional indexes, and virtual/stored generated columns.
"""

from __future__ import annotations

import re

from dera.metadata.enums import CanonicalTypeCategory, GenerationMode, IndexType


class MySqlMetadataAdapter:
    """Specialized metadata adapter for MySQL INFORMATION_SCHEMA output."""

    @staticmethod
    def categorize_type(data_type: str, full_column_type: str = "") -> CanonicalTypeCategory:
        """Categorize native MySQL data type into CanonicalTypeCategory."""
        dt = data_type.strip().lower()
        full = full_column_type.strip().lower()

        # Boolean alias: tinyint(1)
        if "tinyint(1)" in full or dt == "boolean" or dt == "bool":
            return CanonicalTypeCategory.BOOLEAN

        base = re.sub(r"\(.*?\)", "", dt).strip()

        # Integers
        if base in (
            "tinyint",
            "smallint",
            "mediumint",
            "int",
            "integer",
            "bigint",
            "serial",
        ):
            return CanonicalTypeCategory.INTEGER

        # Decimals
        if base in ("decimal", "numeric", "dec", "fixed"):
            return CanonicalTypeCategory.DECIMAL

        # Floats
        if base in ("float", "double", "double precision", "real"):
            return CanonicalTypeCategory.FLOAT

        # Text / Char
        if base in (
            "char",
            "varchar",
            "tinytext",
            "text",
            "mediumtext",
            "longtext",
        ):
            return CanonicalTypeCategory.TEXT

        # Binary
        if base in (
            "bit",
            "binary",
            "varbinary",
            "tinyblob",
            "blob",
            "mediumblob",
            "longblob",
        ):
            return CanonicalTypeCategory.BINARY

        # Date & Time
        if base in ("date", "year"):
            return CanonicalTypeCategory.DATE
        if base == "time":
            return CanonicalTypeCategory.TIME
        if base in ("datetime", "timestamp"):
            return CanonicalTypeCategory.TIMESTAMP

        # JSON
        if base == "json":
            return CanonicalTypeCategory.JSON

        # Enum & Set
        if base == "enum":
            return CanonicalTypeCategory.ENUM
        if base == "set":
            return CanonicalTypeCategory.SET

        # Spatial
        if base in (
            "geometry",
            "point",
            "linestring",
            "polygon",
            "multipoint",
            "multilinestring",
            "multipolygon",
            "geometrycollection",
        ):
            return CanonicalTypeCategory.SPATIAL

        return CanonicalTypeCategory.OTHER

    @staticmethod
    def parse_generation_mode(extra_text: str | None) -> GenerationMode:
        """Detect MySQL generated column storage mode."""
        if not extra_text:
            return GenerationMode.NONE
        s = extra_text.lower()
        if "stored" in s:
            return GenerationMode.STORED
        if "virtual" in s:
            return GenerationMode.VIRTUAL
        return GenerationMode.NONE

    @staticmethod
    def parse_index_type(index_type_str: str | None) -> IndexType:
        """Map MySQL index_type to canonical IndexType."""
        if not index_type_str:
            return IndexType.BTREE
        it = index_type_str.strip().upper()
        if it in IndexType.__members__:
            return IndexType(it)
        if it == "FULLTEXT":
            return IndexType.FULLTEXT
        if it == "SPATIAL":
            return IndexType.SPATIAL
        return IndexType.OTHER
