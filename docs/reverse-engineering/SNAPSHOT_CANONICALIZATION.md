# Schema Snapshot Canonicalization Specification

## 1. Objective

Canonicalization transforms arbitrary in-memory schema objects into a strictly deterministic, reproducible form before serialization and fingerprint hashing.

Any two schema representations containing identical structural elements—regardless of extraction order, query execution sequence, or internal dictionary hash seed—must yield byte-identical canonical payloads.

---

## 2. Canonical Ordering Rules

### 2.1 Table Ordering
Tables are sorted lexicographically by:
1. `namespace` (schema name, ascending)
2. `name` (native table name, ascending)

### 2.2 Column Ordering
Columns in a table are **not** sorted alphabetically, because column ordinal position is semantically significant in relational databases (affecting `SELECT *`, positional inserts, tuple definitions, and foreign key mappings).
Columns are sorted strictly by:
1. `ordinal_position` (1-indexed ascending integer)

### 2.3 Constraint Ordering
- **Primary Key**: Exactly one or none per table. Composite column sequences preserve key declaration order.
- **Foreign Keys**: Sorted by `name` (ascending).
- **Unique Constraints**: Sorted by `name` (ascending). Composite column sequences preserve declaration order.
- **Check Constraints**: Sorted by `name` (ascending).

### 2.4 Index Ordering
Indexes are sorted by:
1. `name` (ascending)
Composite index column sequences preserve index declaration order.

### 2.5 Views & Triggers
- **Views**: Sorted by `namespace` (ascending), then `name` (ascending).
- **Triggers**: Sorted by `table_name` (ascending), then `name` (ascending).

### 2.6 Relationship & Dependency Ordering
- **Relationships**: Sorted by `source_table_id`, then `target_table_id`, then `constraint_name`.
- **Dependencies**: Summarized deterministically into scalar counts and cycle metrics.

---

## 3. Numeric & Primitive Canonicalization

To ensure platform-independent serialization across operating systems (Windows, Linux, macOS) and architectures (x86_64, ARM64):
1. **Integers**: Represented as standard base-10 integers without exponent notations.
2. **Booleans**: Represented strictly as `true` or `false`.
3. **Nulls**: Explicitly represented as `null`. Missing keys are prohibited in structural payloads.
4. **Non-finite Floats**: `NaN`, `Infinity`, and `-Infinity` are strictly prohibited and rejected with `SnapshotSerializationError`.

---

## 4. Unicode Handling & Identifier Semantics

DERA preserves database identifiers exactly as declared by the source engine:
- No case-folding or lowercase normalization is applied during snapshot canonicalization. PostgreSQL case-sensitive quoted identifiers (`"UserData"` vs `"userdata"`) remain distinct.
- Unescaped UTF-8 characters are preserved without `\uXXXX` escaping (RFC 8785 Section 3.2.2.2).
- Normalized Unicode byte sequences guarantee cross-platform reproducibility.
