# Schema Search & Filtering Specification

**Document Reference**: `docs/frontend/SCHEMA_SEARCH.md`  
**Milestone**: Phase 7.3 — Database Connection & Schema Explorer UI  

---

## 1. Search Capabilities

The Schema Explorer includes client-side real-time filtering to support schemas with hundreds of tables and columns:

- **Entity Search**: Matches substrings in table names, view names, and namespace identifiers.
- **Debounced Input**: Instant filtering with keyboard input optimization.
- **Empty Filter State**: Clear visual callout with a one-click "Clear Search" action when no objects match the search criteria.

---

## 2. Namespace Filtering

In addition to text queries, users can constrain the navigation tree using the Namespace select menu:

```typescript
// Filter pipeline in Schema Explorer navigation tree
const filteredNamespaces = namespaces
  .filter(ns => activeNamespaceFilter === "all" || ns.name === activeNamespaceFilter)
  .map(ns => ({
    ...ns,
    tables: ns.tables.filter(table =>
      table.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      ns.name.toLowerCase().includes(searchQuery.toLowerCase())
    )
  }))
  .filter(ns => ns.tables.length > 0);
```
