"""Tests for bounded BFS, DFS graph traversal and weakly connected components."""

from __future__ import annotations

import pytest
from dera.metadata.enums import ObjectKind
from dera.metadata.identity import compute_stable_object_id
from dera.reverse_engineering.graph.builder import ForeignKeyGraphBuilder
from dera.reverse_engineering.graph.edges import ColumnPairMapping, ForeignKeyEdge
from dera.reverse_engineering.graph.errors import TraversalLimitExceededError
from dera.reverse_engineering.graph.limits import GraphResourceLimits
from dera.reverse_engineering.graph.nodes import TableNode
from dera.reverse_engineering.graph.traversal import (
    TraversalDirection,
    TraversalStrategy,
)

from tests.reverse_engineering.phase_6_3.fixtures import make_graph_provenance


def make_chain_graph():
    """Constructs t1 -> t2 -> t3 -> t4 with an isolated t5."""
    prov = make_graph_provenance()
    db_id = compute_stable_object_id("postgresql", ObjectKind.DATABASE, "chain_db")
    builder = ForeignKeyGraphBuilder(
        database_id=db_id, database_name="chain_db", engine="postgresql"
    )

    nodes = [
        TableNode(
            object_id=compute_stable_object_id("postgresql", ObjectKind.TABLE, f"t{i}"),
            native_name=f"t{i}",
            provenance=prov,
        )
        for i in range(1, 6)
    ]
    for n in nodes:
        builder.add_node(n)

    p = ColumnPairMapping(
        source_column_name="ref_id", referenced_column_name="id", ordinal_position=1
    )
    for i in range(1, 4):
        builder.add_edge(
            ForeignKeyEdge(
                object_id=compute_stable_object_id(
                    "postgresql", ObjectKind.FOREIGN_KEY, f"fk_t{i}_t{i + 1}"
                ),
                native_name=f"fk_t{i}_t{i + 1}",
                source_table_id=nodes[i - 1].object_id,
                referenced_table_id=nodes[i].object_id,
                source_table_name=f"t{i}",
                referenced_table_name=f"t{i + 1}",
                column_pairs=(p,),
                provenance=prov,
            )
        )

    return builder.build(), nodes


def test_bfs_traversal_outgoing():
    graph, nodes = make_chain_graph()
    res = graph.traverse(
        start_table_id=nodes[0].object_id,
        direction=TraversalDirection.OUTGOING,
        strategy=TraversalStrategy.BFS,
    )

    expected_ids = (nodes[0].object_id, nodes[1].object_id, nodes[2].object_id, nodes[3].object_id)
    assert res.visited_nodes == expected_ids
    assert len(res.traversed_edges) == 3
    assert res.max_depth_reached == 3
    assert not res.is_truncated


def test_dfs_traversal_outgoing():
    graph, nodes = make_chain_graph()
    res = graph.traverse(
        start_table_id=nodes[0].object_id,
        direction=TraversalDirection.OUTGOING,
        strategy=TraversalStrategy.DFS,
    )

    expected_ids = (nodes[0].object_id, nodes[1].object_id, nodes[2].object_id, nodes[3].object_id)
    assert res.visited_nodes == expected_ids
    assert len(res.traversed_edges) == 3


def test_traversal_incoming_direction():
    graph, nodes = make_chain_graph()
    # Starting at t4 incoming should reach t3, t2, t1
    res = graph.traverse(
        start_table_id=nodes[3].object_id,
        direction=TraversalDirection.INCOMING,
        strategy=TraversalStrategy.BFS,
    )
    expected_ids = (nodes[3].object_id, nodes[2].object_id, nodes[1].object_id, nodes[0].object_id)
    assert res.visited_nodes == expected_ids


def test_traversal_resource_limits_depth():
    graph, nodes = make_chain_graph()
    limits = GraphResourceLimits(max_traversal_depth=1)
    res = graph.traverse(start_table_id=nodes[0].object_id, limits=limits)

    # With max_traversal_depth=1, only t1 and t2 should be visited
    assert res.visited_nodes == (nodes[0].object_id, nodes[1].object_id)


def test_traversal_resource_limits_max_visited_nodes_exception():
    graph, nodes = make_chain_graph()
    limits = GraphResourceLimits(max_visited_nodes=2)
    with pytest.raises(TraversalLimitExceededError):
        graph.traverse(start_table_id=nodes[0].object_id, limits=limits, raise_on_limit=True)


def test_weakly_connected_components():
    graph, nodes = make_chain_graph()
    wcc = graph.weakly_connected_components()
    # Should have 2 components: {t1, t2, t3, t4} and {t5}
    assert len(wcc) == 2

    comp_sizes = sorted([len(c) for c in wcc])
    assert comp_sizes == [1, 4]
