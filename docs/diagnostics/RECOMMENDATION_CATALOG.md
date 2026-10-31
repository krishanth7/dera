# Recommendation Catalog

## Catalog Overview

The Recommendation Catalog provides versioned (`RECOMMENDATION_CATALOG_VERSION = "1.0.0"`), peer-reviewed templates for all diagnostic rules across Phases 8.1–8.4.

## Catalog Entries

### Index Recommendations

#### `REC-IDX-001`: Redundant Index Removal
- **Applicable Rules**: `DERA-IDX-001`, `DERA-IDX-002`
- **Action**: Review duplicate or redundant secondary indexes with engineering teams. Confirm via production query execution plans (`pg_stat_user_indexes` or engine equivalents) that the index is not relied upon for unique enforcement or foreign key cascading before dropping.
- **Risks**: Unintended query regressions if optimizer relies on index statistics or edge-case query hints.
- **Verification**: Run `EXPLAIN ANALYZE` on critical queries before and after disabling the index.

#### `REC-IDX-002`: Missing Foreign Key Index
- **Applicable Rules**: `DERA-IDX-003`
- **Action**: Assess workload query patterns on the child table. If JOINs or parent table row deletions frequently filter by foreign key columns, create a supporting index on the leading foreign key columns.
- **Risks**: Additional write overhead on frequent INSERT/UPDATE workloads.
- **Verification**: Verify join performance improvements in staging environments.

### Constraint Recommendations

#### `REC-CON-001`: Primary Key Integrity
- **Applicable Rules**: `DERA-CON-001`
- **Action**: Correct primary key column definitions to disallow nullable columns. Define non-nullable constraints and verify unique non-null values.
- **Risks**: Table rewrite locks during column constraint modifications.
- **Verification**: Execute `SELECT COUNT(*) FROM table WHERE col IS NULL;` before applying `NOT NULL`.

### Maintainability Recommendations

#### `REC-MAINT-001`: Wide Table Decomposition
- **Applicable Rules**: `DERA-MAINT-001`
- **Action**: Review table column responsibilities. Separate rarely accessed large columns (e.g., text blobs, JSON payloads) into one-to-one extension tables or vertical partitions.
- **Risks**: Migration complexity and additional JOIN overhead if poorly split.
- **Verification**: Profile I/O and query projection width across dominant query paths.

#### `REC-MAINT-003`: Naming Standardization
- **Applicable Rules**: `DERA-MAINT-003`
- **Action**: Align table and column identifiers with agreed organization naming conventions (e.g., snake_case). Use view aliases or migration deprecation periods to prevent breaking API consumers.
- **Risks**: Downstream application or ORM query breakage.
- **Verification**: Audit codebase references before applying renames.
