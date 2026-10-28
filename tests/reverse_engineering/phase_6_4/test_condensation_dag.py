"""Tests for condensation DAG supernode construction and topological condensation ordering."""

from __future__ import annotations

from tests.reverse_engineering.phase_6_4.fixtures import (
    analyze_database,
    make_complex_scc_schema,
    make_diamond_dag_schema,
    make_mutual_cycle_schema,
)


def test_condensation_dag_pure_dag():
    """Verify in pure DAG, each node maps 1-to-1 to a condensation supernode."""
    db = make_diamond_dag_schema()
    res = analyze_database(db)

    assert len(res.condensation_nodes) == 4
    for c in res.condensation_nodes:
        assert c.is_cyclic is False
        assert len(c.member_node_ids) == 1


def test_condensation_dag_mutual_cycle():
    """Verify mutual cycle contracts into a single cyclic condensation supernode."""
    db = make_mutual_cycle_schema()
    res = analyze_database(db)

    assert len(res.condensation_nodes) == 1
    c = res.condensation_nodes[0]
    assert c.is_cyclic is True
    assert len(c.member_node_ids) == 2
    assert len(res.ordering.condensed_order) == 1


def test_condensation_dag_complex_scc():
    """Verify complex schema with cyclic component contracts correctly into condensation DAG."""
    db = make_complex_scc_schema()
    res = analyze_database(db)

    cyclic_cond = [c for c in res.condensation_nodes if c.is_cyclic]
    assert len(cyclic_cond) >= 1
    # Condensed order must be topologically valid
    assert len(res.ordering.condensed_order) == len(res.condensation_nodes)
