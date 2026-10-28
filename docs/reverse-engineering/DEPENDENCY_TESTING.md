# Phase 6.4 Dependency Analysis Test Strategy & Verification

## 1. Test Suite Architecture

The Phase 6.4 test suite (`tests/reverse_engineering/phase_6_4/`) covers unit, integration, determinism, golden file, cross-engine, security, and edge-case scenarios:

| Test Module | Tests | Description |
| :--- | :--- | :--- |
| `test_cycle_detection.py` | 6 | Self-referencing, mutual, indirect, complex, and acyclic cycle tests. |
| `test_cycle_breakability.py` | 5 | Nullable FK, deferrable constraint, post-load, and unbreakable cycle remediation. |
| `test_topological_sort.py` | 6 | Kahn's algorithm ordering, parent precedence, and multi-branch determinism. |
| `test_condensation_dag.py` | 5 | Supernode condensation, inter-SCC edge preservation, and condensation topological sort. |
| `test_parallel_levels.py` | 5 | Generation stratification, root assignment, and parallel level invariants. |
| `test_dependency_metrics.py` | 5 | In/out degree, depth, transitive ancestors/descendants, root/leaf/isolated checks. |
| `test_validation.py` | 6 | Strict/non-strict validation, error detection on unbreakable cycles, warnings. |
| `test_determinism.py` | 4 | Bit-for-bit repeatability, node shuffle resistance, and stable fingerprinting. |
| `test_serialization.py` | 5 | RFC 8785 JSON canonicalization, deserialization, and roundtrip fidelity. |
| `test_security.py` | 5 | Resource limits enforcement (`max_nodes`, `max_edges`, `max_cycles`, max bytes). |
| `test_cross_engine.py` | 4 | Multi-engine schema verification (PostgreSQL, SQLite, MySQL). |
| `test_integration.py` | 3 | End-to-end integration: `CanonicalDatabase -> SchemaRepresentation -> ForeignKeyGraph -> DependencyAnalysisResult`. |
| `test_golden_dependencies.py` | 2 | Golden JSON snapshot verification across 8 topologies. |

**Total Phase 6.4 Tests**: 61 / 61 passed (100% pass rate).

---

## 2. Golden File Topologies

Eight golden reference snapshots are validated under `tests/reverse_engineering/phase_6_4/golden/`:
1. `golden_linear_dag.json` (Linear parent $\to$ child dependency)
2. `golden_diamond_dag.json` (Diamond dependency with multiple convergent paths)
3. `golden_self_referencing.json` (Self-referencing table cycle)
4. `golden_mutual_cycle.json` (Bidirectional 2-table mutual cycle)
5. `golden_indirect_cycle.json` (3-table cyclic dependency)
6. `golden_complex_scc.json` (Multi-cycle complex SCC)
7. `golden_ecommerce.json` (Realistic multi-table e-commerce relational schema)
8. `golden_cross_engine_sqlite.json` (SQLite engine schema representation)
