"""Tests for AdjacencyIndex fast O(1) lookups and neighbor discovery."""

from __future__ import annotations

from dera.reverse_engineering.graph.builder import ForeignKeyGraphBuilder

from tests.reverse_engineering.phase_6_3.fixtures import (
    make_parallel_edges_schema,
)


def test_adjacency_index_lookups():
    """Verify O(1) outgoing, incoming, and pairwise between lookups."""
    db = make_parallel_edges_schema()
    graph = ForeignKeyGraphBuilder.from_canonical(db)
    adj = graph.get_adjacency()

    tasks = graph.get_node_by_name("tasks")
    users = graph.get_node_by_name("users")
    assert tasks is not None
    assert users is not None

    # Outgoing from tasks
    out_tasks = adj.get_outgoing(tasks.object_id)
    assert len(out_tasks) == 2

    # Incoming to users
    in_users = adj.get_incoming(users.object_id)
    assert len(in_users) == 2

    # Between tasks and users
    between = adj.get_between(tasks.object_id, users.object_id)
    assert len(between) == 2

    # Between users and tasks (reverse) is empty
    assert len(adj.get_between(users.object_id, tasks.object_id)) == 0


def test_adjacency_neighbor_discovery():
    """Verify distinct outgoing, incoming, and bidirectional neighbor lookups."""
    db = make_parallel_edges_schema()
    graph = ForeignKeyGraphBuilder.from_canonical(db)
    adj = graph.get_adjacency()

    tasks = graph.get_node_by_name("tasks")
    users = graph.get_node_by_name("users")
    assert tasks is not None
    assert users is not None

    # Outgoing neighbors of tasks should be {users} (deduplicated across parallel edges)
    assert adj.outgoing_neighbors(tasks.object_id) == (users.object_id,)
    assert adj.incoming_neighbors(tasks.object_id) == ()

    # Incoming neighbors of users should be {tasks}
    assert adj.incoming_neighbors(users.object_id) == (tasks.object_id,)
    assert adj.outgoing_neighbors(users.object_id) == ()

    # All neighbors
    assert adj.all_neighbors(tasks.object_id) == (users.object_id,)
    assert adj.all_neighbors(users.object_id) == (tasks.object_id,)
