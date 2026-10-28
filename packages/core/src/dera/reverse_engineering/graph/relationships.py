"""DERA Reverse Engineering — Phase 6.3 Relationship Query Helpers.

Provides deterministic query utilities for discovering and filtering foreign key relationships
and direct table neighbors.
"""

from __future__ import annotations

from collections.abc import Iterable

from dera.metadata.identity import ObjectId
from dera.reverse_engineering.graph.edges import ForeignKeyEdge
from dera.reverse_engineering.graph.ordering import sort_foreign_key_edges


def outgoing_relationships(
    edges: Iterable[ForeignKeyEdge],
    table_id: ObjectId,
) -> tuple[ForeignKeyEdge, ...]:
    """Return all foreign key edges declared by the given table, stably sorted."""
    filtered = [e for e in edges if e.source_table_id == table_id]
    return sort_foreign_key_edges(filtered)


def incoming_relationships(
    edges: Iterable[ForeignKeyEdge],
    table_id: ObjectId,
) -> tuple[ForeignKeyEdge, ...]:
    """Return all foreign key edges referencing the given table, stably sorted."""
    filtered = [e for e in edges if e.referenced_table_id == table_id]
    return sort_foreign_key_edges(filtered)


def relationships_between(
    edges: Iterable[ForeignKeyEdge],
    source_table_id: ObjectId,
    referenced_table_id: ObjectId,
) -> tuple[ForeignKeyEdge, ...]:
    """Return all foreign key edges from source_table_id to referenced_table_id, stably sorted."""
    filtered = [
        e
        for e in edges
        if e.source_table_id == source_table_id and e.referenced_table_id == referenced_table_id
    ]
    return sort_foreign_key_edges(filtered)


def outgoing_neighbors(
    edges: Iterable[ForeignKeyEdge],
    table_id: ObjectId,
) -> tuple[ObjectId, ...]:
    """Return distinct referenced table ObjectIds for foreign keys declared by table_id, stably sorted."""
    targets = {e.referenced_table_id for e in edges if e.source_table_id == table_id and e.referenced_table_id is not None}
    return tuple(sorted(targets, key=lambda oid: str(oid)))


def incoming_neighbors(
    edges: Iterable[ForeignKeyEdge],
    table_id: ObjectId,
) -> tuple[ObjectId, ...]:
    """Return distinct source table ObjectIds that reference table_id via foreign key, stably sorted."""
    sources = {e.source_table_id for e in edges if e.referenced_table_id == table_id}
    return tuple(sorted(sources, key=lambda oid: str(oid)))


def all_neighbors(
    edges: Iterable[ForeignKeyEdge],
    table_id: ObjectId,
) -> tuple[ObjectId, ...]:
    """Return distinct table ObjectIds connected either incoming or outgoing with table_id, stably sorted."""
    combined = set(outgoing_neighbors(edges, table_id)) | set(incoming_neighbors(edges, table_id))
    return tuple(sorted(combined, key=lambda oid: str(oid)))
