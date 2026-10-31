# Index & Constraint Diagnostic Performance Benchmarks

## 1. Algorithmic Complexity Bounds
- **Exact Duplicate Detection (`DERA-IDX-001`)**:
  - $O(T \times I^2)$ worst-case per table where $I$ is index count on that table, but with $I$ typically $< 20$, average execution is sub-millisecond per table.
  - Hashing via `signature_hash()` allows constant-time hash comparisons.
- **Redundant Prefix Analysis (`DERA-IDX-002`)**:
  - Bounded to pairwise comparisons between B-Tree indexes on the same table.
- **Foreign Key Coverage (`DERA-IDX-003`)**:
  - $O(F \times I)$ comparisons per table, bounded by foreign key and index counts.

## 2. Resource Limits & Circuit Breakers
Diagnosed via `DiagnosticResourceLimits`:
- `max_objects`: 100,000 objects maximum per run.
- `max_findings`: 10,000 findings maximum per run.
- `timeout_seconds`: 60.0s total execution timeout.
Exceeding limits raises `ResourceLimitExceededError` without unbounded memory or CPU consumption.
