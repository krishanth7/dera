# Determinism & Reproducibility (Phase 6.1)

## 1. Overview

DERA is a deterministic database engineering platform. A foundational requirement of Phase 6.1 is that **identical input metadata produces byte-for-byte identical output schema representations and cryptographic hashes**, regardless of:
- Catalog query return order
- Python dictionary hash seeds
- Shuffled input collections
- Operating system or hardware environment

---

## 2. Deterministic Ordering Algorithms

The module `dera.reverse_engineering.ordering` establishes canonical sorting algorithms:

```python
from dera.reverse_engineering.ordering import (
    sort_namespaces,
    sort_tables,
    sort_columns,
    sort_constraints,
    sort_indexes,
    sort_foreign_keys,
    sort_triggers,
    sort_views,
    sort_references,
    sort_foreign_key_references,
)
```

### Sorting Rules

- **Namespaces**: `(ns.name.lower(), ns.name)`
- **Tables**: `(tbl.name.lower(), tbl.name)`
- **Columns**: `(col.ordinal_position, col.name.lower(), col.name)`
- **Constraints**: `(c.name.lower(), c.name, tuple(col.lower() for col in c.columns))`
- **Foreign Keys**: `(fk.name.lower(), fk.name, fk.referenced_table_name.lower(), tuple(col.lower() for col in fk.source_columns))`
- **Indexes**: `(0 if idx.is_primary else 1, 0 if idx.is_unique else 1, idx.name.lower(), idx.name)`
- **Triggers & Views**: `(item.name.lower(), item.name)`
- **Foreign Key References**: `(fk.foreign_key_name.lower(), fk.foreign_key_name, fk.source_table_name.lower(), fk.referenced_table_name.lower(), fk.foreign_key_id)`

---

## 3. Cryptographic Fingerprinting

```python
schema_hash = schema.compute_hash()
# Example output: 'a7f34c9182390a12e3409d...' (64 hex characters)
```

### Hash Computation Properties

1. **Normalized Input**: Internal models are sorted and normalized before hashing. Shuffled inputs yield identical digests.
2. **Whitespace Invariance**: Compact JSON serialization (`indent=None, separators=(',', ':')`) eliminates formatting whitespace variations.
3. **Sorted Keys**: Every JSON level is serialized with `sort_keys=True`.
4. **Excludes Non-Deterministic Runtime Telemetry**: Elapsed construction time (`build_duration_ms`) is held in a private attribute and excluded from the serialized dictionary and hash digest.
5. **Deterministic Timestamp Format**: All datetimes are formatted using ISO 8601 UTC with explicit `'Z'`.
