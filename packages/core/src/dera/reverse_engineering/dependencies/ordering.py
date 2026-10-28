"""DERA Reverse Engineering — Phase 6.4 Deterministic Ordering.

Provides canonical, deterministic sorting and canonicalization helpers for dependency edges,
cycles, SCCs, topological levels, and validation findings.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence

from dera.metadata.identity import ObjectId
from dera.reverse_engineering.dependencies.models import (
    CondensationNode,
    CycleInstance,
    DependencyEdge,
    DependencyValidationFinding,
    StronglyConnectedComponent,
    TopologicalLevel,
)


def canonicalize_cycle_nodes(nodes: Sequence[ObjectId]) -> tuple[ObjectId, ...]:
    """Rotate a cycle sequence so that the node with the minimum ObjectId value is first.

    Ensures that (A, B, C), (B, C, A), and (C, A, B) produce an identical canonical representation.
    """
    if not nodes:
        return ()
    if len(nodes) == 1:
        return tuple(nodes)

    min_idx = 0
    min_val = str(nodes[0])
    for i in range(1, len(nodes)):
        curr_val = str(nodes[i])
        if curr_val < min_val:
            min_val = curr_val
            min_idx = i

    return tuple(nodes[min_idx:]) + tuple(nodes[:min_idx])


def sort_dependency_edges(edges: Iterable[DependencyEdge]) -> tuple[DependencyEdge, ...]:
    """Sort dependency edges deterministically by dependent_id, referenced_id, and edge_id."""
    return tuple(
        sorted(
            edges,
            key=lambda e: (
                str(e.dependent_id),
                str(e.referenced_id),
                e.edge_id,
            ),
        )
    )


def sort_cycle_instances(cycles: Iterable[CycleInstance]) -> tuple[CycleInstance, ...]:
    """Sort cycle instances deterministically."""
    return tuple(
        sorted(
            cycles,
            key=lambda c: (
                c.kind.value,
                len(c.node_ids),
                tuple(str(n) for n in c.node_ids),
                c.cycle_id,
            ),
        )
    )


def sort_sccs(sccs: Iterable[StronglyConnectedComponent]) -> tuple[StronglyConnectedComponent, ...]:
    """Sort strongly connected components deterministically: cyclic first, then by size, then members."""
    return tuple(
        sorted(
            sccs,
            key=lambda s: (
                not s.is_cyclic,  # Cyclic components first
                -len(s.node_ids),  # Larger components first
                tuple(str(n) for n in s.node_ids),
                s.scc_id,
            ),
        )
    )


def sort_topological_levels(levels: Iterable[TopologicalLevel]) -> tuple[TopologicalLevel, ...]:
    """Sort topological levels by layer index."""
    return tuple(sorted(levels, key=lambda lvl: lvl.level))


def sort_condensation_nodes(nodes: Iterable[CondensationNode]) -> tuple[CondensationNode, ...]:
    """Sort condensation nodes deterministically."""
    return tuple(
        sorted(
            nodes,
            key=lambda c: (
                not c.is_cyclic,
                -len(c.member_node_ids),
                tuple(str(n) for n in c.member_node_ids),
                c.condensation_id,
            ),
        )
    )


def sort_dependency_validation_findings(
    findings: Iterable[DependencyValidationFinding],
) -> tuple[DependencyValidationFinding, ...]:
    """Sort validation findings by severity rank, rule ID, and message."""
    severity_rank = {"ERROR": 0, "WARNING": 1, "INFO": 2}
    return tuple(
        sorted(
            findings,
            key=lambda f: (
                severity_rank.get(f.severity, 99),
                f.rule_id,
                f.message,
                tuple(sorted(f.context.items())),
            ),
        )
    )
