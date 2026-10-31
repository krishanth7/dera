# Constraint Inspection Specification

**Module**: `apps/web/src/components/table-inspector/ConstraintsTab.tsx`  
**Phase**: 7.5 — Table Inspector, Advanced Search & Dependency Visualization  

---

## 1. Overview

The Constraint Inspection tab surfaces all verified integrity constraints belonging to a table: Primary Keys, Foreign Keys, Unique Constraints, and Check Constraints.

---

## 2. Constraint Categories

### 2.1 Primary Key Constraints
- Preserves multi-column composite primary key semantics.
- Displays ordered column list (e.g. `(#1 tenant_id, #2 order_id)`).
- Never represents composite columns as separate independent primary keys.

### 2.2 Foreign Key Constraints
- Displays referencing child table and referenced parent table.
- Renders ordered column pair mappings:
  `(source_col_1, source_col_2) -> (target_col_1, target_col_2)`
- Surfaces native referential actions:
  - `ON DELETE`: `CASCADE`, `RESTRICT`, `SET NULL`, `NO ACTION`, `SET DEFAULT`
  - `ON UPDATE`: `CASCADE`, `RESTRICT`, `SET NULL`, `NO ACTION`, `SET DEFAULT`
- Direct link to inspect the referenced parent table in the same schema.

### 2.3 Unique Constraints
- Surfaces constraint identity and ordered unique column lists.
- Differentiates declared unique constraints from unique secondary indexes.

### 2.4 Check Constraints
- Renders raw SQL check expressions as inert, syntax-styled text.
- Untrusted SQL text is completely escaped to prevent script injection or DOM interpretation.
