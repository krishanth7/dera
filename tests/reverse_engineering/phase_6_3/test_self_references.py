"""Tests for self-referencing (self-loop) foreign key relationships."""

from __future__ import annotations

from dera.reverse_engineering.graph.builder import ForeignKeyGraphBuilder

from tests.reverse_engineering.phase_6_3.fixtures import make_self_referencing_schema


def test_self_referencing_relationship():
    """Verify self-loop foreign keys where source and referenced table are identical."""
    db = make_self_referencing_schema()
    graph = ForeignKeyGraphBuilder.from_canonical(db)

    cat = graph.get_node_by_name("categories")
    assert cat is not None

    outgoing = graph.outgoing(cat.object_id)
    assert len(outgoing) == 1
    edge = outgoing[0]

    assert edge.is_self_referencing is True
    assert edge.source_table_id == cat.object_id
    assert edge.referenced_table_id == cat.object_id

    # Self-loops appear in both outgoing and incoming
    incoming = graph.incoming(cat.object_id)
    assert len(incoming) == 1
    assert incoming[0] == edge

    # Neighbors handling of self-loop: cat is its own neighbor
    assert graph.outgoing_neighbors(cat.object_id) == (cat.object_id,)
    assert graph.incoming_neighbors(cat.object_id) == (cat.object_id,)

    # Traversal should not loop infinitely
    res = graph.traverse(start_table_id=cat.object_id)
    assert res.visited_nodes == (cat.object_id,)
    assert len(res.traversed_edges) == 1
