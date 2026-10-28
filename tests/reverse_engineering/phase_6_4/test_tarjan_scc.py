"""Tests for deterministic Tarjan's Strongly Connected Components algorithm."""

from __future__ import annotations

from dera.reverse_engineering.dependencies.algorithms.tarjan import (
    compute_strongly_connected_components,
)


def test_tarjan_pure_dag():
    """Verify Tarjan partitions pure DAG into single-node non-cyclic components."""
    nodes = ["t0", "t1", "t2", "t3"]
    # t1 depends on t0, t2 depends on t1, t3 depends on t2
    adj = {
        "t3": ["t2"],
        "t2": ["t1"],
        "t1": ["t0"],
        "t0": [],
    }
    sccs = compute_strongly_connected_components(nodes, adj)
    assert len(sccs) == 4
    for scc in sccs:
        assert scc.is_cyclic is False
        assert len(scc.node_ids) == 1


def test_tarjan_self_loop():
    """Verify single-node with self-loop is detected as a cyclic SCC."""
    nodes = ["emp", "dept"]
    adj = {
        "emp": ["emp", "dept"],
        "dept": [],
    }
    sccs = compute_strongly_connected_components(nodes, adj, self_loops={"emp"})
    assert len(sccs) == 2
    cyclic_sccs = [s for s in sccs if s.is_cyclic]
    assert len(cyclic_sccs) == 1
    assert cyclic_sccs[0].node_ids == ("emp",)


def test_tarjan_mutual_cycle():
    """Verify 2 mutually dependent tables form a single cyclic SCC."""
    nodes = ["author", "book", "publisher"]
    # author <-> book, publisher is independent
    adj = {
        "author": ["book"],
        "book": ["author", "publisher"],
        "publisher": [],
    }
    sccs = compute_strongly_connected_components(nodes, adj)
    assert len(sccs) == 2
    cyclic = [s for s in sccs if s.is_cyclic]
    assert len(cyclic) == 1
    assert set(cyclic[0].node_ids) == {"author", "book"}


def test_tarjan_indirect_cycle():
    """Verify 3-table circular dependency forms a single cyclic SCC."""
    nodes = ["tA", "tB", "tC", "tRoot"]
    # tA -> tB -> tC -> tA, all depend on tRoot
    adj = {
        "tA": ["tB", "tRoot"],
        "tB": ["tC"],
        "tC": ["tA"],
        "tRoot": [],
    }
    sccs = compute_strongly_connected_components(nodes, adj)
    assert len(sccs) == 2
    cyclic = [s for s in sccs if s.is_cyclic]
    assert len(cyclic) == 1
    assert set(cyclic[0].node_ids) == {"tA", "tB", "tC"}


def test_tarjan_complex_intertwined_sccs():
    """Verify complex graph with multiple intertwined cycles."""
    nodes = ["a", "b", "c", "d", "e"]
    # a -> b -> c -> a
    # b -> d -> b
    # e is leaf depending on c
    adj = {
        "a": ["b"],
        "b": ["c", "d"],
        "c": ["a"],
        "d": ["b"],
        "e": ["c"],
    }
    sccs = compute_strongly_connected_components(nodes, adj)
    assert len(sccs) == 2
    cyclic = [s for s in sccs if s.is_cyclic]
    assert len(cyclic) == 1
    assert set(cyclic[0].node_ids) == {"a", "b", "c", "d"}
    acyclic = [s for s in sccs if not s.is_cyclic]
    assert len(acyclic) == 1
    assert acyclic[0].node_ids == ("e",)
