# Index Inspection Specification

**Module**: `apps/web/src/components/table-inspector/IndexesTab.tsx`  
**Phase**: 7.5 — Table Inspector, Advanced Search & Dependency Visualization  

---

## 1. Overview

The Index Inspection tab visualizes secondary, primary, and unique indexes declared on a database entity, preserving engine-specific index semantics across PostgreSQL, SQLite, MySQL, and MariaDB.

---

## 2. Display Attributes

For every discovered index, the card presents:
1. **Index Name**: Native index identifier from system catalogs.
2. **Indexed Columns**: Ordered list of index key columns with ordinal markers (`#1`, `#2`, etc.).
3. **Uniqueness Flag**: Explicit `UNIQUE` badge indicating enforcing unique constraints or unique lookup indices.
4. **Primary Key Association**: `PRIMARY` badge indicating backing b-tree index for a table's primary key.
5. **Stable Object ID**: Canonical ID assigned during Phase 6.2 structural reconstruction.
