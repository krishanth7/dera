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
    """Verify that reversing/shuffling the declaration order of tables produces identical SHA-256 hash."""
    db1 = make_ecommerce_schema()
    schema1 = SchemaBuilder.from_canonical_database(db1)
    graph1 = ForeignKeyGraphBuilder.from_schema(schema1)

    analyzer = DependencyAnalyzer()
    res1 = analyzer.analyze(graph1, schema=schema1)
    hash1 = compute_dependency_hash(res1)

    # Build second database with reversed table order and reversed foreign keys
    orig_ns = db1.namespaces[0]
    shuffled_tables = tuple(
        t.model_copy(update={"foreign_keys": tuple(reversed(t.foreign_keys))})
        for t in reversed(orig_ns.tables)
    )
    shuffled_ns = orig_ns.model_copy(update={"tables": shuffled_tables})
    db2 = db1.model_copy(update={"namespaces": (shuffled_ns,)})

    schema2 = SchemaBuilder.from_canonical_database(db2)
    graph2 = ForeignKeyGraphBuilder.from_schema(schema2)
    res2 = analyzer.analyze(graph2, schema=schema2)
    hash2 = compute_dependency_hash(res2)

    assert hash1 == hash2
    assert res1.ordering.creation_order == res2.ordering.creation_order
    assert res1.ordering.drop_order == res2.ordering.drop_order
    assert res1.ordering.levels == res2.ordering.levels


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
