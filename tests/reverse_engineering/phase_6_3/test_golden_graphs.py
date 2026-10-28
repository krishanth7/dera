"""Golden file tests verifying byte-level deterministic serialized foreign key graph snapshots."""

from __future__ import annotations

from pathlib import Path

import pytest
from dera.reverse_engineering.graph.builder import ForeignKeyGraphBuilder
from dera.reverse_engineering.graph.serialization import (
    deserialize_graph_from_json,
    serialize_graph_to_json,
)

from tests.reverse_engineering.phase_6_3.fixtures import (
    make_composite_fk_schema,
    make_parallel_edges_schema,
    make_self_referencing_schema,
    make_simple_fk_schema,
    make_unresolved_fk_schema,
)

GOLDEN_DIR = Path(__file__).parent / "golden"

GOLDEN_CASES = [
    ("golden_postgresql.json", lambda: make_simple_fk_schema("postgresql")),
    ("golden_sqlite.json", lambda: make_simple_fk_schema("sqlite")),
    ("golden_mysql.json", lambda: make_simple_fk_schema("mysql")),
    ("golden_mariadb.json", lambda: make_simple_fk_schema("mariadb")),
    ("golden_composite_keys.json", lambda: make_composite_fk_schema("postgresql")),
    ("golden_self_referencing.json", lambda: make_self_referencing_schema("postgresql")),
    ("golden_parallel_relationships.json", lambda: make_parallel_edges_schema("postgresql")),
    ("golden_partial_metadata.json", lambda: make_unresolved_fk_schema("postgresql")),
]


@pytest.mark.parametrize("golden_file, schema_fn", GOLDEN_CASES)
def test_golden_graph_deterministic_output(golden_file: str, schema_fn):
    """Verify serialized output matches approved golden file byte-for-byte."""
    schema = schema_fn()
    graph = ForeignKeyGraphBuilder.from_canonical(schema)
    actual_json = serialize_graph_to_json(graph, indent=2) + "\n"

    golden_path = GOLDEN_DIR / golden_file
    assert golden_path.exists(), f"Golden file missing: {golden_path}"

    expected_json = golden_path.read_text(encoding="utf-8")
    # Replace CRLF with LF to handle cross-platform line endings
    assert actual_json.replace("\r\n", "\n") == expected_json.replace("\r\n", "\n")

    # Roundtrip deserialization
    deserialized = deserialize_graph_from_json(expected_json)
    assert deserialized.compute_hash() == graph.compute_hash()
