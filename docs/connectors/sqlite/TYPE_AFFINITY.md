# DERA SQLite Type Affinity Rules

## Overview

SQLite uses dynamic typing and type affinity rather than static, rigorous column data typing (unless `STRICT` mode is declared). DERA preserves both the original native declared type string and the derived SQLite Type Affinity (`packages/connectors/src/dera_connectors/sqlite/types.py`).

---

## The 5 Type Affinity Rules (SQLite 3 Specification Section 3.1)

Type affinity is determined from the declared column type according to the following precedence rules:

### Rule 1: INTEGER Affinity
If the declared type contains the string `"INT"` (case-insensitive):
- Assigned Affinity: `INTEGER`
- Examples: `INT`, `INTEGER`, `TINYINT`, `SMALLINT`, `MEDIUMINT`, `BIGINT`, `UNSIGNED BIG INT`, `INT2`, `POINT`

### Rule 2: TEXT Affinity
If the declared type contains any of `"CHAR"`, `"CLOB"`, or `"TEXT"`:
- Assigned Affinity: `TEXT`
- Examples: `CHARACTER(20)`, `VARCHAR(255)`, `VARYING CHARACTER(255)`, `NCHAR(55)`, `TEXT`, `CLOB`

### Rule 3: BLOB Affinity
If the declared type contains `"BLOB"` or no type is specified (e.g. untyped column):
- Assigned Affinity: `BLOB`
- Examples: `BLOB`, `NONE`, untyped `id`

### Rule 4: REAL Affinity
If the declared type contains any of `"REAL"`, `"FLOA"`, or `"DOUB"`:
- Assigned Affinity: `REAL`
- Examples: `REAL`, `FLOAT`, `DOUBLE`, `DOUBLE PRECISION`

### Rule 5: NUMERIC Affinity
Otherwise, the affinity is:
- Assigned Affinity: `NUMERIC`
- Examples: `NUMERIC`, `DECIMAL(10,5)`, `BOOLEAN`, `DATE`, `DATETIME`, `JSON`

---

## Preservation Invariants

- `ColumnInfo.data_type`: Preserves the declared type string (e.g. `VARCHAR(255)`).
- `ColumnInfo.engine_specific["affinity"]`: Stores the computed affinity (`INTEGER`, `TEXT`, `BLOB`, `REAL`, `NUMERIC`).
- SQLite types are never coerced or forced into PostgreSQL types.
