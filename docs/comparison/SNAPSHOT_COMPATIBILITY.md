# Snapshot Compatibility & Version Boundaries

**Phase:** 9.1 — Deterministic Schema Snapshot Comparison Engine  

---

## 1. Supported Format Versions

The comparison engine supports snapshots conforming to:
- `SNAPSHOT_FORMAT_VERSION = "dera.schema.snapshot.v1"`
- `1.0.0` (Legacy initial release format)

If either snapshot presents an unsupported format version, the engine raises `IncompatibleSnapshotError`.

## 2. Engine Compatibility Policy

Phase 9.1 enforces:
- **Same-Engine Comparisons:** Fully supported across `postgresql`, `supabase`, `sqlite`, `mysql`, and `mariadb`.
- **Compatible Engine Families:** By default (`allow_compatible_engine_families=True`), engines sharing identical dialect families are permitted:
  - `postgres_family`: `postgresql` and `supabase`
  - `mysql_family`: `mysql` and `mariadb`
  - `sqlite_family`: `sqlite`
- **Cross-Engine Disallowed:** Comparing PostgreSQL to SQLite or MySQL raises `UnsupportedEngineComparisonError`.
