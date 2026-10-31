# DERA-IDX-003: Foreign Key Supporting Index Coverage

## 1. Specification
Rule `DERA-IDX-003` audits child tables for foreign key constraints that lack a supporting index on their referencing columns in database engines that do not automatically create them.

## 2. Engine-Specific Behavior
- **PostgreSQL & SQLite**: Neither engine automatically creates an index on child referencing columns when a `FOREIGN KEY` is declared. Without an index with the foreign key columns as a leading prefix, updates or deletes to the parent table trigger full table scans on the child table, causing lock contention and query degradation.
- **MySQL & MariaDB (InnoDB)**: The InnoDB storage engine automatically requires and generates a supporting index on foreign key child columns if an appropriate one does not already exist. Therefore, rule `DERA-IDX-003` returns `EvaluationStatus.NOT_APPLICABLE` for MySQL and MariaDB to prevent false positives.

## 3. Leading Prefix Rule
An index `I` supports foreign key `FK` if and only if:
1. `I.columns[:len(FK.columns)] == FK.columns` (exact ordinal match of leading columns).
2. `I.predicate is None` (partial indexes are excluded from full coverage guarantee).
