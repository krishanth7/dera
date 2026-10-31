# Schema Complexity Diagnostics

## Definition and Intent

Schema complexity diagnostics measure aggregate structural volume and density across relational entities. Raw entity counts alone do not dictate design flaws; normalized ratios (such as average columns per table, constraint density, and foreign key fan-out) provide standardized engineering indicators for architectural complexity.

## Computed Complexity Metrics

The schema complexity engine computes the following metrics via `compute_schema_complexity`:

- `table_count`: Total declared relational tables.
- `view_count`: Total database views (standard and materialized where accessible).
- `column_count`: Cumulative column declarations across all tables.
- `constraint_count`: Total constraints (Primary Key, Foreign Key, Unique, Check).
- `index_count`: Total secondary indexes.
- `foreign_key_count`: Total foreign key dependencies.
- `namespace_count`: Distinct database namespaces / schemas.
- `avg_columns_per_table`: $\frac{\text{column\_count}}{\text{table\_count}}$
- `avg_constraints_per_table`: $\frac{\text{constraint\_count}}{\text{table\_count}}$

## Normalization Principles

1. **Size Independence**: Small schemas (e.g. 5 tables) with high constraint ratios are not penalized over large enterprise schemas (e.g. 500 tables) with clean modular decomposition.
2. **Deterministic Aggregation**: Object ordering in inputs does not alter summary statistics.
3. **Missing Metadata Handling**: Partial metadata representations report known object counts without extrapolating missing entities.
