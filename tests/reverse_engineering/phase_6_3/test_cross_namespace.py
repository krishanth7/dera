"""Tests for cross-namespace foreign key relationships."""

from __future__ import annotations

from dera.reverse_engineering.graph.builder import ForeignKeyGraphBuilder

from tests.reverse_engineering.phase_6_3.fixtures import make_cross_namespace_schema


def test_cross_namespace_relationship():
    """Verify relationships spanning distinct schemas are correctly tagged and preserved."""
    db = make_cross_namespace_schema()
    graph = ForeignKeyGraphBuilder.from_canonical(db)

    users = graph.get_node_by_name("users", "auth")
    profiles = graph.get_node_by_name("profiles", "app")
    assert users is not None
    assert profiles is not None

    outgoing = graph.outgoing(profiles.object_id)
    assert len(outgoing) == 1
    edge = outgoing[0]

    assert edge.is_cross_namespace is True
    assert edge.source_namespace == "app"
    assert edge.source_table_name == "profiles"
    assert edge.referenced_namespace == "auth"
    assert edge.referenced_table_name == "users"

    assert edge.source_fully_qualified_name == "app.profiles"
    assert edge.referenced_fully_qualified_name == "auth.users"

    # Adjacency indexes cross-namespace correctly
    assert graph.incoming(users.object_id) == (edge,)
