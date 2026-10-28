# Snapshot Retention & Lifecycle Management

## 1. Retention Policy Model

The `SnapshotRetentionPolicy` configuration governs snapshot pruning:

```python
class SnapshotRetentionPolicy(BaseModel):
    max_snapshots_per_database: int | None = Field(default=50)
    max_age_days: int | None = Field(default=365)
    protected_tags: tuple[str, ...] = Field(default=("production", "baseline", "release"))
    preserve_unique_fingerprints: bool = Field(default=True)
```

---

## 2. Retention Execution (`RetentionManager`)

Pruning is managed via `RetentionManager.apply(storage, workspace_id, policy)`:

1. **Tag Protection**: Any snapshot possessing a tag in `protected_tags` is exempt from pruning.
2. **Unique Fingerprint Preservation**: If `preserve_unique_fingerprints` is `True`, the latest snapshot for every unique structural fingerprint is preserved, preventing the loss of historical schema iterations.
3. **Age Expiration**: Snapshots older than `max_age_days` (relative to current UTC) are marked for deletion.
4. **Count Pruning**: If the non-protected count exceeds `max_snapshots_per_database`, oldest snapshots are pruned first.
5. **Auditable Result**: Returns `RetentionActionResult` recording pruned IDs, retained IDs, and total storage reclaimed.
