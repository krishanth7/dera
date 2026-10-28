"""DERA Reverse Engineering — Cycle Analysis & Aggregation.

Classifies cycles across strongly connected components, updates complex multi-cycle
components, and constructs comprehensive diagnostic CycleReports.
"""

from __future__ import annotations

from collections.abc import Sequence

from dera.reverse_engineering.dependencies.models import (
    CycleInstance,
    CycleKind,
    CycleReport,
    StronglyConnectedComponent,
)
from dera.reverse_engineering.dependencies.ordering import sort_cycle_instances, sort_sccs


def compile_cycle_report(
    sccs: Sequence[StronglyConnectedComponent],
) -> tuple[CycleReport, tuple[StronglyConnectedComponent, ...]]:
    """Aggregate discovered cycles across all SCCs and construct an auditable CycleReport.

    Also refines cycle kinds to COMPLEX when an SCC contains multiple overlapping cycles.

    Returns:
        Tuple of (CycleReport, updated tuple of StronglyConnectedComponents).
    """
    updated_sccs: list[StronglyConnectedComponent] = []
    all_cycles: list[CycleInstance] = []

    self_ref_count = 0
    mutual_count = 0
    indirect_count = 0
    complex_count = 0
    breakable_count = 0
    unbreakable_count = 0
    cyclic_scc_count = 0

    for scc in sccs:
        if not scc.is_cyclic:
            updated_sccs.append(scc)
            continue

        cyclic_scc_count += 1
        scc_cycles = list(scc.cycles)

        # If SCC has more than 1 cycle, or if members > 2 and cycles >= 2, classify as COMPLEX
        is_complex = len(scc_cycles) > 1 or (len(scc.node_ids) > 2 and len(scc_cycles) >= 2)

        refined_cycles: list[CycleInstance] = []
        for c in scc_cycles:
            if is_complex and c.kind not in (CycleKind.SELF_REFERENCING,):
                # Upgrade to COMPLEX
                c = CycleInstance(
                    cycle_id=c.cycle_id.replace("mutual", "complex").replace("indirect", "complex"),
                    kind=CycleKind.COMPLEX,
                    node_ids=c.node_ids,
                    edge_ids=c.edge_ids,
                    break_edges=c.break_edges,
                    is_breakable=c.is_breakable,
                    recommended_break_strategy=c.recommended_break_strategy,
                )

            refined_cycles.append(c)
            all_cycles.append(c)

            if c.kind == CycleKind.SELF_REFERENCING:
                self_ref_count += 1
            elif c.kind == CycleKind.MUTUAL:
                mutual_count += 1
            elif c.kind == CycleKind.INDIRECT:
                indirect_count += 1
            elif c.kind == CycleKind.COMPLEX:
                complex_count += 1

            if c.is_breakable:
                breakable_count += 1
            else:
                unbreakable_count += 1

        updated_sccs.append(
            StronglyConnectedComponent(
                scc_id=scc.scc_id,
                node_ids=scc.node_ids,
                is_cyclic=scc.is_cyclic,
                cycles=sort_cycle_instances(refined_cycles),
            )
        )

    sorted_cycles = sort_cycle_instances(all_cycles)
    sorted_sccs_result = sort_sccs(updated_sccs)

    report = CycleReport(
        has_cycles=len(sorted_cycles) > 0,
        cycle_count=len(sorted_cycles),
        scc_count=len(sorted_sccs_result),
        cyclic_scc_count=cyclic_scc_count,
        self_referencing_count=self_ref_count,
        mutual_count=mutual_count,
        indirect_count=indirect_count,
        complex_count=complex_count,
        breakable_cycle_count=breakable_count,
        unbreakable_cycle_count=unbreakable_count,
        cycles=sorted_cycles,
        sccs=sorted_sccs_result,
    )

    return report, sorted_sccs_result
