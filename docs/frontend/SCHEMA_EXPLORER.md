# Schema Explorer Specification

**Document Reference**: `docs/frontend/SCHEMA_EXPLORER.md`  
**Milestone**: Phase 7.3 — Database Connection & Schema Explorer UI  

---

## 1. Overview & Layout Architecture

The Schema Explorer Studio (`/schemas/[schemaId]`) provides an interactive, read-only visual environment for browsing extracted database schemas, navigating object hierarchies, and analyzing entity relationships.

```text
+-----------------------------------------------------------------------------+
| Top Breadcrumb & Metadata Header: Schema Name • Engine • Completeness • Sync|
+------------------------------------+----------------------------------------+
| Navigation Tree (Left Pane)        | Detail Studio (Main Pane)              |
|                                    |                                        |
| [Search Objects...] [Namespace v]  | [Overview Mode]                        |
|                                    |   - High-level metrics & topology      |
| ▾ public (3 tables)                |                                        |
|    ▪ users                         | [Table Inspector Mode]                 |
|    ▪ orders                        |   - Tabs: Columns | Constraints |       |
|    ▪ order_items                   |           Indexes | Provenance         |
| ▾ analytics (1 table)              |   - Column types, nullability, defaults|
|    ▪ daily_metrics                 |   - PK, FK, Unique & Check definitions |
+------------------------------------+----------------------------------------+
```

---

## 2. Key Capabilities

- **Split-Pane Ergonomics**: Dedicated object navigation tree on the left and contextual detail studio on the right.
- **Hierarchical Tree Browsing**: Interactive namespace collapsible groups containing database tables and views.
- **Dual Studio Modes**:
  1. *Schema Overview*: High-level summary of total namespaces, tables, columns, constraints, foreign keys, and indexes.
  2. *Table Inspector*: Deep technical inspection with structured tabs for Columns, Constraints, Indexes, and Provenance.
- **Metadata Synchronization**: One-click refresh action triggering backend reverse-engineering re-inspection.
- **Zero-AI Determinism**: All relationships, types, and constraints reflect verified database metadata without generative inferences.
