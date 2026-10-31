# Constraint Inspection Specification

**Document Reference**: `docs/frontend/CONSTRAINT_INSPECTION.md`  
**Milestone**: Phase 7.3 — Database Connection & Schema Explorer UI  

---

## 1. Relational Constraint Categories

The Constraints tab renders structured cards for each verified database constraint, organized by semantic category:

### 1. Primary Keys
- Identifies unique row identifiers.
- Preserves multi-column composite key ordering (e.g. `(tenant_id, user_id)`).

### 2. Foreign Keys
- Explicitly links referencing columns to referenced namespace and table columns.
- Renders referential actions (`ON UPDATE`, `ON DELETE`) such as `CASCADE`, `RESTRICT`, `SET NULL`, `NO ACTION`.
- Indicates deferrability settings (`DEFERRABLE INITIALLY DEFERRED`).

### 3. Unique Constraints
- Highlights candidate keys and alternative unique constraints.
- Accurately renders single-column and composite unique definitions.

### 4. Check Constraints
- Displays check expressions as inert, syntax-highlighted code.
- Expressions are strictly rendered as text; browser-side execution is prohibited.

```text
+-----------------------------------------------------------------------+
| [FK] fk_orders_customer_id                                            |
| Type: FOREIGN KEY • Referencing: customer_id                          |
| Target: public.customers (id)                                         |
| Rules: ON UPDATE CASCADE • ON DELETE RESTRICT                         |
+-----------------------------------------------------------------------+
| [CHECK] chk_order_amount_positive                                     |
| Expression: amount > 0.00                                             |
+-----------------------------------------------------------------------+
```
