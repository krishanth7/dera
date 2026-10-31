"""DERA Reverse Engineering — Phase 6.6 Deterministic Export Ordering.

Provides stable, canonical tie-breaking and ordering utilities to guarantee
byte-level reproducibility for all export formats.
"""

from __future__ import annotations

from dera.metadata.models import (
    CanonicalColumn,
    CanonicalConstraint,
    CanonicalIndex,
    CanonicalTable,
)
from dera.reverse_engineering.graph.models import ForeignKeyEdge, TableNode


def sort_export_tables(tables: list[CanonicalTable]) -> list[CanonicalTable]:
    """Sort tables deterministically by namespace (schema_name) then table name."""
    return sorted(
        tables,
        key=lambda t: (getattr(t, "schema_name", getattr(t, "namespace", "")) or "", t.name),
    )


def sort_export_columns(columns: list[CanonicalColumn]) -> list[CanonicalColumn]:
    """Sort columns strictly by ordinal position to preserve relational semantics."""
    return sorted(columns, key=lambda c: (c.ordinal_position, c.name))


def sort_export_constraints(constraints: list[CanonicalConstraint]) -> list[CanonicalConstraint]:
    """Sort constraints deterministically by name."""
    return sorted(constraints, key=lambda c: (c.name, str(c.constraint_type)))


def sort_export_indexes(indexes: list[CanonicalIndex]) -> list[CanonicalIndex]:
    """Sort indexes deterministically by name."""
    return sorted(indexes, key=lambda idx: idx.name)


def sort_export_nodes(nodes: list[TableNode]) -> list[TableNode]:
    """Sort graph nodes by namespace then name."""
    return sorted(nodes, key=lambda n: (n.namespace, n.name, n.table_id))


def sort_export_edges(edges: list[ForeignKeyEdge]) -> list[ForeignKeyEdge]:
    """Sort graph edges by source_table_id, referenced_table_id, then native_name."""
    return sorted(
        edges,
        key=lambda e: (
            e.source_table_id,
            getattr(e, "referenced_table_id", getattr(e, "target_table_id", "")),
            e.native_name,
        ),
    )
