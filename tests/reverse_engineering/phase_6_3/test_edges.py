"""Tests for ForeignKeyEdge direction, properties, and parallel edge multigraph support."""

from __future__ import annotations

from dera.reverse_engineering.graph.builder import ForeignKeyGraphBuilder

from tests.reverse_engineering.phase_6_3.fixtures import (
    make_parallel_edges_schema,
    make_simple_fk_schema,
)


def test_edge_direction_convention():
    """Verify strictly canonical child -> parent direction convention."""
    db = make_simple_fk_schema()
    graph = ForeignKeyGraphBuilder.from_canonical(db)

    cust = graph.get_node_by_name("customers")
    orders = graph.get_node_by_name("orders")
    assert cust is not None
    assert orders is not None

    # Child (orders) declares FK pointing to Parent (customers)
    outgoing_orders = graph.outgoing(orders.object_id)
    assert len(outgoing_orders) == 1
    edge = outgoing_orders[0]
    assert edge.source_table_id == orders.object_id
    assert edge.referenced_table_id == cust.object_id

    # Parent (customers) has incoming FK edge
    incoming_cust = graph.incoming(cust.object_id)
    assert len(incoming_cust) == 1
    assert incoming_cust[0] == edge


def test_parallel_edges_support():
    """Verify directed multigraph support: multiple foreign keys between same tables are distinct edges."""
    db = make_parallel_edges_schema()
    graph = ForeignKeyGraphBuilder.from_canonical(db)

    tasks = graph.get_node_by_name("tasks")
    users = graph.get_node_by_name("users")
    assert tasks is not None
    assert users is not None

    edges_between = graph.relationships_between(tasks.object_id, users.object_id)
    assert len(edges_between) == 2

    edge_names = {e.native_name for e in edges_between}
    assert edge_names == {"fk_tasks_creator", "fk_tasks_assignee"}

    # Distinct ObjectIds
    assert edges_between[0].object_id != edges_between[1].object_id
