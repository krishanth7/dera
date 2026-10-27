"""DERA Canonical Metadata Normalization & Identity — MariaDB Adapter.

Normalizes MariaDB catalog types, persistent/virtual generated columns,
and JSON alias check constraints.
"""

from __future__ import annotations

from dera.metadata.adapters.mysql import MySqlMetadataAdapter
from dera.metadata.enums import CanonicalTypeCategory, GenerationMode, IndexType


class MariaDbMetadataAdapter:
    """Specialized metadata adapter for MariaDB INFORMATION_SCHEMA output."""

    @staticmethod
    def categorize_type(data_type: str, full_column_type: str = "") -> CanonicalTypeCategory:
        """Categorize native MariaDB data type into CanonicalTypeCategory."""
        # Delegates to MySQL adapter logic, which covers MariaDB syntax
        return MySqlMetadataAdapter.categorize_type(data_type, full_column_type)

    @staticmethod
    def parse_generation_mode(extra_text: str | None) -> GenerationMode:
        """Detect MariaDB generated column storage mode (handles PERSISTENT)."""
        if not extra_text:
            return GenerationMode.NONE
        s = extra_text.lower()
        if "persistent" in s or "stored" in s:
            return GenerationMode.STORED
        if "virtual" in s:
            return GenerationMode.VIRTUAL
        return GenerationMode.NONE

    @staticmethod
    def parse_index_type(index_type_str: str | None) -> IndexType:
        """Map MariaDB index_type to canonical IndexType."""
        return MySqlMetadataAdapter.parse_index_type(index_type_str)
