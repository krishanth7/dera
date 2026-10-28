# Snapshot Compatibility & Equivalence Model

## 1. Supported Format Versions

DERA snapshot engines track supported versions via `SnapshotCompatibilityChecker`:
- Supported Versions: `("dera.schema.snapshot.v1",)`
- Supported Fingerprint Algorithms: `("sha256",)`

Attempting to deserialize or verify an unsupported version raises `SnapshotIncompatibleVersionError`.

---

## 2. Equivalence Levels

Two snapshots can be compared via `SnapshotCompatibilityChecker.check_equivalence(a, b)`:

| Equivalence Level | Criteria | Interpretation |
| :--- | :--- | :--- |
| `EXACT_BYTE_IDENTICAL` | Identical full JSON serialization bytes (including all envelope metadata, timestamps, and tags). | Exact duplicate snapshot record. |
| `STRUCTURAL_FINGERPRINT_MATCH` | Identical `fingerprint` hash. Envelopes may differ (e.g. captured on different days). | Schemas are structurally identical. |
| `NONE` | Fingerprints differ or databases differ. | Schemas are distinct. |

---

## 3. Cross-Engine Equivalence Limitation

DERA preserves native SQL engine constructs in `SnapshotStructuralPayload` (such as native column types and constraint dialect semantics).

Consequently, a PostgreSQL schema and an equivalent MySQL schema will produce distinct structural fingerprints because native data types differ (`serial` vs `int auto_increment`).
Cross-engine equivalence is evaluated at the semantic diff level in Phase 9, not via identical SHA-256 fingerprint matching.
