"""Regression tests comparing live dependency analysis against verified golden JSON files."""

from __future__ import annotations

from pathlib import Path

import pytest
from dera.reverse_engineering.dependencies.serialization import (
    compute_dependency_hash,
    deserialize_dependency_analysis_from_json,
)

from tests.reverse_engineering.phase_6_4.fixtures import (
    analyze_database,
    make_complex_scc_schema,
    make_diamond_dag_schema,
    make_ecommerce_schema,
    make_indirect_cycle_schema,
    make_linear_dag_schema,
    make_mutual_cycle_schema,
    make_self_referencing_schema,
)

GOLDEN_DIR = Path(__file__).parent / "golden"

TEST_CASES = [
    ("golden_linear_dag.json", make_linear_dag_schema()),
    ("golden_diamond_dag.json", make_diamond_dag_schema()),
    ("golden_self_referencing.json", make_self_referencing_schema()),
    ("golden_mutual_cycle.json", make_mutual_cycle_schema()),
    ("golden_indirect_cycle.json", make_indirect_cycle_schema()),
    ("golden_complex_scc.json", make_complex_scc_schema()),
    ("golden_ecommerce.json", make_ecommerce_schema()),
    ("golden_cross_engine_sqlite.json", make_linear_dag_schema(engine="sqlite")),
]


@pytest.mark.parametrize("golden_file,db", TEST_CASES)
def test_golden_file_parity(golden_file: str, db):
    """Verify live analysis matches stored golden file byte-for-byte and hash-for-hash."""
    golden_path = GOLDEN_DIR / golden_file
    assert golden_path.exists(), f"Missing golden file: {golden_path}"

    with open(golden_path, encoding="utf-8") as f:
        golden_content = f.read()

    golden_result = deserialize_dependency_analysis_from_json(golden_content)
    live_result = analyze_database(db)

    # 1. Compare hashes
    assert compute_dependency_hash(live_result) == compute_dependency_hash(golden_result)

    # 2. Compare structural properties
    assert live_result.is_dag == golden_result.is_dag
    assert live_result.node_count == golden_result.node_count
    assert live_result.edge_count == golden_result.edge_count
    assert live_result.ordering.creation_order == golden_result.ordering.creation_order
    assert live_result.ordering.drop_order == golden_result.ordering.drop_order
    assert len(live_result.ordering.levels) == len(golden_result.ordering.levels)
    assert live_result.cycle_report.cycle_count == golden_result.cycle_report.cycle_count
