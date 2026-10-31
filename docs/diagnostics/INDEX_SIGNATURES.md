# DERA Index Signatures & Semantic Equivalence

## 1. Concept
Index equivalence cannot rely merely on column names. Two indexes with the same column names might have different access methods (e.g. BTREE vs HASH), sort orders (ASC vs DESC), null orderings, partial predicates, or operator classes.

## 2. CanonicalIndexSignature Data Structure
```python
@dataclass(frozen=True)
class CanonicalIndexSignature:
    parent_table_id: str
    index_type: str
    is_unique: bool
    terms: tuple[CanonicalIndexTermSignature, ...]
    predicate: str | None
```

## 3. Cryptographic Fingerprint
The signature produces a SHA-256 hash across canonical JSON-serialized attributes:
- `table_id`: Owning table canonical ID
- `type`: Lowercase index method (e.g. `btree`)
- `unique`: Boolean uniqueness
- `terms`: Normalized sequence of terms (column/expression, ordinal, ASC/DESC, NULLS FIRST/LAST)
- `predicate`: Whitespace-trimmed, lowercase SQL predicate or None
