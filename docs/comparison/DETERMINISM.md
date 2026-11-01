# Determinism & Cryptographic Fingerprinting

**Phase:** 9.1 — Deterministic Schema Snapshot Comparison Engine  

---

## 1. Deterministic Ordering Invariant

Comparison results are sorted according to a strict multi-tier key before reporting:
1. Object Type Hierarchy (`NAMESPACE` -> `TABLE` -> `COLUMN` -> `PRIMARY_KEY` -> `UNIQUE_CONSTRAINT` -> `FOREIGN_KEY` -> `CHECK_CONSTRAINT` -> `INDEX` -> `VIEW` -> `TRIGGER` -> `RELATIONSHIP`)
2. Namespace (lexicographical)
3. Parent table name / Parent ID (lexicographical)
4. Native object name (lexicographical)
5. Canonical ObjectId (lexicographical)
6. ChangeType (`REMOVED` -> `MODIFIED` -> `ADDED` -> `UNCHANGED`)
7. Property Difference name (for granular property changes)
8. Cryptographic Fingerprint (tiebreaker)

## 2. Fingerprint Specifications

- **Change Fingerprint:** SHA-256 over canonical RFC 8785 JSON of `(comparator_version, object_type, canonical_id, change_type, changed_properties, before_properties, after_properties)`. Prefix: `DERA:DIFF:CHANGE:V1\n`.
- **Config Fingerprint:** SHA-256 over normalized configuration options. Prefix: `DERA:DIFF:CONFIG:V1\n`.
- **Report Fingerprint:** SHA-256 over `(baseline_fingerprint, target_fingerprint, config_fingerprint, sorted_change_fingerprints)`. Prefix: `DERA:DIFF:REPORT:V1\n`.
