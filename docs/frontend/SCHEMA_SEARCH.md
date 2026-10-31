# Advanced Schema Search Architecture

**Module**: `apps/web/src/components/schema-search/`  
**Route**: `/search` (and `/app/search`)  
**Phase**: 7.5 — Table Inspector, Advanced Search & Dependency Visualization  

---

## 1. Overview

Advanced Schema Search enables cross-schema discovery of database objects within authorized workspaces. Engineers can locate tables, views, columns, foreign keys, primary keys, check constraints, unique constraints, and indexes through a unified, debounced search studio.

---

## 2. Searchable Object Types

- **Tables & Views**: Matches table names, view names, and table comments.
- **Columns**: Matches column names, native data types, and canonical types.
- **Constraints**: Matches constraint names, referenced parent tables, and check expressions.
- **Indexes**: Matches index names and participating column lists.
- **Namespaces**: Matches native schema names (e.g. `public`, `auth`, `billing`).

---

## 3. Query Execution & Performance

1. **Debouncing**: Input changes are debounced by 300ms to eliminate redundant network load.
2. **Cancellation**: In-flight requests are aborted when the search query changes using clean-up handlers.
3. **Pagination**: Results are paginated with selectable page sizes (10, 25, 50 rows per page) to maintain low memory consumption and instant UI responsiveness.
4. **Keyboard Shortcut**: Pressing `/` automatically focuses the search input from anywhere on the page.
