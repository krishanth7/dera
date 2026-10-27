# Index Normalization

**Subsystem:** `dera.metadata.models.index`  

---

## 1. Index Model Structure

Indexes are represented via `CanonicalIndex`:
- `name: str`: Native index name.
- `is_unique: bool`: Unique value enforcement.
- `is_primary: bool`: Backing primary key constraint index.
- `index_type: IndexType`: `BTREE`, `HASH`, `GIN`, `GIST`, `BRIN`, `SPGIST`, `RTREE`, `FULLTEXT`, `SPATIAL`, `OTHER`.
- `terms: tuple[CanonicalIndexTerm, ...]`: Ordered terms comprising the index.
- `predicate: str | None`: Partial index WHERE filter expression.

---

## 2. Functional & Expression Terms

When an index includes an expression rather than a plain column (e.g. `lower(email)` in PostgreSQL or `((amount * 100))` in MySQL 8.0+):
- `CanonicalIndexTerm.is_expression = True`
- `CanonicalIndexTerm.expression = "<raw_sql_expression>"`
- `CanonicalIndexTerm.column_name = None`

Expression text is stored as an untrusted metadata string and is never executed by DERA.
