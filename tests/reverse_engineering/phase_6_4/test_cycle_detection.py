"""Tests for elementary cycle enumeration, canonical rotation, and kind classification."""

from __future__ import annotations

from dera.reverse_engineering.dependencies.algorithms.johnson import find_elementary_cycles
from dera.reverse_engineering.dependencies.models import (
    CycleKind,
    DependencyEdge,
    DependencyKind,
)
from dera.reverse_engineering.dependencies.ordering import canonicalize_cycle_nodes

from tests.reverse_engineering.phase_6_4.fixtures import (
    analyze_database,
    make_complex_scc_schema,
    make_indirect_cycle_schema,
    make_mutual_cycle_schema,
    make_self_referencing_schema,
)


def test_canonicalize_cycle_nodes():
    """Verify cycle rotation puts lowest ObjectId first deterministically."""
    c1 = canonicalize_cycle_nodes(("c", "a", "b"))
    assert c1 == ("a", "b", "c")

    c2 = canonicalize_cycle_nodes(("b", "c", "a"))
    assert c2 == ("a", "b", "c")

    c3 = canonicalize_cycle_nodes(("single",))
    assert c3 == ("single",)

    assert canonicalize_cycle_nodes(()) == ()


def test_self_referencing_cycle_detection():
    """Verify self-referencing cycle is correctly detected and classified."""
    db = make_self_referencing_schema()
    res = analyze_database(db)

    assert res.is_dag is False
    assert res.cycle_report.has_cycles is True
    assert res.cycle_report.cycle_count == 1
    assert res.cycle_report.self_referencing_count == 1
    cycle = res.cycle_report.cycles[0]
    assert cycle.kind == CycleKind.SELF_REFERENCING
    assert len(cycle.node_ids) == 1


def test_mutual_cycle_detection():
    """Verify mutual 2-table cycle is detected and classified."""
    db = make_mutual_cycle_schema()
    res = analyze_database(db)

    assert res.is_dag is False
    assert res.cycle_report.cycle_count == 1
    assert res.cycle_report.mutual_count == 1
    cycle = res.cycle_report.cycles[0]
    assert cycle.kind == CycleKind.MUTUAL
    assert len(cycle.node_ids) == 2


def test_indirect_cycle_detection():
    """Verify 3-table circular dependency is detected and classified."""
    db = make_indirect_cycle_schema()
    res = analyze_database(db)

    assert res.is_dag is False
    assert res.cycle_report.cycle_count == 1
    assert res.cycle_report.indirect_count == 1
    cycle = res.cycle_report.cycles[0]
    assert cycle.kind == CycleKind.INDIRECT
    assert len(cycle.node_ids) == 3


def test_complex_scc_cycle_classification():
    """Verify multiple overlapping cycles in an SCC are classified as COMPLEX."""
    db = make_complex_scc_schema()
    res = analyze_database(db)

    assert res.is_dag is False
    assert res.cycle_report.complex_count >= 1
    assert res.cycle_report.has_cycles is True


def test_cycle_enumeration_circuit_breaker():
    """Verify max_cycles terminates cycle enumeration cleanly on dense cyclic graphs."""
    # Complete 4-node clique K4 (dense cycles)
    nodes = ["n1", "n2", "n3", "n4"]
    adj = {u: [v for v in nodes if v != u] for u in nodes}
    edges_by_pair = {
        (u, v): [
            DependencyEdge(
                edge_id=f"e_{u}_{v}",
                dependent_id=u,
                referenced_id=v,
                kind=DependencyKind.TABLE_FOREIGN_KEY,
            )
        ]
        for u in nodes
        for v in nodes
        if u != v
    }

    cycles, truncated = find_elementary_cycles(
        scc_nodes=nodes,
        adjacency=adj,
        edges_by_pair=edges_by_pair,
        max_cycles=2,
    )
    assert truncated is True
    assert len(cycles) == 2
