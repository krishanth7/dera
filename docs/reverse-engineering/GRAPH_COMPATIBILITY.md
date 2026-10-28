# Cross-Engine Foreign Key Semantics & Compatibility

## 1. Engine Capability Profiles

DERA normalizes foreign key relationship graphs across four supported database engines:

| Feature | PostgreSQL | Supabase | SQLite | MySQL / MariaDB |
| :--- | :--- | :--- | :--- | :--- |
| **Composite Keys** | Supported | Supported | Supported | Supported |
| **Cross-Schema References** | Supported | Supported | Unsupported (single schema per db) | Supported |
| **Self-Referencing Keys** | Supported | Supported | Supported | Supported |
| **Deferrability Options** | `DEFERRABLE`, `INITIALLY_DEFERRED` | `DEFERRABLE`, `INITIALLY_DEFERRED` | `DEFERRABLE` (SQLite 3.7+) | `NOT DEFERRABLE` only |
| **Match Types** | `FULL`, `PARTIAL`, `SIMPLE` | `FULL`, `PARTIAL`, `SIMPLE` | `NONE` | `NONE` |
| **Referential Actions** | `CASCADE`, `SET NULL`, `SET DEFAULT`, `RESTRICT`, `NO ACTION` | `CASCADE`, `SET NULL`, `SET DEFAULT`, `RESTRICT`, `NO ACTION` | `CASCADE`, `SET NULL`, `SET DEFAULT`, `RESTRICT`, `NO ACTION` | `CASCADE`, `SET NULL`, `RESTRICT`, `NO ACTION` (`SET DEFAULT` invalid in InnoDB) |
| **Enforcement Flag** | Always enforced | Always enforced | Pragma-dependent (`foreign_keys=ON`) | Engine-dependent (`InnoDB` enforced, `MyISAM` ignored) |

---

## 2. PostgreSQL & Supabase

PostgreSQL supports the full relational foreign key specification:
- Multi-namespace schemas (e.g., `public`, `auth`, `storage`, custom schemas).
- Deferrable constraints with initial evaluation control.
- Full constraint validation tracking (`NOT VALID` foreign keys).
- Rich referential action matrix.

The DERA graph builder preserves all PostgreSQL constraint names, deferrability settings, and match types in `ForeignKeyEdge`.

---

## 3. SQLite

SQLite stores foreign keys inside table declarations:
- Foreign key definitions are scoped within a single database file.
- SQLite parses foreign key constraints during table creation, but enforcement requires `PRAGMA foreign_keys = ON;`. DERA records constraint presence faithfully regardless of the runtime PRAGMA state.
- Column mappings preserve declared sequence numbers (`seq` column in `PRAGMA foreign_key_list`).

---

## 4. MySQL & MariaDB

MySQL (InnoDB) and MariaDB enforce strict referential rules:
- Requires indexes on both foreign key columns and referenced columns.
- Cross-database foreign keys are permitted across databases on the same host if permissions allow, mapped to cross-namespace relationships in DERA.
- Constraints are non-deferrable (`NOT_DEFERRABLE`).
- `SET DEFAULT` action is rejected by the InnoDB storage engine.

The graph builder checks engine capability flags via [`capabilities.py`](file:///packages/core/src/dera/reverse_engineering/graph/capabilities.py) to validate that engine-specific metadata is preserved accurately.
