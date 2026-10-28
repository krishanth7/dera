"""Tests for parallel execution level stratification and generational batching."""

from __future__ import annotations

from tests.reverse_engineering.phase_6_4.fixtures import (
    analyze_database,
    make_diamond_dag_schema,
    make_ecommerce_schema,
    make_linear_dag_schema,
)


def test_linear_dag_levels():
    """Verify linear 4-node chain creates 4 distinct sequential levels."""
    db = make_linear_dag_schema()
    res = analyze_database(db)

    assert len(res.ordering.levels) == 4
    for i, lvl in enumerate(res.ordering.levels):
        assert lvl.level == i
        assert len(lvl.node_ids) == 1


def test_diamond_dag_levels():
    """Verify diamond DAG creates 3 parallel levels with branches grouped in level 1."""
    db = make_diamond_dag_schema()
    res = analyze_database(db)
    tbl_map = {t.name: t.id for t in db.namespaces[0].tables}

    levels = res.ordering.levels
    assert len(levels) == 3

    # Level 0: root
    assert len(levels[0].node_ids) == 1
    assert levels[0].node_ids[0] == tbl_map["root"]

    # Level 1: branch_a and branch_b concurrently!
    assert len(levels[1].node_ids) == 2
    assert set(levels[1].node_ids) == {tbl_map["branch_a"], tbl_map["branch_b"]}

    # Level 2: sink
    assert len(levels[2].node_ids) == 1
    assert levels[2].node_ids[0] == tbl_map["sink"]


def test_ecommerce_schema_parallel_levels():
    """Verify multi-table production e-commerce schema partitions into parallel layers."""
    db = make_ecommerce_schema()
    res = analyze_database(db)
    tbl_map = {t.name: t.id for t in db.namespaces[0].tables}

    levels = res.ordering.levels
    assert len(levels) == 3

    # Level 0 roots: users, categories, audit_log
    assert set(levels[0].node_ids) == {
        tbl_map["users"],
        tbl_map["categories"],
        tbl_map["audit_log"],
    }

    # Level 1: products (depends on categories), orders (depends on users)
    assert set(levels[1].node_ids) == {tbl_map["products"], tbl_map["orders"]}

    # Level 2: order_items, reviews
    assert set(levels[2].node_ids) == {tbl_map["order_items"], tbl_map["reviews"]}
