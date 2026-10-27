# Metadata Dialect Compatibility Matrix

**Subsystem:** `dera.metadata`  

---

## 1. Engine Normalization Matrix

| Engine | Canonical Namespace | Data Type Classification | Generated Columns | Check Constraints | Functional Indexes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **PostgreSQL** | `database.schema` | Full SQL types + Arrays + Domains | `STORED` | Fully supported | Expression terms recorded |
| **Supabase PostgreSQL** | `database.schema` | Inherits PostgreSQL adapter | `STORED` | Fully supported | Expression terms recorded |
| **SQLite** | `main` / attached db | Type affinity rules (5 rules) | `VIRTUAL` / `STORED` via `table_xinfo` | Supported; synthetic surrogate names | B-tree index terms |
| **MySQL** | `database` / schema | MySQL types + ENUM + SET | `STORED` / `VIRTUAL` | MySQL 8.0.16+; surrogate fallback | Supported (`EXPRESSION` terms) |
| **MariaDB** | `database` / schema | MySQL types + JSON alias | `PERSISTENT` (mapped to `STORED`) / `VIRTUAL` | Fully supported | Column terms |
