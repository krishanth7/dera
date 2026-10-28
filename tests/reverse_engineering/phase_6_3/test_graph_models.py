"""Tests for Phase 6.3 Foreign Key Graph domain contracts and models."""

from __future__ import annotations

import pytest
from dera.reverse_engineering.graph.builder import ForeignKeyGraphBuilder
from dera.reverse_engineering.graph.edges import ColumnPairMapping, ForeignKeyEdge
from dera.reverse_engineering.graph.models import (
    UnresolvedReason,
    UnresolvedReference,
)
from dera.reverse_engineering.graph.nodes import TableNode
from pydantic import ValidationError

from tests.reverse_engineering.phase_6_3.fixtures import (
    make_graph_provenance,
    make_simple_fk_schema,
)


def test_table_node_immutability():
    """Verify TableNode is frozen and rejects attribute assignment."""
    prov = make_graph_provenance()
    node = TableNode(
        object_id="dera:table:12345",
        native_name="users",
        namespace_name="public",
        column_count=5,
        primary_key_columns=("id",),
        provenance=prov,
    )
    assert node.fully_qualified_name == "public.users"
    with pytest.raises(ValidationError):
        node.native_name = "modified"


def test_foreign_key_edge_immutability():
    """Verify ForeignKeyEdge is frozen and directional attributes are correct."""
    prov = make_graph_provenance()
    pair = ColumnPairMapping(source_column_name="user_id", referenced_column_name="id", ordinal_position=1)
    edge = ForeignKeyEdge(
        object_id="dera:foreign_key:54321",
        native_name="fk_orders_user",
        source_table_id="dera:table:orders",
        referenced_table_id="dera:table:users",
        source_table_name="orders",
        referenced_table_name="users",
        column_pairs=(pair,),
        provenance=prov,
    )
    assert edge.source_columns == ("user_id",)
    assert edge.referenced_columns == ("id",)
    assert edge.source_fully_qualified_name == "public.orders"
    assert edge.referenced_fully_qualified_name == "public.users"
    with pytest.raises(ValidationError):
        edge.native_name = "new_name"


def test_foreign_key_graph_basic_properties():
    """Verify ForeignKeyGraph root model properties, node/edge lookups, and immutability."""
    db = make_simple_fk_schema()
    graph = ForeignKeyGraphBuilder.from_canonical(db)

    assert graph.contract_version == "1.0.0"
    assert graph.database_name == "test_db"
    assert graph.engine == "postgresql"
    assert graph.node_count == 2
    assert graph.edge_count == 1
    assert not graph.is_empty

    cust_node = graph.get_node_by_name("customers", "public")
    assert cust_node is not None
    assert cust_node.native_name == "customers"
    assert graph.has_node(cust_node.object_id)

    ord_node = graph.get_node_by_name("orders", "public")
    assert ord_node is not None

    edges = graph.outgoing(ord_node.object_id)
    assert len(edges) == 1
    assert edges[0].native_name == "fk_orders_customer"

    incoming = graph.incoming(cust_node.object_id)
    assert len(incoming) == 1
    assert incoming[0].native_name == "fk_orders_customer"

    # Verify frozen
    with pytest.raises(ValidationError):
        graph.database_name = "hacked"


def test_unresolved_reference_model():
    """Verify UnresolvedReference audit model captures details correctly."""
    prov = make_graph_provenance()
    unres = UnresolvedReference(
        foreign_key_id="dera:foreign_key:unres",
        native_name="fk_broken",
        source_table_id="dera:table:orders",
        source_table_name="orders",
        referenced_table_name="missing_table",
        declared_source_columns=("cust_id",),
        declared_referenced_columns=("id",),
        reason=UnresolvedReason.REFERENCED_TABLE_NOT_FOUND,
        details="Table missing_table not found in catalog.",
        provenance=prov,
    )
    assert unres.reason == UnresolvedReason.REFERENCED_TABLE_NOT_FOUND
    assert "missing_table" in repr(unres)
