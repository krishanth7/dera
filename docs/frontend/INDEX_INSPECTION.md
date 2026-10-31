# Index Inspection Specification

**Document Reference**: `docs/frontend/INDEX_INSPECTION.md`  
**Milestone**: Phase 7.3 — Database Connection & Schema Explorer UI  

---

## 1. Index Metadata Display

The Indexes tab provides visibility into performance access paths and uniqueness constraints implemented via indexes.

### Displayed Index Fields

- **Index Name**: Database identifier of the index (e.g. `idx_users_email_lower`).
- **Uniqueness**: Badge denoting `UNIQUE` or `NON-UNIQUE`.
- **Index Method / Type**: Access method such as `BTREE`, `GIN`, `GIST`, `HASH`, or engine default.
- **Indexed Columns**: Ordered list of covered attributes including sort direction (`ASC`, `DESC`, `NULLS LAST`).
- **Partial / Filter Predicate**: Inert text display of index `WHERE` clauses where present.

```text
+-------------------------------------------------------------------------+
| [INDEX] idx_users_active_email                                          |
| Method: BTREE • Type: UNIQUE                                            |
| Columns: (email ASC, tenant_id ASC)                                     |
| Filter Expression: WHERE deleted_at IS NULL                             |
+-------------------------------------------------------------------------+
```
