# Snapshot Provenance Specification

## 1. Provenance Model

Every schema snapshot envelope embeds a `SnapshotProvenance` record capturing source environment metadata:

```python
class SnapshotProvenance(BaseModel):
    source_engine: str
    source_version: str
    connector_version: str | None = None
    capture_timestamp: datetime
    consistency: CaptureConsistency = CaptureConsistency.UNKNOWN
    completeness: MetadataCompleteness = MetadataCompleteness.COMPLETE
    native_identifier: str | None = None
```

---

## 2. Capture Consistency States

Relational databases may be modified concurrently while metadata is being extracted by Phase 5 connectors.

The `CaptureConsistency` enum documents the transactional guarantees under which metadata was gathered:

| Value | Description |
| :--- | :--- |
| `TRANSACTIONALLY_CONSISTENT` | Connector operated inside a repeatable-read or serializable transaction with a single catalog snapshot (e.g. PostgreSQL `SET TRANSACTION ISOLATION LEVEL REPEATABLE READ`). |
| `POINT_IN_TIME_CONSISTENT` | Underlying storage snapshot taken at a single consistent physical LSN or WAL position. |
| `BEST_EFFORT` | Connector queried information schema tables consecutively across distinct transactions. Potential race conditions between table and constraint collection. |
| `UNKNOWN` | Source consistency guarantee could not be verified by the connector. |

DERA strictly prohibits claiming transactional consistency unless the connector explicitly guarantees and certifies it.

---

## 3. Provenance vs. Fingerprint Boundary

Provenance data lives strictly within `SnapshotEnvelope.provenance`.
It documents *how* and *when* the schema was extracted, while `SnapshotStructuralPayload` documents *what* the schema is.

Therefore, extracting the same schema with connector v1.0.0 and later with connector v1.1.0 preserves identical structural fingerprints while updating the envelope's provenance history.
