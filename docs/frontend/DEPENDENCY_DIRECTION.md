# Dependency Direction & Graph Semantics

**Module**: `apps/web/src/components/dependency-explorer/`  
**Phase**: 7.5 — Table Inspector, Advanced Search & Dependency Visualization  

---

## 1. Directional Conventions

DERA enforces strict, consistent graph direction semantics rooted in Phase 6.3 foreign key graph contracts:

```text
+------------------------------------+
|  Referencing Table (Child Entity)  |
|          orders.customer_id        |
+-----------------+------------------+
                  |
                  | Foreign Key Edge (Dependency)
                  | points from child to parent
                  v
+------------------------------------+
|   Referenced Table (Parent Entity) |
|           customers.id             |
+------------------------------------+
```

---

## 2. Dependency Definitions

- **Child Depends on Parent**: `orders` cannot contain valid foreign keys until `customers` exists.
- **Outgoing Dependencies (Prerequisites)**: When inspecting a table, its outgoing edges represent parent tables that must exist *prior* to populating this table.
- **Incoming Dependents (Blast Radius)**: When inspecting a table, incoming edges represent child tables that reference this table and would be impacted by primary key modifications or drops.
- **Cycle Direction**: In cyclic references (`A -> B -> A`), mutual reachability creates a deadlock that requires foreign key deferral or nullable foreign keys.
