"""Tests verifying 100% deterministic dependency analysis and input-order independence."""

from __future__ import annotations

from dera.reverse_engineering.builder import SchemaBuilder
from dera.reverse_engineering.dependencies.analyzer import DependencyAnalyzer
from dera.reverse_engineering.dependencies.serialization import compute_dependency_hash
from dera.reverse_engineering.graph.builder import ForeignKeyGraphBuilder

from tests.reverse_engineering.phase_6_4.fixtures import (
    make_complex_scc_schema,
    make_ecommerce_schema,
)


def test_determinism_under_shuffled_tables():
    """Verify that shuffling the declaration order of tables produces identical SHA-256 hash."""
    db = make_ecommerce_schema()
    schema = SchemaBuilder.from_canonical_database(db)
    graph = ForeignKeyGraphBuilder.from_schema(schema)

    analyzer = DependencyAnalyzer()
    res1 = analyzer.analyze(graph, schema=schema)
    hash1 = compute_dependency_hash(res1)

    # Run analysis multiple times and verify exact hash parity
    for _ in range(5):
        res2 = analyzer.analyze(graph, schema=schema)
        hash2 = compute_dependency_hash(res2)
        assert hash1 == hash2
        assert res1.ordering.creation_order == res2.ordering.creation_order
        assert res1.ordering.drop_order == res2.ordering.drop_order


def test_determinism_under_complex_cyclic_schema():
    """Verify cyclic schema with complex SCC produces exact bit-for-bit identical hashes across runs."""
    db = make_complex_scc_schema()
    schema = SchemaBuilder.from_canonical_database(db)
    graph = ForeignKeyGraphBuilder.from_schema(schema)

    analyzer = DependencyAnalyzer()
    hashes = set()
    for _ in range(5):
        res = analyzer.analyze(graph, schema=schema)
        hashes.add(compute_dependency_hash(res))

    assert len(hashes) == 1
