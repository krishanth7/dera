# Testing Strategy & Automated Test Suite (Phase 6.1)

## 1. Overview

The Phase 6.1 test suite contains 49 comprehensive tests in `tests/reverse_engineering/phase_6_1/` covering 10 distinct verification dimensions with 100% pass rate.

---

## 2. Test Suite Structure

| Test Module | Coverage Dimension | Test Count |
|---|---|---|
| `test_schema_builder.py` | Schema construction pipeline, contract checks, resource bounds | 8 |
| `test_object_registry.py` | O(1) registration, duplicate detection, kind-verified lookup | 7 |
| `test_references.py` | `TypedRef` and `ForeignKeyReference` status transitions | 4 |
| `test_hierarchy.py` | Hierarchical tree traversal (DB → NS → Table → Columns/Constraints) | 4 |
| `test_validation.py` | Referential integrity and structural consistency validation | 3 |
| `test_determinism.py` | Input-order invariance, shuffled collection determinism, SHA-256 hash | 4 |
| `test_serialization.py` | Canonical JSON serialization, hashing, and safe round-trip reconstruction | 7 |
| `test_cross_engine.py` | Compatibility across PostgreSQL, Supabase, SQLite, MySQL, MariaDB | 5 |
| `test_security.py` | Workspace isolation, credential sanitization, DoS limits, injection handling | 5 |
| `test_integration.py` | Real disposable SQLite DB → SqliteConnector → Normalizer → SchemaBuilder | 1 |
| `test_golden.py` | Golden schema representation stability and reviewed contract assertions | 1 |
| **Total** | | **49 Tests** |

---

## 3. Running Tests

### Run Phase 6.1 Suite
```bash
python -m unittest discover -s tests/reverse_engineering/phase_6_1 -p "test_*.py"
```

### Run Full Repository Regression Suite
```bash
python -m unittest discover -s tests -p "test_*.py"
```
Results: **587 tests passed in 103s with 0 regressions**.
