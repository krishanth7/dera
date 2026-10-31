# Table Width Diagnostics (DERA-MNT-001)

## Overview

Excessive table width (the "wide table pattern") occurs when a single relational table declares an unusually large number of columns. While wide tables are legitimate in certain analytical contexts (e.g. denormalized marts, OLAP schemas), in OLTP environments they often indicate missing domain boundaries, row-size exhaustion risk, or polymorphic attribute anti-patterns.

## Thresholds and Evaluation Policy

Table width diagnostics evaluate column counts using configurable tiered thresholds:

- **Baseline Threshold** (`max_table_width`, default: 30 columns): Emits `INFORMATIONAL` finding.
- **Review Threshold** (`review_table_width`, default: 50 columns): Emits `LOW` severity finding for architectural review.
- **Elevated Threshold** (`elevated_table_width`, default: 100 columns): Emits `MEDIUM` severity finding indicating potential engine limits (e.g., PostgreSQL row size limits or SQLite `SQLITE_MAX_COLUMN`).

## Evidence Contract

Each finding produces structured `DiagnosticEvidence`:
- `object_id`: Table canonical ID.
- `field_name`: `"column_count"`.
- `observed_value`: Exact column count.
- `expected_value`: `"< {threshold}"`.
- `context_data`: Includes `table_name`, `namespace`, and configured threshold levels.

## Engineering Recommendations

1. Evaluate whether the entity consolidates multiple bounded contexts.
2. Consider vertical partitioning or decomposition into 1:1 extension tables.
3. Verify that wide tables do not approach engine page limits or performance degradation during row updates.
