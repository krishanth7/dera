# Maintainability Testing Strategy

## Test Suite Architecture

The Phase 8.4 test suite validates metric computation, rule evaluation, boundary thresholds, dialect-specific keywords, and permutation invariance across 3 dedicated test modules:

1. **`tests/diagnostics/test_maintainability_metrics.py`**:
   - `test_is_lob_column`: Unbounded large text/binary storage type detection.
   - `test_compute_table_metrics`: Column composition, nullability ratio, default/identity counts.
   - `test_compute_schema_complexity`: Aggregate schema complexity metrics and normalized averages.
   - `test_matches_naming_profile`: Deterministic regex verification across `snake_case`, `camelCase`, `PascalCase`, `kebab-case`, `UPPER_SNAKE_CASE`.
   - `test_is_reserved_word`: Engine-specific SQL keywords for PostgreSQL, MySQL, SQLite.
   - `test_compute_naming_compliance`: Aggregate compliance scoring.
   - `test_compute_namespace_metrics`: Table distribution and imbalance ratio.
   - `test_coupling_metrics`: Total degree centrality, condensation depth, and cycle detection.

2. **`tests/diagnostics/test_maintainability_rules.py`**:
   - Evaluates all 8 Phase 8.4 diagnostic rules (`DERA-MNT-001` through `DERA-MNT-008`).
   - Verifies baseline vs. elevated thresholds, severity assignments, and evidence contents.
   - Verifies dialect-aware reserved word handling across PostgreSQL and MySQL.
   - Verifies rule exemption for single-namespace schemas (`NOT_APPLICABLE`).

3. **`tests/diagnostics/test_maintainability_determinism.py`**:
   - Executes 5 seeded randomized permutations over namespaces, tables, columns, graph nodes, and edges.
   - Verifies that rule evaluation outputs, finding order, and fingerprints remain 100% bitwise-identical regardless of input collection ordering.

## Verification Command

```powershell
python -m pytest tests/diagnostics/test_maintainability_metrics.py tests/diagnostics/test_maintainability_rules.py tests/diagnostics/test_maintainability_determinism.py -v
```
