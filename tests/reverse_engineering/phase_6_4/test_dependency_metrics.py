"""Tests for dependency metrics, centrality attributes, and root/leaf identification."""

from __future__ import annotations

from tests.reverse_engineering.phase_6_4.fixtures import (
    analyze_database,
    make_diamond_dag_schema,
    make_ecommerce_schema,
    make_linear_dag_schema,
)


def test_linear_dag_metrics():
    """Verify in-degree, out-degree, and depth on a 4-table linear chain."""
    db = make_linear_dag_schema()
    res = analyze_database(db)
    tbl_map = {t.name: t.id for t in db.namespaces[0].tables}

    # t0 is root (in_degree=0, out_degree=1)
    t0_id = tbl_map["t0"]
    assert t0_id in res.root_node_ids
    m0 = res.get_node_metrics(t0_id)
    assert m0 is not None
    assert m0.is_root is True
    assert m0.is_leaf is False
    assert m0.in_degree == 0
    assert m0.out_degree == 1
    assert m0.transitive_dependent_count == 3
    assert m0.depth_level == 0

    # t3 is leaf (in_degree=1, out_degree=0)
    t3_id = tbl_map["t3"]
    assert t3_id in res.leaf_node_ids
    m3 = res.get_node_metrics(t3_id)
    assert m3 is not None
    assert m3.is_leaf is True
    assert m3.is_root is False
    assert m3.in_degree == 1
    assert m3.out_degree == 0
    assert m3.transitive_dependency_count == 3
    assert m3.depth_level == 3


def test_diamond_dag_metrics():
    """Verify transitive ancestor and descendant counts in diamond graph."""
    db = make_diamond_dag_schema()
    res = analyze_database(db)

    root_id = res.root_node_ids[0]
    m_root = res.get_node_metrics(root_id)
    assert m_root.out_degree == 2  # branch_a and branch_b
    assert m_root.transitive_dependent_count == 3  # branch_a, branch_b, sink

    sink_id = res.leaf_node_ids[0]
    m_sink = res.get_node_metrics(sink_id)
    assert m_sink.in_degree == 2  # branch_a and branch_b
    assert m_sink.transitive_dependency_count == 3  # branch_a, branch_b, root


def test_ecommerce_isolated_node_metrics():
    """Verify audit_log is identified as isolated (in_degree=0, out_degree=0)."""
    db = make_ecommerce_schema()
    res = analyze_database(db)
    tbl_map = {t.name: t.id for t in db.namespaces[0].tables}

    assert len(res.isolated_node_ids) == 1
    iso_id = res.isolated_node_ids[0]
    assert iso_id == tbl_map["audit_log"]

    m_iso = res.get_node_metrics(iso_id)
    assert m_iso.is_root is True
    assert m_iso.is_leaf is True
    assert m_iso.in_degree == 0
    assert m_iso.out_degree == 0
    assert m_iso.transitive_dependency_count == 0
    assert m_iso.transitive_dependent_count == 0
