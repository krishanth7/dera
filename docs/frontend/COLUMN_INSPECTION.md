# Column Inspection Specification

**Module**: `apps/web/src/components/table-inspector/ColumnsTab.tsx`  
**Phase**: 7.5 — Table Inspector, Advanced Search & Dependency Visualization  

---

## 1. Overview

The Column Inspection tab provides granular attribute evaluation for every column defined on a table, preserving native column ordinal positions as defined in the source database catalog.

---

## 2. Display Attributes

Each column row renders:
1. **Ordinal Position**: 1-based native column index.
2. **Column Name**: Exact native identifier formatted in monospaced typography.
3. **Native Type & Canonical Type**: Engine-specific native type (e.g. `varchar(255)`, `uuid`, `timestamptz`) accompanied by the DERA canonical classification (`string`, `integer`, `timestamp`, `boolean`).
4. **Nullability**: Explicit visual distinction between `NOT NULL` (amber warning badge) and `NULL` (neutral check indicator).
5. **Key Indicators**:
   - **Primary Key (PK)**: Gold badge indicating primary key membership.
   - **Foreign Key (FK)**: Blue badge displaying the target table and referenced column name.
6. **Default Expression**: Inert SQL default value or snippet.

---

## 3. Sorting & Filtering

- **Deterministic Sort Fields**: Ordinal position (default), column name, data type, and nullability.
- **Client-Side Filter**: Real-time substring filter matching column names or data type strings.
- **Expandable Detail Drawer**: Clickable chevron reveals stable column object ID, canonical mappings, and specific foreign key constraint names.
