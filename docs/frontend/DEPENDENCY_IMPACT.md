# Structural Impact & Blast Radius Analysis

**Module**: `apps/web/src/components/dependency-explorer/`  
**Route**: `/dependencies` & `/tables/[tableId]`  
**Phase**: 7.5 — Table Inspector, Advanced Search & Dependency Visualization  

---

## 1. Overview

Structural impact analysis determines the ripple effects of modifying or dropping a database table or constraint. Rather than relying on predictive guesswork or LLMs, DERA uses the verified Phase 6.3 foreign key graph to compute exact reverse dependency trees.

```text
                  +--------------------------------+
                  |         Selected Table         |
                  |          [ customers ]         |
                  +---------------+----------------+
                                  |
                                  | referenced by
                                  v
                  +---------------+----------------+
                  |            orders              |
                  |     (Direct blast radius)      |
                  +---------------+----------------+
                                  |
                                  | referenced by
                                  v
                  +---------------+----------------+
                  |         order_items            |
                  |   (Transitive blast radius)    |
                  +--------------------------------+
```

---

## 2. Structural vs. Application Impact

DERA strictly separates verified structural impact from hypothetical application behavior:

| Category | DERA Treatment | Rationale |
| :--- | :--- | :--- |
| **Direct Structural Impact** | Verified | Directly referenced by foreign key constraints in other tables. Drops without `CASCADE` will fail immediately. |
| **Transitive Structural Impact** | Verified | Multi-hop dependents that cannot exist without the root table due to cascade rules or relational hierarchy. |
| **Application Layer Impact** | Non-Inferred | DERA does not guess application query impacts or runtime logic, maintaining strict deterministic standards. |

---

## 3. Impact Metrics in Phase 7.5

1. **Direct Dependents Count**: Number of tables immediately referencing the target table.
2. **Total Transitive Blast Radius**: Count of all downstream reachable tables across arbitrary hops.
3. **Execution Ordering Constraints**:
   - **Creation Rank**: Topological level during schema instantiation.
   - **Tear-Down Rank**: Reverse topological level during schema drop sequences.
4. **Referential Integrity Actions**:
   - Breakdown of downstream constraints by `ON DELETE CASCADE`, `ON DELETE SET NULL`, `ON DELETE RESTRICT`, and `NO ACTION`.
