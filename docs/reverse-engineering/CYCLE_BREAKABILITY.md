# Phase 6.4 Cycle Breakability & Remediation Analysis

## 1. Overview

When circular dependencies exist between database tables, direct sequential data loading or schema migration will fail due to foreign key violations. DERA analyzes the underlying constraint definitions to recommend deterministic cycle breakability strategies.

---

## 2. Breakability Strategies (`BreakabilityStrategy`)

Every detected `CycleInstance` is evaluated against structural constraints in the schema to determine the least invasive remediation strategy:

| Strategy | Feasibility Condition | Migration Remediation |
| :--- | :--- | :--- |
| `NULLABLE_FOREIGN_KEY` | At least one FK column in the cycle is nullable (`is_nullable=True`). | Insert rows with `NULL` in the breaking column; load other tables; update the foreign key column with valid parent IDs. |
| `DEFERRABLE_CONSTRAINT` | At least one FK constraint is marked deferrable (`DEFERRABLE INITIALLY DEFERRED`). | Execute loading transaction with constraints deferred until commit time. |
| `POST_DATA_LOAD_CONSTRAINT` | Non-nullable, non-deferrable cycle, but can be dropped and recreated as a post-load constraint. | Create tables without the breaking constraint; load data; apply `ALTER TABLE ... ADD CONSTRAINT` post-load. |
| `UNBREAKABLE` | Hard circular dependency with non-nullable columns, non-deferrable constraints, and strict schema immutability. | Flagged as validation `ERROR`. Requires architectural schema refactoring. |

---

## 3. Evaluation Order & Determinism

When multiple candidate break edges exist within a cycle, the breaking edge is chosen deterministically:
1. Prefer `NULLABLE_FOREIGN_KEY` over `DEFERRABLE_CONSTRAINT`.
2. Prefer `DEFERRABLE_CONSTRAINT` over `POST_DATA_LOAD_CONSTRAINT`.
3. If multiple edges share the same strategy, select the edge with the lexicographically smallest `edge_id`.
