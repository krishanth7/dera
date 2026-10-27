"""DERA Canonical Metadata Normalization & Identity — Database Model.

Defines the top-level CanonicalDatabase model encapsulating namespaces, tables,
views, and comprehensive schema provenance.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from dera.metadata.models.namespace import CanonicalNamespace
from dera.metadata.models.table import CanonicalTable
from dera.metadata.provenance import MetadataProvenance


class CanonicalDatabase(BaseModel):
    """Top-level canonical metadata model for an inspected database."""

    model_config = ConfigDict(frozen=True)

    id: str = Field(
        ...,
        description="Deterministic canonical ObjectId for this database.",
    )
    name: str = Field(
        ...,
        description="Logical database identifier or connection database name.",
    )
    engine: str = Field(
        ...,
        description="Database engine type (e.g. 'postgresql', 'sqlite', 'mysql', 'mariadb').",
    )
    contract_version: str = Field(
        default="1.0.0",
        description="Version string of the canonical metadata contract.",
    )
    namespaces: tuple[CanonicalNamespace, ...] = Field(
        default_factory=tuple,
        description="Ordered tuple of namespaces/schemas contained within this database.",
    )
    provenance: MetadataProvenance = Field(
        ...,
        description="Root extraction provenance and audit information.",
    )

    def get_namespace(self, name: str) -> CanonicalNamespace | None:
        """Find namespace by case-insensitive name match."""
        target = name.strip().lower()
        for ns in self.namespaces:
            if ns.name.strip().lower() == target:
                return ns
        return None

    def all_tables(self) -> tuple[CanonicalTable, ...]:
        """Convenience method returning a flat tuple of all tables across all namespaces."""
        tables: list[CanonicalTable] = []
        for ns in self.namespaces:
            tables.extend(ns.tables)
        return tuple(tables)

    def find_table(self, schema_name: str, table_name: str) -> CanonicalTable | None:
        """Lookup table by schema name and table name."""
        ns = self.get_namespace(schema_name)
        if ns is None:
            return None
        return ns.get_table(table_name)
