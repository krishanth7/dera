# Canonical Type Normalization

**Subsystem:** `dera.metadata.adapters`  
**Taxonomy:** `CanonicalTypeCategory`  

---

## 1. Canonical Type Taxonomy

DERA defines a deterministic 17-category type taxonomy for high-level schema classification:

```text
INTEGER    DECIMAL    FLOAT      BOOLEAN    TEXT       BINARY
DATE       TIME       TIMESTAMP  JSON       UUID       ENUM
SET        ARRAY      SPATIAL    OTHER      UNKNOWN
```

---

## 2. Cross-Dialect Mapping Matrix

| Canonical Category | PostgreSQL | SQLite | MySQL / MariaDB |
| :--- | :--- | :--- | :--- |
| **INTEGER** | `smallint`, `int`, `bigint`, `serial` | Declared type contains `INT` | `tinyint`, `smallint`, `int`, `bigint` |
| **DECIMAL** | `numeric`, `decimal` | Contains `NUMERIC`, `DECIMAL` | `decimal`, `numeric`, `fixed` |
| **FLOAT** | `real`, `double precision` | Contains `REAL`, `FLOA`, `DOUB` | `float`, `double` |
| **BOOLEAN** | `boolean`, `bool` | Contains `BOOL` | `tinyint(1)`, `boolean` |
| **TEXT** | `varchar`, `char`, `text`, `citext` | Contains `CHAR`, `CLOB`, `TEXT` | `varchar`, `char`, `text`, `longtext` |
| **BINARY** | `bytea`, `bit` | Contains `BLOB` | `binary`, `varbinary`, `blob` |
| **DATE** | `date` | Contains `DATE` | `date`, `year` |
| **TIME** | `time`, `timetz` | Contains `TIME` | `time` |
| **TIMESTAMP** | `timestamp`, `timestamptz` | Contains `TIMESTAMP` | `datetime`, `timestamp` |
| **JSON** | `json`, `jsonb` | Contains `JSON` | `json` |
| **UUID** | `uuid` | Contains `UUID` | `char(36)` / `uuid` |
| **ENUM** | User-defined enum types | N/A (CHECK constraint) | `enum('val1', 'val2')` |
| **SET** | N/A | N/A | `set('a', 'b')` |
| **ARRAY** | Native array (`type[]`) | N/A (JSON) | N/A (JSON) |
| **SPATIAL** | `geometry`, `geography` | N/A | `point`, `polygon`, `geometry` |
