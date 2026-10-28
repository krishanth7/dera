"""Tests verifying dependency analysis across PostgreSQL, SQLite, MySQL, and MariaDB."""

from __future__ import annotations

import pytest

from tests.reverse_engineering.phase_6_4.fixtures import (
    analyze_database,
    make_ecommerce_schema,
    make_linear_dag_schema,
)


@pytest.mark.parametrize("engine", ["postgresql", "sqlite", "mysql", "mariadb"])
def test_cross_engine_linear_dag(engine: str):
    """Verify linear DAG analysis behaves identically across all 4 database engines."""
    db = make_linear_dag_schema(engine=engine)
    res = analyze_database(db)

    assert res.is_dag is True
    assert len(res.ordering.creation_order) == 4
    assert len(res.ordering.levels) == 4
    assert len(res.root_node_ids) == 1
    assert len(res.leaf_node_ids) == 1


@pytest.mark.parametrize("engine", ["postgresql", "sqlite", "mysql", "mariadb"])
def test_cross_engine_ecommerce_schema(engine: str):
    """Verify production e-commerce schema analysis across all 4 database engines."""
    db = make_ecommerce_schema(engine=engine)
    res = analyze_database(db)
    tbl_map = {t.name: t.id for t in db.namespaces[0].tables}

    assert res.is_dag is True
    assert len(res.ordering.creation_order) == 7
    assert len(res.ordering.levels) == 3
    assert len(res.isolated_node_ids) == 1
    assert res.isolated_node_ids[0] == tbl_map["audit_log"]
