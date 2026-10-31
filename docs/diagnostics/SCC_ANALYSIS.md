# DERA Phase 8.3 — Strongly Connected Component (SCC) Analysis

## 1. Overview
In Phase 6.4, DERA implemented Tarjan's strongly connected components algorithm to partition the relational multigraph into equivalence classes of mutually reachable tables. In Phase 8.3, the diagnostic engine bridges SCC topology directly to operational risk and migration sequencing diagnostics.

## 2. Condensation DAG Transformation
To evaluate dependency depth, breadth, and topological levels on graphs that contain cycles without infinite recursion:
1. Every multi-table cyclic SCC is contracted into a single "supernode" ($C_i$).
2. A directed acyclic graph (Condensation DAG) is constructed:
   $$\mathcal{G}_{\text{condensed}} = (\mathcal{V}_{\text{SCC}}, \mathcal{E}_{\text{condensed}})$$
   where an edge $(C_u \to C_v)$ exists if and only if there is a directed foreign key from some table in $C_u$ to some table in $C_v$.
3. The Condensation DAG is strictly acyclic, guaranteeing finite, bounded topological depth and level stratification.

## 3. Elementary Cycle Enumeration
Within each cyclic SCC, elementary cycles are boundedly enumerated using Johnson's cycle-finding algorithm:
- Detects the minimal distinct directed cycles within the component.
- Records member paths and constraint identities.
- Distinguishes breakable cycles (those with at least one nullable or deferrable foreign key) from unbreakable cycles.
