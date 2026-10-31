# DERA Diagnostics — Testing Strategy & Verification

**Milestone:** Phase 8.1 — Deterministic Schema Diagnostic Rules Engine  
**Test Suite Directory:** `tests/diagnostics/`  
**Status:** Canonical Reference  

---

## 1. Test Suite Architecture

The diagnostic engine is validated by an extensive test matrix in `tests/diagnostics/`:

| Test Module | Coverage Scope |
| :--- | :--- |
| `test_models.py` | Model immutability, validation constraints, evidence sanitization, canonical dictionary serialization. |
| `test_registry.py` | Rule registration, duplicate ID rejection, invalid metadata detection, deterministic alphabetical listing, criteria filtering. |
| `test_context.py` | Context creation, resource limits validation, configuration hashing. |
| `test_applicability.py` | Engine dialect matching, capability state evaluation, metadata completeness checks. |
| `test_fingerprint.py` | Finding fingerprint invariance, configuration fingerprint stability, serialization round-trip preservation. |
| `test_evaluator.py` | Execution orchestration, deterministic sorting, error isolation, resource limits enforcement. |
| `test_foundational_rules.py` | Comprehensive positive, negative, and edge-case evaluations for `DERA-SCHEMA-001` through `005`. |
| `test_determinism.py` | Permutation invariance (shuffled tables and rules produce identical report hashes). |
| `test_cross_engine.py` | Multi-engine fixtures: PostgreSQL, Supabase PostgreSQL, SQLite, MySQL, MariaDB. |
| `test_snapshots.py` | Direct evaluation of Phase 6.5 immutable `SchemaSnapshot` payloads. |
| `test_security.py` | Credential stripping, resource ceiling rejection, denial-of-service defense. |
| `test_api.py` | FastAPI endpoint contracts: rule listing, rule lookup, schema evaluation. |

---

## 2. Execution Command

```bash
python -m pytest tests/diagnostics/ -v
```
