"""Cycle Detection and Strongly Connected Component (SCC) Analysis.

Uses Tarjan's strongly connected components algorithm to detect circular dependencies
in the migration operation dependency graph.

Strict Non-Negotiable:
- Dependency cycles must NEVER be silently broken.
- Operations involved in cycles are flagged as BLOCKED with clear explanatory reasons.
"""

from typing import Dict, List, Set
from dera.migration.planning.graph import OperationDependencyGraph


class CycleDetector:
    """Tarjan SCC based cycle detection for migration operation graph."""

    def __init__(self, graph: OperationDependencyGraph):
        self.graph = graph

    def find_cycles(self) -> List[List[str]]:
        """Identify all strongly connected components with 2+ operations or self-loops."""
        index = 0
        indices: Dict[str, int] = {}
        lowlinks: Dict[str, int] = {}
        on_stack: Set[str] = set()
        stack: List[str] = []
        sccs: List[List[str]] = []

        def strongconnect(v: str):
            nonlocal index
            indices[v] = index
            lowlinks[v] = index
            index += 1
            stack.append(v)
            on_stack.add(v)

            # Follow forward edges: prerequisite -> dependent
            for w in sorted(self.graph.forward_edges.get(v, [])):
                if w not in indices:
                    strongconnect(w)
                    lowlinks[v] = min(lowlinks[v], lowlinks[w])
                elif w in on_stack:
                    lowlinks[v] = min(lowlinks[v], indices[w])

            if lowlinks[v] == indices[v]:
                scc = []
                while True:
                    w = stack.pop()
                    on_stack.remove(w)
                    scc.append(w)
                    if w == v:
                        break
                # A cycle exists if SCC has > 1 node or a self-dependency loop
                if len(scc) > 1 or (len(scc) == 1 and v in self.graph.forward_edges.get(v, set())):
                    sccs.append(sorted(scc))

        for node in sorted(self.graph.operations.keys()):
            if node not in indices:
                strongconnect(node)

        # Sort SCCs deterministically by first element
        return sorted(sccs, key=lambda comp: comp[0] if comp else "")

    def annotate_blocked_operations(self) -> List[List[str]]:
        """Detect cycles and mark affected operations as blocked."""
        cycles = self.find_cycles()
        for cycle in cycles:
            cycle_desc = " -> ".join(cycle)
            for op_id in cycle:
                op = self.graph.operations.get(op_id)
                if op:
                    op.is_blocked = True
                    op.blocking_reasons.append(
                        f"Circular dependency detected in operations: {cycle_desc}. Requires manual staging or cycle breakdown."
                    )
        return cycles
