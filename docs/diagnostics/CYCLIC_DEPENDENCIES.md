# DERA-DEP-001: Circular Foreign Key Dependencies & SCCs

## 1. Rule Definition
- **Rule ID**: `DERA-DEP-001`
- **Rule Title**: Circular Foreign Key Dependencies & Strongly Connected Components
- **Category**: `DEPENDENCIES`
- **Default Severity**: `MEDIUM` (downgraded to `LOW` for single-node self-loops)
- **Applicability**: All relational database engines supporting foreign keys.

## 2. Theoretical Foundation
A directed cycle occurs when a sequence of foreign keys forms a loop ($A \to B \to \dots \to A$). In relational databases:
1. **Self-Referential Relationships ($A \to A$)**: Hierarchies and trees (e.g. `employees.manager_id \to employees.id`). Valid when the FK is nullable or root rows have `NULL` parent pointers.
2. **Mutual Dependencies ($A \to B$ and $B \to A$)**: Two tables pointing to each other.
3. **Indirect Dependency Cycles ($A \to B \to C \to A$)**: Multi-table cycles.

## 3. Operational Implications
Circular dependencies break linear topological sorting (Kahn's algorithm). Operations affected include:
- **Migration & Table Creation**: Tables cannot be created before their referenced parents without deferrable constraints or multi-stage DDL.
- **Bulk Data Loading**: Seeding initial rows requires disabling constraints or setting nullable parent keys.
- **Table Truncation / Drop**: Cascade operations require ordered foreign key disablement.

## 4. Evaluation & Severity
- Single-node self-loops: Severity `LOW`. Rationale: Standard hierarchical design pattern; requires nullable FK for root rows.
- Multi-node SCCs: Severity `MEDIUM`. Rationale: Prevents linear topological sorting; requires transactional deferrable constraints or migration breakages.
