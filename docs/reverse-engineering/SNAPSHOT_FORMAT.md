# Schema Snapshot Format Specification

## 1. Specification Identifier

- **Format Version**: `dera.schema.snapshot.v1`
- **Fingerprint Algorithm**: `sha256`
- **Fingerprint Domain**: `DERA:SCHEMA:STRUCTURAL:V1`

---

## 2. Top-Level SchemaSnapshot Schema

The top-level `SchemaSnapshot` contract defines the full serializable unit of an immutable snapshot:

| Field | Type | Description |
| :--- | :--- | :--- |
| `format_version` | `str` | Format specification version (`dera.schema.snapshot.v1`). |
| `snapshot_id` | `str` | Stable snapshot record identifier (`snap_<hex32>`). |
| `fingerprint` | `str` | Hex-encoded SHA-256 structural content digest (64 characters). |
| `fingerprint_algorithm` | `str` | Name of algorithm (`sha256`). |
| `fingerprint_domain` | `str` | Explicit domain separator (`DERA:SCHEMA:STRUCTURAL:V1`). |
| `database_id` | `str` | Canonical ObjectId of the source database. |
| `database_name` | `str` | Native database name. |
| `engine` | `str` | Normalized engine identifier (`postgresql`, `sqlite`, etc.). |
| `payload` | `SnapshotStructuralPayload` | Frozen canonical structural schema representation. |
| `envelope` | `SnapshotEnvelope` | Operational and environmental capture metadata. |

---

## 3. Structural Payload Contract

```json
{
  "database_id": "dera:database:5fbc03cc91bdc419857dc621",
  "database_name": "app_db",
  "engine": "postgresql",
  "tables": [
    {
      "table_id": "dera:table:5fbc03cc91bdc419857dc622",
      "namespace": "public",
      "name": "users",
      "table_type": "TABLE",
      "columns": [
        {
          "column_id": "dera:column:5fbc03cc91bdc419857dc623",
          "name": "id",
          "ordinal_position": 1,
          "native_type": "integer",
          "canonical_type": "INTEGER",
          "is_nullable": false,
          "default_expression": null
        }
      ],
      "primary_key": {
        "constraint_id": "dera:constraint:5fbc03cc91bdc419857dc624",
        "name": "pk_users",
        "columns": ["id"]
      },
      "foreign_keys": [],
      "unique_constraints": [],
      "check_constraints": [],
      "indexes": []
    }
  ],
  "views": [],
  "triggers": [],
  "relationships": [],
  "dependencies": {
    "total_edges": 0,
    "has_cycles": false,
    "cycle_count": 0,
    "scc_count": 1,
    "cyclic_scc_count": 0,
    "topological_levels_count": 1
  },
  "completeness": "COMPLETE"
}
```

---

## 4. Operational Envelope Contract

```json
{
  "capture_timestamp": "2026-10-28T12:00:00.000000Z",
  "workspace_id": "ws_production",
  "requester_id": "usr_admin",
  "storage_location": "file:///var/dera/snapshots/ws_production/snap_794632676cf14110808621db66f099ba.json",
  "provenance": {
    "source_engine": "postgresql",
    "source_version": "16.1",
    "connector_version": "1.0.0",
    "capture_timestamp": "2026-10-28T12:00:00.000000Z",
    "consistency": "TRANSACTIONALLY_CONSISTENT",
    "completeness": "COMPLETE",
    "native_identifier": "app_db"
  },
  "validation_findings": [],
  "tags": ["prod", "release-2.4"]
}
```

---

## 5. Backward Compatibility & Extension Rules

1. New optional structural fields must default to standard empty representations (e.g., `()` or `None`).
2. Fields cannot be reordered or removed in `dera.schema.snapshot.v1`.
3. If structural canonicalization rules or hashing boundaries evolve, the version must advance to `dera.schema.snapshot.v2` with a distinct fingerprint domain.
