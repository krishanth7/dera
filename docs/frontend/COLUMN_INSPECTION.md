# Column Inspection Specification

**Document Reference**: `docs/frontend/COLUMN_INSPECTION.md`  
**Milestone**: Phase 7.3 — Database Connection & Schema Explorer UI  

---

## 1. Technical Column Table

The Columns tab renders an exhaustive, sortable technical table of all attributes belonging to the inspected relation.

### Table Columns

| Header | Description | Example |
|---|---|---|
| `#` | Ordinal position in relation | `1`, `2`, `3` |
| `Name` | Column identifier with PK indicator | `id` `[PK]`, `email` |
| `Native Type` | Engine-specific raw database type | `varchar(255)`, `timestamptz` |
| `Canonical Type` | Normalized DERA canonical type | `string`, `timestamp`, `uuid` |
| `Nullable` | Nullability constraint status | `NOT NULL` (red badge), `NULL` (gray badge) |
| `Default` | Default value expression | `'active'::text`, `CURRENT_TIMESTAMP` |
| `Attributes` | Auto-increment, identity, or generated flags | `IDENTITY(1,1)`, `GENERATED ALWAYS` |

---

## 2. Ordinal Ordering Preservation

Columns are rendered in physical database ordinal sequence to preserve database engineering context, with optional user-driven sorting by name or type.
All default expressions and generated formulas are escaped to prevent XSS.
