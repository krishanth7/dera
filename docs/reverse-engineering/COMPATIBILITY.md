# Cross-Engine Compatibility & Capability Awareness (Phase 6.1)

## 1. Supported Database Engines

Phase 6.1 supports canonical schema representation across all Phase 5 database engines:

| Engine | Namespace Semantics | Key Native Features Represented |
|---|---|---|
| **PostgreSQL** | Multi-schema (`public`, custom schemas) | Composite PK/FKs, check constraints, partial/expression indexes, stored generated columns, views, triggers |
| **Supabase** | Multi-schema (`auth`, `public`, `storage`) | PostgreSQL schemas and extensions |
| **SQLite** | Single namespace (`main`, attached databases) | Type affinity, inline check constraints, AUTOINCREMENT primary keys, expression indexes |
| **MySQL** | Database name as schema namespace | Table comments, column comments, unsigned integer types, FK referential actions |
| **MariaDB** | Database name as schema namespace | Virtual & stored generated columns, CHECK constraints |

---

## 2. Capability Awareness & Completeness Tracking

Engines possess differing levels of catalog expressiveness. DERA avoids inventing fictional metadata for unsupported engine features. Instead, it classifies engine features using `CapabilityState` and tracks completeness using `MetadataCompleteness`:

```python
from dera.reverse_engineering.capabilities import (
    CapabilityState,
    SchemaCapabilityProfile,
    assess_schema_capabilities,
)
```

### Feature Capability States

- `SUPPORTED`: Natively supported by engine and successfully extracted.
- `UNSUPPORTED`: Not supported by the database engine (e.g. named check constraints or stored procedures in SQLite).
- `RESTRICTED`: Supported by engine, but inspection account lacked catalog permissions.
- `UNKNOWN`: Status could not be affirmatively determined.

### SchemaCapabilityProfile
```python
profile = schema.capability_profile
# profile.overall_completeness: COMPLETE, PARTIAL, RESTRICTED, or UNSUPPORTED
# profile.features: dict[str, CapabilityState]
# profile.has_restricted_metadata: bool
# profile.has_unsupported_features: bool
```
