# DERA SQLite Connector Configuration

## Overview

The SQLite connector is configured through the strongly-typed `SqliteConnectorConfig` model, inheriting from `ConnectorConfig` in `packages/connectors/src/dera_connectors/sqlite/configuration.py`.

Unlike PostgreSQL, SQLite configuration intentionally omits `host`, `port`, `username`, `password`, and `tls` settings.

---

## Configuration Model Reference

### `SqliteConnectorConfig`

| Field | Type | Default | Description |
|---|---|---|---|
| `engine` | `DatabaseEngine` | `DatabaseEngine.SQLITE` | Engine identifier (`sqlite`). |
| `database` | `str` | *(Required)* | Approved filesystem path or storage identifier referencing the SQLite database file. |
| `approved_storage_roots` | `list[str]` | `[]` | List of authorized directory roots. When non-empty, paths outside these roots are rejected with `ConnectorSecurityViolationError`. |
| `allow_memory_databases` | `bool` | `False` | Whether in-memory database targets (`:memory:`) are permitted (restricted to test environments). |
| `read_only` | `bool` | `True` | Enforce read-only access mode (`mode=ro`). Must remain `True` in all production workloads. |
| `immutable_snapshot` | `bool` | `False` | When `True`, appends `immutable=1` to SQLite URI for verified write-once snapshots. |
| `busy_timeout_ms` | `int` | `5000` | SQLite busy handler timeout in milliseconds before raising `sqlite3.BusyError`. |
| `max_file_size_bytes` | `int` | `10737418240` (10 GB) | Upper boundary for target database file size. |
| `timeouts` | `TimeoutSettings` | Standard timeouts | Operation deadlines (connect: 10s, query: 30s, metadata: 60s). |

---

## Example Configuration

```python
from dera_connectors.sqlite.configuration import SqliteConnectorConfig
from dera_connectors.configuration import TimeoutSettings

config = SqliteConnectorConfig(
    database="/data/workspaces/ws_123/production.sqlite",
    approved_storage_roots=["/data/workspaces/ws_123"],
    read_only=True,
    busy_timeout_ms=5000,
    timeouts=TimeoutSettings(
        connect_timeout_seconds=5.0,
        query_timeout_seconds=15.0,
        metadata_timeout_seconds=30.0,
    ),
)
```
