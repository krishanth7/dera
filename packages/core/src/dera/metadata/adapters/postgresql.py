"""DERA Canonical Metadata Normalization & Identity — PostgreSQL Adapter.

Normalizes PostgreSQL and Supabase PostgreSQL catalog types, default expressions,
index terms, arrays, and domains into canonical schema models.
"""

from __future__ import annotations

import re

from dera.metadata.enums import CanonicalTypeCategory, GenerationMode, IndexType


class PostgresqlMetadataAdapter:
    """Specialized metadata adapter for PostgreSQL and Supabase catalog output."""

    @staticmethod
    def categorize_type(data_type: str) -> CanonicalTypeCategory:
        """Categorize native PostgreSQL type string into CanonicalTypeCategory."""
        dt = data_type.strip().lower()

        # Array types (e.g. integer[], text[], _int4)
        if dt.endswith("[]") or dt.startswith("_"):
            return CanonicalTypeCategory.ARRAY

        # Strip modifiers like (255) or (10,2)
        base = re.sub(r"\(.*?\)", "", dt).strip()

        # Integers
        if base in (
            "smallint",
            "integer",
            "bigint",
            "int",
            "int2",
            "int4",
            "int8",
            "serial",
            "bigserial",
            "smallserial",
        ):
            return CanonicalTypeCategory.INTEGER

        # Decimals
        if base in ("numeric", "decimal"):
            return CanonicalTypeCategory.DECIMAL

        # Floats
        if base in ("real", "double precision", "float", "float4", "float8"):
            return CanonicalTypeCategory.FLOAT

        # Boolean
        if base in ("boolean", "bool"):
            return CanonicalTypeCategory.BOOLEAN

        # Strings & Text
        if base in (
            "character varying",
            "varchar",
            "character",
            "char",
            "text",
            "citext",
            "name",
            "bpchar",
        ):
            return CanonicalTypeCategory.TEXT

        # Binary
        if base in ("bytea", "bit", "bit varying", "varbit"):
            return CanonicalTypeCategory.BINARY

        # Date & Time
        if base == "date":
            return CanonicalTypeCategory.DATE
        if base in ("time", "timetz", "time without time zone", "time with time zone"):
            return CanonicalTypeCategory.TIME
        if base in (
            "timestamp",
            "timestamptz",
            "timestamp without time zone",
            "timestamp with time zone",
        ):
            return CanonicalTypeCategory.TIMESTAMP

        # JSON
        if base in ("json", "jsonb"):
            return CanonicalTypeCategory.JSON

        # UUID
        if base == "uuid":
            return CanonicalTypeCategory.UUID

        # Spatial
        if base in (
            "point",
            "line",
            "lseg",
            "box",
            "path",
            "polygon",
            "circle",
            "geometry",
            "geography",
        ):
            return CanonicalTypeCategory.SPATIAL

        return CanonicalTypeCategory.OTHER

    @staticmethod
    def parse_generation_mode(extra_or_expr: str | None) -> GenerationMode:
        """Detect PostgreSQL generated column storage mode."""
        if not extra_or_expr:
            return GenerationMode.NONE
        s = extra_or_expr.lower()
        if "stored" in s or "always" in s:
            return GenerationMode.STORED
        return GenerationMode.NONE

    @staticmethod
    def parse_index_type(access_method: str | None) -> IndexType:
        """Map PostgreSQL AM to canonical IndexType."""
        if not access_method:
            return IndexType.BTREE
        am = access_method.strip().upper()
        if am in IndexType.__members__:
            return IndexType(am)
        return IndexType.OTHER
