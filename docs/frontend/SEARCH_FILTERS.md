# Search Filters Specification

**Module**: `apps/web/src/components/schema-search/SearchFiltersPanel.tsx`  
**Phase**: 7.5 — Table Inspector, Advanced Search & Dependency Visualization  

---

## 1. Overview

The Search Filters panel enables engineers to constrain search scope across multiple dimensions without losing search context.

---

## 2. Available Filter Dimensions

1. **Object Type**:
   - `All Objects`: Searches across all registered schema entities.
   - `Tables`: Matches relational tables.
   - `Views`: Matches database views.
   - `Columns`: Matches individual columns and data types.
   - `Constraints`: Matches primary keys, foreign keys, unique keys, and check rules.
   - `Indexes`: Matches database indexes.
   - `Namespaces`: Matches schemas and namespaces.

2. **Schema Scope**:
   - Dropdown listing all authorized database connections in the current workspace.

3. **Namespace Filter**:
   - Dropdown listing all discovered namespaces within the selected schema scope.

4. **Constraint Category**:
   - Active when searching constraints: `PRIMARY_KEY`, `FOREIGN_KEY`, `UNIQUE`, `CHECK`.

5. **Active Filter Indicators**:
   - Visual badges display active filter criteria with a one-click "Reset Filters" action.
