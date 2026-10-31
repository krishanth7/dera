# DERA Phase 8.3 — Relationship & Dependency Testing Strategy

## 1. Test Architecture
The test suite for Phase 8.3 comprises unit, integration, determinism, and performance tests organized under `tests/diagnostics/`:

- `test_relationship_rules.py`: Validates all 4 relationship rules (`DERA-REL-001` through `DERA-REL-004`) across valid, corrupted, composite, and cross-namespace scenarios.
- `test_dependency_rules.py`: Validates all 4 dependency rules (`DERA-DEP-001` through `DERA-DEP-004`) covering acyclic DAGs, self-loops, 2-node cycles, multi-node cycles, depth thresholds, fan-in hubs, fan-out consumers, and structural impact radius.
- `test_graph_helpers.py`: Verifies reverse reachability traversal, bounded BFS depth, node mapping, and parallel edge grouping.
- `test_relationship_determinism.py`: Runs multi-trial randomized input graph permutations (shuffling nodes, edges, and unresolved references) verifying bitwise identical findings and deterministic fingerprints.

## 2. Benchmark & Performance Invariants
- Graph integrity and composite FK validation run in $\mathcal{O}(|V| + |E|)$ time.
- Tarjan SCC and Johnson cycle evaluation run in precomputed Phase 6.4 analysis.
- Reverse reachability traversal executes within $< 5\text{ms}$ on 500-table topologies.
- 100% of tests execute with zero network calls and zero database mutations.
