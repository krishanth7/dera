# Table Inspector Architecture & UI Specification

**Module**: `apps/web/src/components/table-inspector/`  
**Route**: `/tables/[tableId]` (and `/app/tables/[tableId]`)  
**Phase**: 7.5 — Table Inspector, Advanced Search & Dependency Visualization  

---

## 1. Overview

The Table Inspector provides a deep structural analysis view for any verified database table or view within an authorized workspace. It consumes Phase 6.2 canonical structural metadata via Phase 6.6 REST endpoints (`/api/v1/reverse-engineering/schemas/{schema_id}/tables/{table_id}`).

```text
                                  +----------------------------------+
                                  |      Table Metadata Header       |
                                  | Name, Namespace, Engine, Status  |
                                  +-----------------+----------------+
                                                    |
                                  +-----------------v----------------+
                                  |       Summary Stat Cards         |
                                  |  Cols, PK, FK, Unique, CK, Idx   |
                                  +-----------------+----------------+
                                                    |
         +--------------------+---------------------+--------------------+--------------------+
         |                    |                     |                    |                    |
+--------v-------+   +--------v-------+    +--------v-------+   +--------v-------+   +--------v-------+
|  Columns Tab   |   |Constraints Tab |    |  Indexes Tab   |   |Dependencies Tab|   | Raw JSON Tab   |
| Ordinals, PK/FK|   |  PK, FK, UQ, CK|    | Unique, Method |   | Up/Down stream |   | Provenance     |
+----------------+   +----------------+    +----------------+   +----------------+   +----------------+
```

---

## 2. Component Composition

- **`TableMetadataHeader`**: Displays native table identity, namespace, engine badge (`postgresql`, `sqlite`, `mysql`, `mariadb`), completeness status (`COMPLETE`, `PARTIAL`, `RESTRICTED`), snapshot indicator, and action links to the ER Canvas, Dependency Explorer, and Schema Explorer.
- **`TableSummaryCards`**: Interactive stat counters for columns, primary keys, foreign keys, unique constraints, check constraints, and indexes. Clicking any card switches the active tab.
- **`ColumnsTab`**: Ordinal column table with client-side sorting, text filtering, primary/foreign key badges, and expandable column inspection rows.
- **`ConstraintsTab`**: Detailed constraint inspection supporting multi-column composite primary keys, composite foreign key mappings, native referential actions (`ON UPDATE`, `ON DELETE`), unique constraints, and inert check constraint expressions.
- **`IndexesTab`**: Index inspection displaying indexed columns, uniqueness, and primary status.
- **`DependenciesTab`**: Immediate upstream and downstream dependencies with cycle status detection and direct link to the Dependency Explorer.
- **`RawMetadataTab`**: Formatted JSON representation of the canonical table object with clipboard copy action.
