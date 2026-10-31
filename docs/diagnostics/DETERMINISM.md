# DERA Diagnostics — Determinism & Reproducibility Guarantees

**Milestone:** Phase 8.1 — Deterministic Schema Diagnostic Rules Engine  
**Module:** `packages/core/src/dera/diagnostics/evaluator.py`, `packages/core/src/dera/diagnostics/serialization.py`  
**Status:** Canonical Reference  

---

## 1. Zero-Drift Guarantees

DERA diagnostics enforces mathematical determinism across all evaluation stages:

1. **Deterministic Rule Order:** All rules in the registry are evaluated sequentially in lexicographical order of `rule_id`.
2. **Deterministic Entity Traversal:** Entities within the canonical schema are sorted by canonical object identity tuples prior to rule processing.
3. **Deterministic Finding Sorting:** All aggregated findings are sorted by a documented stable tuple:
   ```python
   key = lambda f: (-f.severity.rank, f.object_id, f.rule_id, f.fingerprint)
   ```
4. **Deterministic Serialization:** JSON serialization strictly uses `sort_keys=True` and `ensure_ascii=True` with no platform-specific whitespace variances.
5. **Report Content Hash:** The report content hash (`report_hash`) computes a SHA-256 digest over the stable summary, coverage, rule outcomes, and findings while stripping execution time and evaluation UUIDs.
