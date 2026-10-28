"""Security, resource limit, and immutability tests for Phase 6.4."""

from __future__ import annotations

import pytest
from dera.reverse_engineering.builder import SchemaBuilder
from dera.reverse_engineering.dependencies.analyzer import DependencyAnalyzer
from dera.reverse_engineering.dependencies.errors import DependencyResourceLimitError
from dera.reverse_engineering.dependencies.limits import DependencyResourceLimits
from dera.reverse_engineering.graph.builder import ForeignKeyGraphBuilder

from tests.reverse_engineering.phase_6_4.fixtures import (
    make_ecommerce_schema,
    make_linear_dag_schema,
)


def test_resource_limit_max_nodes_enforced():
    """Verify max_nodes limit stops execution with DependencyResourceLimitError."""
    db = make_ecommerce_schema()  # 7 tables
    schema = SchemaBuilder.from_canonical_database(db)
    graph = ForeignKeyGraphBuilder.from_schema(schema)

    limits = DependencyResourceLimits(max_nodes=5)  # Less than 7
    analyzer = DependencyAnalyzer(limits=limits)

    with pytest.raises(DependencyResourceLimitError):
        analyzer.analyze(graph, schema=schema)


def test_resource_limit_max_edges_enforced():
    """Verify max_edges limit stops execution with DependencyResourceLimitError."""
    db = make_ecommerce_schema()  # 6 FK edges
    schema = SchemaBuilder.from_canonical_database(db)
    graph = ForeignKeyGraphBuilder.from_schema(schema)

    limits = DependencyResourceLimits(max_edges=3)  # Less than 6
    analyzer = DependencyAnalyzer(limits=limits)

    with pytest.raises(DependencyResourceLimitError):
        analyzer.analyze(graph, schema=schema)


def test_zero_database_mutation_policy():
    """Verify that dependency analysis executes strictly in-memory without database sockets."""
    db = make_linear_dag_schema()
    schema = SchemaBuilder.from_canonical_database(db)
    graph = ForeignKeyGraphBuilder.from_schema(schema)

    analyzer = DependencyAnalyzer()
    res = analyzer.analyze(graph, schema=schema)

    # Result contains no socket, cursor, or connection state
    assert not hasattr(res, "connection")
    assert not hasattr(res, "cursor")
    assert not hasattr(res, "execute")
