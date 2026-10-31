# Engine-Specific Index and Constraint Semantics

## 1. Engine Capability Matrix

| Feature / Semantics | PostgreSQL | Supabase | SQLite | MySQL (InnoDB) | MariaDB (InnoDB) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **B-Tree Leftmost Prefix** | Supported | Supported | Supported | Supported | Supported |
| **Partial Indexes (WHERE)** | Supported | Supported | Supported | Unsupported | Unsupported |
| **Expression / Functional** | Supported | Supported | Supported | Supported (8.0+) | Supported (10.2+) |
| **Auto Index Foreign Keys** | No | No | No | Yes (InnoDB) | Yes (InnoDB) |
| **Check Constraints Enforced**| Yes | Yes | Yes (3.3+) | Yes (8.0.16+) | Yes (10.2.1+) |
| **Included Columns (INCLUDE)**| Yes (11+) | Yes | Unsupported | Unsupported | Unsupported |
| **Null Ordering (NULLS FIRST)**| Supported | Supported | Supported (3.30+)| Unsupported | Unsupported |

## 2. Dialect Specific Rules
- In PostgreSQL and SQLite, foreign keys without leading-prefix indexes are flagged by `DERA-IDX-003`.
- In MySQL and MariaDB, `DERA-IDX-003` yields `NOT_APPLICABLE` because InnoDB enforces/creates child indexes automatically.
- Partial indexes require exact predicate string matching after canonical normalization.
