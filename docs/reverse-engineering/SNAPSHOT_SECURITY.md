# Snapshot Subsystem Security Controls

## 1. Zero Credential Embedding

Snapshots contain schema definitions, table structures, and constraint logic.
Under no circumstances do snapshots contain passwords, connection strings, API tokens, or secrets:
- Database connection strings are decoupled from `CanonicalDatabase.id` and `SnapshotEnvelope.provenance`.
- `test_no_credentials_embedded_in_payload` continuously scans serialized snapshots for key terms (`password`, `secret`, `bearer`, `access_token`).

---

## 2. Workspace Isolation & Path Traversal Prevention

In multi-tenant or enterprise environments, snapshots belonging to Workspace A must never be accessible to Workspace B:
- `FileSystemSnapshotStorage` invokes `sanitize_workspace_id()` on all operations.
- Rejects path traversal sequences (`..`, `/`, `\`, null bytes, control characters).
- Storage operations resolve absolute paths and verify `path.is_relative_to(base_dir / sanitized_workspace)`.
- Attempting to query `get_by_id(snap_id, "workspace_b")` returns `None` or raises `SnapshotNotFoundError`, preventing ID-enumeration attacks.

---

## 3. Denial-of-Service (DoS) Limits

Payload parsing is guarded by strict bounds (`SnapshotResourceLimits`):
- `max_serialized_bytes`: 50 MB limit on incoming JSON payloads.
- `max_object_count`: 100,000 maximum schema objects per snapshot.
- `max_nesting_depth`: 32 maximum recursive JSON depth.
- `max_identifier_length`: 1,024 characters per table or column name.
- `max_sql_expression_bytes`: 65,536 bytes per native expression (views, defaults).
- Non-finite numbers (`NaN`, `Infinity`) trigger immediate deserialization rejection.
