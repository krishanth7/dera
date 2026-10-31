# Testing Strategy for Index and Constraint Diagnostics

## 1. Test Suite Architecture
Phase 8.2 test coverage spans unit, integration, cross-engine, determinism, and regression tests:

- `tests/diagnostics/test_index_rules.py`:
  - `DERA-IDX-001`: Duplicate detection, distinct method preservation, partial index distinction.
  - `DERA-IDX-002`: Leftmost prefix detection, unique narrow index protection, non-B-Tree exclusion.
  - `DERA-IDX-003`: PostgreSQL/SQLite unindexed FK detection, partial index handling, MySQL InnoDB exclusion.
  - `DERA-IDX-004`: Index referencing missing column detection.
- `tests/diagnostics/test_constraint_rules.py`:
  - `DERA-CON-001`: Empty PK, duplicate PK columns, missing PK column reference, table without PK preservation.
  - `DERA-CON-002`: Missing child column, column count mismatch, missing parent column, unresolved external table, self-referencing FK.
  - `DERA-CON-003`: Empty UQ, UQ duplicating PK, duplicate UQ declarations.
  - `DERA-CON-004`: Empty check clause, engine applicability.
  - `DERA-CON-005`: Universal constraint column reference integrity.
- `tests/diagnostics/test_index_signatures.py`:
  - Canonical signature hashing, deterministic equivalence, capability checks.
