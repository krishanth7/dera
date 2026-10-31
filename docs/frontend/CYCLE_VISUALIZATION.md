# Cycle Detection & Strongly Connected Component Visualization

**Module**: `apps/web/src/components/dependency-explorer/CycleAnalysisPanel.tsx`  
**Route**: `/dependencies`  
**Phase**: 7.5 — Table Inspector, Advanced Search & Dependency Visualization  

---

## 1. Overview

Circular foreign key relationships prevent naive topological sorting, complicate migration sequences, and necessitate deferred constraint checking or nullable foreign keys. DERA integrates Phase 6.4 cycle analysis results to detect, isolate, and visualize cycles without running heuristic ML models.

```text
+-------------------------------------------------------------------------+
|                  Circular Foreign Key Analysis                          |
+-------------------------------------------------------------------------+
| [!] 1 Elementary Cycle Detected across 2 tables                         |
+-------------------------------------------------------------------------+
| Cycle #1: users -> teams -> users                                       |
| - users.team_id  -> teams.id                                            |
| - teams.owner_id -> users.id                                            |
|                                                                         |
| Recommended Resolution: DEFER_FOREIGN_KEY or NULLIFY_COLUMN            |
+-------------------------------------------------------------------------+
| Strongly Connected Components (SCC):                                    |
| - SCC #1 (Cyclic): [users, teams]                                       |
| - SCC #2 (Acyclic): [organizations]                                     |
| - SCC #3 (Acyclic): [roles]                                             |
+-------------------------------------------------------------------------+
```

---

## 2. Theoretical Foundation

Cycle detection in DERA uses exact graph algorithms executed deterministically by the backend:

1. **Tarjan's SCC Algorithm**: Partitions the schema's directed relationship graph into Strongly Connected Components. Any SCC with more than one node (or a single node with a self-referential edge) contains circular dependencies.
2. **Johnson's Algorithm**: Enumerates all simple (elementary) cycles within cyclic SCCs, generating explicit loop paths (e.g., $A \to B \to C \to A$).
3. **Breakability Strategy Engine**: Inspects foreign key column nullability and constraint deferrability to compute the least-destructive migration strategy:
   - `DEFER_FOREIGN_KEY`: Constraint is deferrable (`INITIALLY DEFERRED`).
   - `NULLIFY_COLUMN`: Foreign key column is nullable, allowing table insertion with `NULL` before updating relationships.
   - `RESTRICT`: Foreign key is non-nullable and immediate; requires circular two-phase DDL migrations.

---

## 3. UI Display Components

- **Cycle Alert Banner**: Highlights presence and severity of cycles with explicit cycle counts.
- **Cycle Path Cards**: Renders the complete traversal loop with directed arrows and edge metadata.
- **Breakability Strategy Pill**: Visual badge denoting strategy (`DEFER_FOREIGN_KEY`, `NULLIFY_COLUMN`, `RESTRICT`) with explanatory tooltips.
- **SCC Inventory**: Accordion view categorizing all SCCs into cyclic vs. acyclic groupings, displaying component size and table memberships.
- **Educational Context**: Contextual callout explaining that circular relationships are valid database constructs (e.g., manager/employee, team/owner) and detailing operational migration impacts.
