"""Tests verifying cross-engine relationship graph construction across PostgreSQL, SQLite, MySQL, and MariaDB."""

from __future__ import annotations

import pytest
from dera.reverse_engineering.graph.builder import ForeignKeyGraphBuilder

from tests.reverse_engineering.phase_6_3.fixtures import make_simple_fk_schema


@pytest.mark.parametrize("engine", ["postgresql", "sqlite", "mysql", "mariadb"])
def test_cross_engine_graph_construction(engine: str):
    """Verify equivalent relationship structures produce compliant graphs across all engines."""
    db = make_simple_fk_schema(engine=engine)
    graph = ForeignKeyGraphBuilder.from_canonical(db)

    assert graph.engine == engine
    assert graph.node_count == 2
    assert graph.edge_count == 1
    assert graph.capability_profile.engine == engine

    # Verify dialect-specific capability assertions
    if engine == "sqlite":
        assert graph.capability_profile.is_enforcement_guaranteed is False
        assert graph.capability_profile.supports_cross_schema_fk is False
    elif engine in ("mysql", "mariadb"):
        assert graph.capability_profile.supports_cross_schema_fk is True
        assert graph.capability_profile.supports_deferrable is False
    elif engine == "postgresql":
        assert graph.capability_profile.supports_deferrable is True
        assert graph.capability_profile.supports_cross_schema_fk is True

    # Referential integrity holds across all engines
    cust = graph.get_node_by_name("customers")
    orders = graph.get_node_by_name("orders")
    assert cust is not None
    assert orders is not None
    assert len(graph.relationships_between(orders.object_id, cust.object_id)) == 1
