# Schema Snapshot Storage Architecture

## 1. Storage Contract Interface

The `SnapshotStorage` abstract base class governs persistence operations:

```python
class SnapshotStorage(ABC):
    @abstractmethod
    async def save(self, snapshot: SchemaSnapshot) -> None: ...

    @abstractmethod
    async def get_by_id(self, snapshot_id: str, workspace_id: str) -> SchemaSnapshot | None: ...

    @abstractmethod
    async def get_by_fingerprint(
        self, fingerprint: str, workspace_id: str
    ) -> list[SchemaSnapshot]: ...

    @abstractmethod
    async def list_snapshots(self, filter_criteria: SnapshotFilter) -> list[SchemaSnapshot]: ...

    @abstractmethod
    async def delete(self, snapshot_id: str, workspace_id: str) -> bool: ...

    @abstractmethod
    async def verify(self, snapshot_id: str, workspace_id: str) -> SnapshotIntegrityReport: ...
```

---

## 2. In-Memory Implementation (`InMemorySnapshotStorage`)

Optimized for ephemeral testing, worker caches, and execution pipelines:
- **Workspace Isolation**: Primary partition keyed by `workspace_id`.
- **Content Deduplication**: Payloads indexed by `fingerprint`, reusing structural payload allocations across duplicate captures while preserving distinct capture metadata envelopes.
- **Defensive Immutability**: Enforces `snapshot_id` unicity per workspace (raises `SnapshotStorageError` if overwriting is attempted).

---

## 3. Filesystem Implementation (`FileSystemSnapshotStorage`)

Production-ready local and volume-mounted persistence:
- **Directory Layout**: `<base_path>/<workspace_id>/<snapshot_id>.json`
- **Atomic Writes**: Writes first to `<snapshot_id>.tmp.<uuid>`, forces flush, then atomically renames (`os.replace`) to `<snapshot_id>.json`.
- **Path Traversal Guards**: Validates that resolved target paths strictly stay within `base_path/<workspace_id>` using `sanitize_workspace_id()`. Rejects `..`, `/`, and null bytes.
- **Immutability Protection**: `save()` checks if the target file exists before writing; raises `SnapshotStorageError` to prevent silent clobbering.
- **Safe Retrieval**: Reconstructs snapshots using `deserialize_snapshot_from_json()` with DoS resource limit enforcement.
