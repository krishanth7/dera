# Graph Testing & Quality Assurance

## 1. Test Suite Architecture

The Phase 6.3 test suite is located in `tests/reverse_engineering/phase_6_3/` and comprises 14 dedicated test modules plus 8 golden verification files:

```text
tests/reverse_engineering/phase_6_3/
├── fixtures.py                     # Deterministic multi-engine schema fixture factories
├── test_graph_models.py            # Root ForeignKeyGraph contract and immutability
├── test_nodes.py                   # TableNode creation, validation, and metadata
├── test_edges.py                   # ForeignKeyEdge, directionality, and actions
├── test_composite_keys.py          # Multi-column keys and ordinal sequence ordering
├── test_adjacency.py               # O(1) adjacency indexes and neighbor queries
├── test_traversal.py               # BFS, DFS, depth bounding, and limits
├── test_self_references.py         # Self-loops and hierarchy handling
├── test_cross_namespace.py         # Multi-schema relationships (e.g. auth -> public)
├── test_validation.py              # Multi-severity validation rules and findings
├── test_determinism.py             # Input ordering independence & stable sorting
├── test_serialization.py          # RFC 8785 Canonical JSON roundtripping & SHA-256
├── test_cross_engine.py            # PostgreSQL, SQLite, MySQL, MariaDB semantics
├── test_security.py                # Resource limits, workspace isolation, large payloads
├── test_integration.py             # Pipeline integration from Phase 6.1 through 6.3
├── test_golden_graphs.py           # 8 golden schema JSON match validations
└── golden/                         # Reviewed golden JSON baseline files
    ├── golden_postgresql.json
    ├── golden_sqlite.json
    ├── golden_mysql.json
    ├── golden_mariadb.json
    ├── golden_composite_keys.json
    ├── golden_self_referencing.json
    ├── golden_parallel_relationships.json
    └── golden_partial_metadata.json
```

---

## 2. Verification Categories

### 2.1. Determinism Tests
Verifies that permuting input collections (e.g., shuffling table or constraint lists) produces bit-for-bit identical graphs and identical SHA-256 hashes.

### 2.2. Golden File Tests
Compares serialized graphs against 8 reviewed reference JSON documents in `golden/` to prevent silent drift in schema serialization.

### 2.3. Security & Limit Tests
Tests defensive bounds against oversized node counts, excessive edge definitions, deep recursion in traversals, and multi-tenant workspace leakage.

### 2.4. Cross-Engine Tests
Validates that engine-specific characteristics (PostgreSQL schemas, SQLite pragmas, MySQL non-deferrability) are preserved accurately without synthetic alteration.

---

## 3. Test Execution

Run the complete Phase 6.3 test suite:
```bash
pytest tests/reverse_engineering/phase_6_3/ -v
```

Run full regression verification across all DERA subsystems:
```bash
pytest tests/ -v
```
