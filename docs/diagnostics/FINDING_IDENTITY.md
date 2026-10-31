# DERA Diagnostics — Finding Identity & Fingerprinting

**Milestone:** Phase 8.1 — Deterministic Schema Diagnostic Rules Engine  
**Module:** `packages/core/src/dera/diagnostics/fingerprint.py`  
**Status:** Canonical Reference  

---

## 1. Stable SHA-256 Finding Fingerprints

Every diagnostic finding is assigned a reproducible, cryptographic fingerprint. This identity allows findings to be tracked across migrations, schema revisions, and snapshot comparisons without depending on volatile run IDs.

### Fingerprint Components

```python
fingerprint_payload = {
    "rule_id": rule_id,
    "rule_version": rule_version,
    "object_id": object_id,
    "evidence": sorted([e.to_canonical_dict() for e in evidence], key=lambda d: (d["field_name"], str(d["observed_value"]))),
}
```

### Invariants
1. **No Volatile Data:** System timestamps, process IDs, and random run UUIDs are strictly excluded.
2. **Normalized Serialization:** Canonical JSON serialization uses sorted keys and standard separators (`","`, `":"`).
3. **Evidence Order Invariance:** Sorting evidence entries by `(field_name, observed_value)` guarantees that permutations in observation order do not alter the resulting fingerprint.
