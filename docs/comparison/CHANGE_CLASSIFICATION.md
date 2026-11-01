# Structural Change Classification & Evidence Model

**Phase:** 9.1 — Deterministic Schema Snapshot Comparison Engine  

---

## 1. Change Types

The comparison engine defines 6 distinct change outcomes (`ComparisonChangeType`):
- `ADDED`: Object exists in target snapshot but not in baseline snapshot.
- `REMOVED`: Object exists in baseline snapshot but not in target snapshot.
- `MODIFIED`: Object exists in both snapshots, with one or more modified properties.
- `UNCHANGED`: Object evaluated and verified structurally identical across both snapshots.
- `UNSUPPORTED`: Comparison cannot be evaluated due to engine or capability restrictions.
- `INDETERMINATE`: Missing required metadata prevents conclusive comparison.

## 2. Before-and-After Evidence

Every `SchemaChange` record requires verifiable evidence:
- **ObjectEvidence:** Contains the source `snapshot_id`, `canonical_id`, `namespace`, `name`, `properties` dictionary, and `completeness` state.
- **PropertyDifference:** For `MODIFIED` objects, contains `property_name`, `before_value`, `after_value`, and `status`.

No modification is ever reported without verified values from both snapshots.
