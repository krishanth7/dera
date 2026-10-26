# DERA Testing Architecture & Quality Verification Guide

> **Project:** DERA — Database Engineering & Reverse Analysis  
> **Maintainer:** Krishanth  
> **Status:** Authoritative Testing Reference  
> **Last Verified:** 2026-10-26 (Commit `e550fdd`)  

---

## 1. Testing Philosophy & Test Pyramid

DERA enforces a deterministic, multi-tiered testing strategy designed to verify domain logic, mathematical invariants, database connector safety, and architectural boundaries.

Because DERA operates under a strict **Zero-AI mandate**, all test suites are completely deterministic and offline-capable:
- **Zero External Network Dependencies:** All 47 automated tests run fully offline without requiring cloud accounts, external databases, or inference APIs.
- **Fast Execution:** The entire 47-test suite executes in approximately **0.5 to 0.8 seconds** on standard developer hardware.
- **Hermetic Isolation:** Database tests execute against SQLite `:memory:` connections or temporary in-process test fixtures that leave zero persistent state.

```
                  ┌───────────────────────────────┐
                  │    Architecture & Boundary    │  (tests/architecture/)
                  │     Zero-AI, Core Isolation   │  1 Test File, 5 Test Cases
                  ├───────────────────────────────┤
                  │     Integration Test Tier     │  (tests/integration/)
                  │  Real SQLite Catalog Parsing  │  1 Test File, 6 Test Cases
                  ├───────────────────────────────┤
                  │    Regression Invariants      │  (tests/regression/)
                  │   SHA-256 Hash Stability      │  1 Test File, 5 Test Cases
                  ├───────────────────────────────┤
                  │   Documentation & i18n Tier   │  (tests/docs/)
                  │   10-Language Navigation      │  1 Test File, 15 Test Cases
                  ├───────────────────────────────┤
                  │       Unit Test Tier          │  (tests/unit/)
                  │  Models, Kahn DAG, Rules, API │  4 Test Files, 16 Test Cases
                  └───────────────────────────────┘
```

---

## 2. Test Suite Organization & Inventory

| Directory | Suite Category | Test File | Test Count | Key Invariants Verified |
|---|---|---|---|---|
| `tests/unit/` | Unit | `test_models.py` | 5 | Immutable dataclass construction, column positions, SHA-256 computation. |
| `tests/unit/` | Unit | `test_api.py` | 2 | FastAPI `/health` and `/info` endpoints (skipped gracefully if fastapi is absent). |
| `tests/unit/` | Unit | `test_validate_pr_title.py` | 6 | Conventional Commits parsing and validation. |
| `tests/unit/` | Unit | `test_validate_pr_readiness.py` | 3 | PR branch, description, and checklist validation. |
| `tests/integration/` | Integration | `test_sqlite_connector.py` | 6 | SQLite `BaseConnector` lifecycle, `PRAGMA query_only = ON;`, composite keys. |
| `tests/regression/` | Regression | `test_schema_regression.py` | 5 | Deterministic schema snapshot SHA-256 fingerprint reproducibility. |
| `tests/architecture/` | Architecture | `test_module_boundaries.py` | 5 | Zero-AI import scanning, core framework independence, SQL mutation rejection. |
| `tests/docs/` | Documentation | `test_language_navigation.py` | 15 | Canonical 10-language navigation banner synchronization across all README files. |
| **Total** | — | **8 Test Files** | **47 Tests** | **Full offline verification in < 1 second** |

---

## 3. How to Execute Test Suites

### 3.1 Running the Full Suite
```bash
# Using the cross-platform runner
python scripts/development/dev.py test

# Using standard Python unittest discovery
python -m unittest discover tests/
```

### 3.2 Running Specific Test Suites
```bash
# Run unit tests only
python -m unittest discover tests/unit

# Run architecture boundary and Zero-AI enforcement tests
python -m unittest tests/architecture/test_module_boundaries.py

# Run SQLite connector integration tests
python -m unittest tests/integration/test_sqlite_connector.py

# Run SHA-256 schema hash regression tests
python -m unittest discover tests/regression

# Run 10-language documentation navigation tests
python -m unittest discover tests/docs
```

---

## 4. Test Fixtures & In-Memory Isolation

### 4.1 SQLite Ephemeral Fixtures
In [`tests/integration/test_sqlite_connector.py`](../../tests/integration/test_sqlite_connector.py), test tables (`users`, `orders`, `order_items`) are dynamically generated in SQLite in-memory databases (`:memory:`):
- Foreign-key relationships are established with explicit `ON DELETE CASCADE` actions.
- Indexes are constructed and verified against `TableIndex` domain models.
- Connections are automatically disposed of during `tearDown()`.

### 4.2 AST Module Boundary Scanning
In [`tests/architecture/test_module_boundaries.py`](../../tests/architecture/test_module_boundaries.py), Python's `ast.parse` walks every `.py` file across `packages/` and `apps/` to ensure no prohibited imports (`openai`, `google.genai`, `torch`, `fastapi` inside `packages/core`) exist.

---

## 5. How to Add New Tests

### 5.1 Adding a New Unit Test
1. Create or open the relevant file in `tests/unit/test_<component>.py`.
2. Inherit from `unittest.TestCase`.
3. Name test methods starting with `test_`.
4. Use standard assertions (`self.assertEqual`, `self.assertTrue`, `self.assertRaises`).

```python
import unittest
from dera.models import DatabaseColumn

class TestColumn(unittest.TestCase):
    def test_column_immutability(self):
        col = DatabaseColumn(name="email", data_type="VARCHAR(255)")
        with self.assertRaises(AttributeError):
            col.name = "new_email"  # Frozen dataclass prevents mutation
```

### 5.2 Adding a New Connector Integration Test
1. Create `tests/integration/test_<dialect>_connector.py`.
2. Subclass `unittest.TestCase`.
3. In `setUp()`, initialize the connector with a `ConnectionConfig`.
4. Ensure target databases run against ephemeral mocks or test containers. Never run integration tests against production databases!

---

## 6. Interpreting Test Failures & Troubleshooting

| Common Failure Message | Root Cause | Resolution |
|---|---|---|
| `AssertionError: ... Forbidden AI import {'openai'} in ...` | Code in `packages/` or `apps/` imported a forbidden AI library. | Remove the AI dependency. DERA must remain 100% deterministic and non-AI. |
| `AssertionError: ... Core module imports web framework ...` | `packages/core` imported `fastapi` or `starlette`. | Decouple domain logic from the transport layer. Core must depend only on Python stdlib. |
| `ReadOnlyViolationError: Query rejected by read-only connector boundary` | An introspection query contained a forbidden keyword (`DROP`, `ALTER`, etc.). | Ensure introspection queries only read from catalog tables (`SELECT`, `PRAGMA`). |
| `AssertionError: Hash mismatch in SchemaSnapshot` | A change altered the serialization format of canonical schema models. | Verify whether the model change was intentional and update regression snapshots accordingly. |

---

## 7. Related Documentation

- [Getting Started Guide](GETTING_STARTED.md)
- [Development Commands](COMMANDS.md)
- [Troubleshooting Guide](TROUBLESHOOTING.md)
- [Module Boundaries Specification](../architecture/MODULE_BOUNDARIES.md)
