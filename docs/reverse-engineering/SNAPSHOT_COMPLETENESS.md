# Metadata Completeness in Schema Snapshots

## 1. Completeness Classifications

Schema extractions can be limited by insufficient database privileges, connector limitations, or unmapped native data types.

DERA categorizes schema snapshot completeness via `MetadataCompleteness`:

| Level | Description |
| :--- | :--- |
| `COMPLETE` | Full structural capture of all tables, views, columns, constraints, indexes, and triggers in the specified catalog/schema. |
| `PARTIAL` | A subset of tables or schema objects was extracted due to filtering or connector capability. |
| `RESTRICTED` | Certain catalog tables could not be inspected due to insufficient permission (e.g. non-superuser on PostgreSQL). |
| `UNSUPPORTED` | Core database engine dialect constructs could not be translated into canonical representations. |
| `UNKNOWN` | Extraction completeness status could not be verified. |

---

## 2. Completeness Impact on Structural Fingerprints

Completeness is an intrinsic structural attribute of `SnapshotStructuralPayload`:

```python
class SnapshotStructuralPayload(BaseModel):
    ...
    completeness: MetadataCompleteness = MetadataCompleteness.COMPLETE
```

### Critical Invariance Rule
Matching fingerprints between two `PARTIAL` snapshots proves that the two partial captures are structurally equivalent.
However, matching fingerprints between two `PARTIAL` captures **does not** prove that the underlying source databases are complete or identical.

A snapshot marked `PARTIAL` will never produce the same fingerprint as an otherwise identical schema marked `COMPLETE`.
