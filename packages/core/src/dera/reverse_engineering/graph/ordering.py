"""DERA Reverse Engineering — Phase 6.3 Deterministic Graph Ordering.

Enforces strictly stable, reproducible ordering across all graph collections:
table nodes, foreign key edges, column mappings, unresolved references, and validation findings.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from dera.reverse_engineering.graph.edges import ColumnPairMapping, ForeignKeyEdge
from dera.reverse_engineering.graph.nodes import TableNode


def sort_table_nodes(nodes: Iterable[TableNode]) -> tuple[TableNode, ...]:
    """Sort table nodes deterministically by (namespace_name, native_name, object_id)."""
    return tuple(
        sorted(
            nodes,
            key=lambda n: (
                n.namespace_name.lower(),
                n.native_name.lower(),
                str(n.object_id),
            ),
        )
    )


def sort_foreign_key_edges(edges: Iterable[ForeignKeyEdge]) -> tuple[ForeignKeyEdge, ...]:
    """Sort foreign key edges deterministically by source table, target table, name, and object_id."""
    return tuple(
        sorted(
            edges,
            key=lambda e: (
                e.source_namespace.lower(),
                e.source_table_name.lower(),
                e.referenced_namespace.lower(),
                e.referenced_table_name.lower(),
                e.native_name.lower(),
                str(e.object_id),
            ),
        )
    )


def sort_column_pairs(pairs: Iterable[ColumnPairMapping]) -> tuple[ColumnPairMapping, ...]:
    """Sort column pair mappings strictly by declared ordinal position."""
    return tuple(sorted(pairs, key=lambda p: (p.ordinal_position, p.source_column_name, p.referenced_column_name)))


def sort_unresolved_references(refs: Iterable[Any]) -> tuple[Any, ...]:
    """Sort unresolved references deterministically."""
    return tuple(
        sorted(
            refs,
            key=lambda r: (
                getattr(r, "source_namespace", "").lower(),
                getattr(r, "source_table_name", "").lower(),
                getattr(r, "native_name", "").lower(),
                str(getattr(r, "foreign_key_id", "")),
            ),
        )
    )


def sort_validation_findings(findings: Iterable[Any]) -> tuple[Any, ...]:
    """Sort validation findings deterministically by severity, code, and object_id."""
    severity_order = {"error": 0, "warning": 1, "info": 2}
    return tuple(
        sorted(
            findings,
            key=lambda f: (
                severity_order.get(str(getattr(f, "severity", "")).lower(), 99),
                str(getattr(f, "code", "")),
                str(getattr(f, "object_id", "") or ""),
                str(getattr(f, "message", "")),
            ),
        )
    )
