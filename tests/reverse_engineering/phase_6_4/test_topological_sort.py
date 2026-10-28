"""Tests for deterministic Kahn's topological sort and sequence ordering."""

from __future__ import annotations

import pytest
from dera.reverse_engineering.dependencies.analyzer import DependencyAnalyzer
from dera.reverse_engineering.dependencies.errors import CyclicDependencyError
from dera.reverse_engineering.graph.builder import ForeignKeyGraphBuilder

from tests.reverse_engineering.phase_6_4.fixtures import (
    analyze_database,
    make_diamond_dag_schema,
    make_linear_dag_schema,
    make_mutual_cycle_schema,
)


def test_topological_sort_linear_dag():
    """Verify linear DAG creation order (parents before children) and drop order (exact reverse)."""
    db = make_linear_dag_schema()
    res = analyze_database(db)

    assert res.is_dag is True
    creation_order = res.ordering.creation_order
    drop_order = res.ordering.drop_order

    tbl_map = {t.name: t.id for t in db.namespaces[0].tables}

    assert len(creation_order) == 4
    assert drop_order == tuple(reversed(creation_order))

    # Verify t0 is first in creation, t3 is last
    assert creation_order[0] == tbl_map["t0"]
    assert creation_order[3] == tbl_map["t3"]


def test_topological_sort_diamond_dag():
    """Verify diamond DAG: root is created first, sink is created last."""
    db = make_diamond_dag_schema()
    res = analyze_database(db)

    tbl_map = {t.name: t.id for t in db.namespaces[0].tables}
    assert res.is_dag is True
    order = res.ordering.creation_order
    assert len(order) == 4
    assert order[0] == tbl_map["root"]
    assert order[3] == tbl_map["sink"]
    # branch_a and branch_b are in the middle
    middle = {order[1], order[2]}
    assert middle == {tbl_map["branch_a"], tbl_map["branch_b"]}


def test_require_dag_flag():
    """Verify require_dag=True raises CyclicDependencyError on cyclic schemas."""
    db = make_mutual_cycle_schema()
    from dera.reverse_engineering.builder import SchemaBuilder

    schema = SchemaBuilder.from_canonical_database(db)
    graph = ForeignKeyGraphBuilder.from_schema(schema)
    analyzer = DependencyAnalyzer()

    with pytest.raises(CyclicDependencyError) as exc_info:
        analyzer.analyze(graph, schema=schema, require_dag=True)

    assert "cycle" in str(exc_info.value).lower()
    assert len(exc_info.value.cycle_ids) > 0
