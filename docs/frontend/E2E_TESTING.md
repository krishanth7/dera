# End-to-End User Journeys & Smoke Testing

**Module**: `apps/web/`  
**Phase**: 7.6 — Accessibility, Responsive Design & Frontend Quality Assurance  

---

## 1. End-to-End User Journeys

Phase 7.6 validates the complete end-to-end integration across all Phase 7 visual engineering studios:

```text
[ 1. User Sign In / Session Restore ]
                |
                v
[ 2. Workspace Selection & Verification ]
                |
                v
[ 3. Database Connection & Dialect Probe ]
                |
                v
[ 4. Schema Explorer & Namespace Navigation ]
                |
                +---> [ 5a. Table Inspector: Columns, PK/FK, Indexes, Provenance ]
                |
                +---> [ 5b. Interactive ER Diagram Canvas: Node, Edge, Pan/Zoom ]
                |
                +---> [ 5c. Advanced Search: Debounced multi-type filtering ]
                |
                v
[ 6. Dependency Explorer: Direct, Transitive (BFS), Cycles (Tarjan/Johnson) ]
                |
                v
[ 7. Secure Session Logout / Token Invalidation ]
```

---

## 2. Tested Journey Scenarios

1. **Authentication & Workspaces**: Sign in with verified credentials, navigate workspace switcher, inspect workspace role permissions (`OWNER`, `ENGINEER`).
2. **Schema Reverse Engineering**: Connect to a verified database (PostgreSQL, SQLite, MySQL), probe dialect, load schema tables.
3. **Table Inspection Flow**: Open `/tables/[tableId]`, inspect 15+ columns, sort by ordinal, verify composite foreign key mappings, and expand column detail drawer.
4. **Relationship Visualization**: Open `/relationships`, verify auto-layout coordinates, pan canvas, click table node, inspect constraints in drawer.
5. **Search to Inspection**: Open `/search`, query `orders`, apply `tables` and `columns` filters, click search result, deep-link to Table Inspector.
6. **Cycle Detection Flow**: Open `/dependencies`, identify circular foreign key loops, view breakability strategy (`DEFER_FOREIGN_KEY`, `NULLIFY_COLUMN`), and toggle WCAG 2.2 accessible table mode.
