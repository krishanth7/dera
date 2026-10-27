# DERA SQLite Connector Compatibility Matrix

## Supported SQLite & Python Runtimes

| Component | Minimum Version | Tested Versions | Support Level |
|---|---|---|---|
| **SQLite 3 Engine** | 3.35.0 (2021) | 3.39.x, 3.40.x, 3.42.x, 3.45.x+ | **Production Tier 1** |
| **Python Runtime** | 3.12+ | 3.12, 3.13, 3.14 | **Production Tier 1** |
| **Operating Systems** | Linux / macOS / Windows | Ubuntu 22.04/24.04, Windows Server 2022 | **Production Tier 1** |

---

## SQLite Feature Support

| SQLite Feature | Minimum SQLite Version | DERA Support Status |
|---|---|---|
| `PRAGMA table_xinfo` | 3.26.0 | Supported (Full generated column discovery) |
| `STRICT` Tables | 3.37.0 | Supported (Detected in `engine_specific`) |
| `WITHOUT ROWID` Tables | 3.8.2 | Supported (Detected in `engine_specific`) |
| Generated Columns | 3.31.0 | Supported (`STORED` and `VIRTUAL`) |
| Partial Indexes | 3.8.0 | Supported (Predicate extracted via `index_xinfo`) |
| Expression Indexes | 3.9.0 | Supported (Terms extracted via `index_xinfo`) |
| WAL Mode Reading | 3.7.0 | Supported (Read-only without checkpoint locking) |
