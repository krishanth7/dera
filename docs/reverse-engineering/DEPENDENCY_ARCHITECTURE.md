# Phase 6.4 Dependency Architecture & Pipeline Flow

## 1. Subsystem Architecture

The Dependency Analysis Subsystem coordinates multiple deterministic graph algorithms into a coherent analysis pipeline:

```text
┌────────────────────────────────────────────────────────┐
│ Input: SchemaRepresentation + ForeignKeyGraph          │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│ Step 1: Ingest & Build Dependency Adjacency            │
│  - Invert FK direction: Table A (FK) -> Table B (PK)   │
│  - Verify resource limits (node count, edge count)     │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│ Step 2: Tarjan SCC Algorithm (Strongly Connected)      │
│  - Compute maximal subgraphs where every vertex is     │
│    reachable from every other vertex                   │
│  - Stable iteration order by ObjectId string           │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│ Step 3: Johnson Bounded Elementary Cycle Enumeration   │
│  - Enumerate distinct elementary cycles                │
│  - Bounded by limits.max_cycles                        │
│  - Canonicalize cycle representations (min element)    │
│  - Classify CycleKind and BreakabilityStrategy         │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│ Step 4: Topological Ordering & Stratification          │
│  - If DAG (zero cycles): Kahn's Priority Queue Sort    │
│    - Compute parallel migration levels                 │
│    - Linear creation order (Parents -> Children)       │
│    - Linear drop order (Children -> Parents)           │
│  - If Cyclic: Condensation Supernode DAG               │
│    - Collapse SCCs into supernodes                     │
│    - Deterministic supernode topological order         │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│ Step 5: Dependency Metrics Computation                 │
│  - In-degree, out-degree, max depth                    │
│  - Transitive ancestor / descendant reachability       │
│  - Identify Root tables, Leaf tables, Isolated tables  │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│ Step 6: Multi-Severity Validation Engine               │
│  - Verify ordering completeness and level validity     │
│  - Flag unbreakable cycles as ERRORS                   │
│  - Flag breakable cycles as WARNINGS                   │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│ Step 7: RFC 8785 Serialization & Fingerprint           │
│  - Deterministic canonical JSON representation         │
│  - SHA-256 fingerprint digest                          │
└────────────────────────────────────────────────────────┘
```

---

## 2. Dependency Directionality Contract

In relational databases:
- Table $A$ declares a foreign key referencing Table $B$.
- Table $B$ must exist before Table $A$ can be populated or created with active constraints.
- Therefore, $A$ **depends on** $B$.

In the `DependencyAnalysisResult`:
- `dependent_node_id`: Table $A$ (Child table declaring the FK).
- `dependency_node_id`: Table $B$ (Parent table referenced by the FK).
- **Creation Order**: $B$ precedes $A$.
- **Drop Order**: $A$ precedes $B$.
