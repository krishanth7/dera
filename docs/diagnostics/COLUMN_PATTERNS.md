# Column Patterns & Nullability Diagnostics (DERA-MNT-002, DERA-MNT-008)

## Column Composition Analysis

DERA audits individual column declarations for composition patterns, storage characteristics, and potential data modeling anti-patterns:
- Nullable vs. non-nullable attributes.
- Default value expression presence.
- Generated and identity column declarations.
- Large Object (LOB) text and binary types (`TEXT`, `BLOB`, `BYTEA`, `CLOB`).

## High Column Nullability Ratio (DERA-MNT-002)

High proportions of nullable columns in a table often reflect optional polymorphic attributes, wide sparse tables, or incomplete entity normalization.

### Thresholds
- **Minimum Columns Evaluated** (`min_table_columns_for_nullability`): 5 columns. Tables with fewer columns are skipped to avoid false positives.
- **Baseline Nullability Ratio** (`max_nullability_ratio`, default: 0.50): Emits `INFORMATIONAL` finding.
- **Elevated Nullability Ratio** (`elevated_nullability_ratio`, default: 0.75): Emits `LOW` severity finding.

## LOB Column Concentration (DERA-MNT-008)

Relational database engines store large text and binary objects out-of-line (TOAST in PostgreSQL, Overflow pages in SQLite/InnoDB). Having multiple LOB columns on a single table increases row overhead, I/O amplification during table scans, and memory consumption during buffer pool reads.

### Thresholds
- **Baseline Concentration** (`max_lob_columns_per_table`, default: 4): Emits `INFORMATIONAL` finding.
- **Elevated Concentration** (`elevated_lob_columns_per_table`, default: 8): Emits `LOW` severity finding.

### Engine Applicability
- **PostgreSQL / Supabase**: Evaluates `text`, `bytea`, `json`, `jsonb`.
- **MySQL / MariaDB**: Evaluates `text`, `mediumtext`, `longtext`, `blob`, `mediumblob`, `longblob`.
- **SQLite**: Evaluates unbounded `text`, `blob`, `clob`.
