# Canonical Object Matching & Identity Rules

**Phase:** 9.1 — Deterministic Schema Snapshot Comparison Engine  

---

## 1. Matching Semantics

Schema objects are matched deterministically across baseline and target snapshots:

| Object Type | Canonical Matching Key | Identity Source |
| :--- | :--- | :--- |
| **Namespace** | `namespace_name` | Direct string match |
| **Table** | `namespace.table_name` | Scoped table identifier |
| **Column** | `column_name` | Table-scoped native column name |
| **Primary Key** | `constraint_name` or `"PRIMARY_KEY"` | Table-scoped primary key |
| **Foreign Key** | `constraint_name` or `fk_cols_<source_cols>` | Scoped foreign key constraint |
| **Unique Constraint** | `constraint_name` or `unq_cols_<cols>` | Scoped unique constraint |
| **Check Constraint** | `constraint_name` or `chk_<expr_prefix>` | Scoped check constraint |
| **Index** | `index_name` | Table-scoped index name |
| **View** | `namespace.view_name` | Scoped view identifier |
| **Relationship** | `edge_id` or `src->tgt:constraint` | Directed FK edge identifier |

## 2. Rename Policy

An object present in baseline but missing in target is classified as `REMOVED`. An object missing in baseline but present in target is classified as `ADDED`. They are **never** automatically merged as a rename without explicit cryptographic or metadata lineage continuity.
