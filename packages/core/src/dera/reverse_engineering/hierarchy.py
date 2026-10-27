"""DERA Reverse Engineering — Phase 6.1 Hierarchical Navigation.

Provides stable, deterministic hierarchical navigation over the object registry,
allowing traversal from database → namespace → tables → columns/constraints/indexes/triggers.

All navigation is based on registered ObjectIds. No direct database connections
are made. Navigation order is deterministic (alphabetic by name, then by ObjectId).
"""

from __future__ import annotations

from dera.metadata.models.column import CanonicalColumn
from dera.metadata.models.constraint import CanonicalConstraint
from dera.metadata.models.database import CanonicalDatabase
from dera.metadata.models.index import CanonicalIndex
from dera.metadata.models.namespace import CanonicalNamespace
from dera.metadata.models.relationship import CanonicalForeignKey
from dera.metadata.models.table import CanonicalTable
from dera.metadata.models.trigger import CanonicalTrigger
from dera.metadata.models.view import CanonicalView
from dera.reverse_engineering.registry import ObjectRegistry


class SchemaHierarchy:
    """Hierarchical navigation helper for a schema object registry.

    Provides stable, deterministic traversal from database → namespaces →
    tables → columns/constraints/indexes/triggers/views.

    All results are returned as sorted tuples to guarantee deterministic output.
    """

    __slots__ = ("_registry",)

    def __init__(self, registry: ObjectRegistry) -> None:
        """Initialise with an already-populated ObjectRegistry.

        Args:
            registry: Fully constructed and populated ObjectRegistry.
        """
        self._registry = registry

    # ------------------------------------------------------------------
    # Database level
    # ------------------------------------------------------------------

    def database(self, database_id: str) -> CanonicalDatabase:
        """Return the CanonicalDatabase for the given ObjectId."""
        return self._registry.get_database(database_id)

    def namespaces(self, database_id: str) -> tuple[CanonicalNamespace, ...]:
        """Return all namespaces belonging to the given database, sorted by name."""
        db = self._registry.get_database(database_id)
        return tuple(sorted(db.namespaces, key=lambda ns: (ns.name.lower(), ns.name)))

    # ------------------------------------------------------------------
    # Namespace level
    # ------------------------------------------------------------------

    def tables(self, namespace_id: str) -> tuple[CanonicalTable, ...]:
        """Return all tables in the given namespace, sorted by name."""
        ns = self._registry.get_namespace(namespace_id)
        return tuple(sorted(ns.tables, key=lambda t: (t.name.lower(), t.name)))

    def views(self, namespace_id: str) -> tuple[CanonicalView, ...]:
        """Return all views in the given namespace, sorted by name."""
        ns = self._registry.get_namespace(namespace_id)
        return tuple(sorted(ns.views, key=lambda v: (v.name.lower(), v.name)))

    # ------------------------------------------------------------------
    # Table level
    # ------------------------------------------------------------------

    def columns(self, table_id: str) -> tuple[CanonicalColumn, ...]:
        """Return all columns in the given table, sorted by ordinal position."""
        table = self._registry.get_table(table_id)
        return tuple(sorted(table.columns, key=lambda c: (c.ordinal_position, c.name.lower())))

    def primary_key(self, table_id: str) -> CanonicalConstraint | None:
        """Return the primary key constraint of the given table, or None."""
        table = self._registry.get_table(table_id)
        return table.primary_key

    def unique_constraints(self, table_id: str) -> tuple[CanonicalConstraint, ...]:
        """Return unique constraints for the given table, sorted by name."""
        table = self._registry.get_table(table_id)
        return tuple(sorted(table.unique_constraints, key=lambda c: (c.name.lower(), c.name)))

    def check_constraints(self, table_id: str) -> tuple[CanonicalConstraint, ...]:
        """Return check constraints for the given table, sorted by name."""
        table = self._registry.get_table(table_id)
        return tuple(sorted(table.check_constraints, key=lambda c: (c.name.lower(), c.name)))

    def all_constraints(self, table_id: str) -> tuple[CanonicalConstraint, ...]:
        """Return all non-FK constraints for the given table (PK + UNIQUE + CHECK), sorted."""
        table = self._registry.get_table(table_id)
        all_constraints: list[CanonicalConstraint] = []
        if table.primary_key is not None:
            all_constraints.append(table.primary_key)
        all_constraints.extend(table.unique_constraints)
        all_constraints.extend(table.check_constraints)
        return tuple(sorted(all_constraints, key=lambda c: (c.name.lower(), c.name)))

    def foreign_keys(self, table_id: str) -> tuple[CanonicalForeignKey, ...]:
        """Return foreign keys originating from the given table, sorted by name."""
        table = self._registry.get_table(table_id)
        return tuple(sorted(table.foreign_keys, key=lambda fk: (fk.name.lower(), fk.name)))

    def indexes(self, table_id: str) -> tuple[CanonicalIndex, ...]:
        """Return indexes on the given table, sorted by primary status then name."""
        table = self._registry.get_table(table_id)
        return tuple(
            sorted(
                table.indexes,
                key=lambda idx: (
                    0 if idx.is_primary else 1,
                    0 if idx.is_unique else 1,
                    idx.name.lower(),
                ),
            )
        )

    def triggers(self, table_id: str) -> tuple[CanonicalTrigger, ...]:
        """Return triggers on the given table, sorted by name."""
        table = self._registry.get_table(table_id)
        return tuple(sorted(table.triggers, key=lambda tr: (tr.name.lower(), tr.name)))

    # ------------------------------------------------------------------
    # Cross-schema navigation
    # ------------------------------------------------------------------

    def all_tables_in_database(self, database_id: str) -> tuple[CanonicalTable, ...]:
        """Return all tables across all namespaces in the database, sorted by
        namespace name then table name.
        """
        db = self._registry.get_database(database_id)
        result: list[CanonicalTable] = []
        for ns in sorted(db.namespaces, key=lambda n: (n.name.lower(), n.name)):
            result.extend(sorted(ns.tables, key=lambda t: (t.name.lower(), t.name)))
        return tuple(result)

    def all_views_in_database(self, database_id: str) -> tuple[CanonicalView, ...]:
        """Return all views across all namespaces in the database."""
        db = self._registry.get_database(database_id)
        result: list[CanonicalView] = []
        for ns in sorted(db.namespaces, key=lambda n: (n.name.lower(), n.name)):
            result.extend(sorted(ns.views, key=lambda v: (v.name.lower(), v.name)))
        return tuple(result)

    def all_foreign_keys_in_database(self, database_id: str) -> tuple[CanonicalForeignKey, ...]:
        """Return all foreign keys across all tables in the database, sorted."""
        tables = self.all_tables_in_database(database_id)
        result: list[CanonicalForeignKey] = []
        for table in tables:
            result.extend(sorted(table.foreign_keys, key=lambda fk: (fk.name.lower(), fk.name)))
        return tuple(result)

    def columns_of_table(self, table_id: str) -> tuple[CanonicalColumn, ...]:
        """Alias for columns() — returns columns sorted by ordinal position."""
        return self.columns(table_id)

    # ------------------------------------------------------------------
    # Registry reference
    # ------------------------------------------------------------------

    @property
    def registry(self) -> ObjectRegistry:
        """The backing object registry."""
        return self._registry
