# Table Overview Specification

**Document Reference**: `docs/frontend/TABLE_OVERVIEW.md`  
**Milestone**: Phase 7.3 — Database Connection & Schema Explorer UI  

---

## 1. Table Inspector Header & Metrics

When a table or view is selected in the navigation tree, the Table Inspector displays identity metadata and structural metrics.

```text
+-------------------------------------------------------------------------+
| [TABLE] public.users                                                    |
| Object ID: tbl_98a72b14 • Canonical Name: public.users                  |
|                                                                         |
| [ 12 Columns ]   [ 1 Primary Key ]   [ 2 Foreign Keys ]   [ 3 Indexes ] |
+-------------------------------------------------------------------------+
| Tabs: [Columns]  [Constraints]  [Indexes]  [Provenance]                 |
+-------------------------------------------------------------------------+
```

---

## 2. Metric Summaries

- **Relation Type**: Identifies whether the entity is a base `table`, `view`, or `materialized_view`.
- **Primary Key Status**: Indicates presence and column count of the primary key constraint.
- **Foreign Key Count**: Displays incoming and outgoing referential relationships.
- **Index Count**: Summarizes secondary access paths and unique index definitions.
- **Completeness & Provenance**: Reflects extraction verification timestamps and connector confidence.
