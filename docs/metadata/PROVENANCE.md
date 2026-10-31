# Provenance & Audit Model

**Subsystem:** `dera.metadata.provenance`  

---

## 1. Provenance Scope

Every normalized database object (databases, namespaces, tables, columns, constraints, indexes, views, and triggers) carries an immutable `MetadataProvenance` instance explaining its extraction history:

```python
class MetadataProvenance(BaseModel):
    source_engine: str  # e.g. "postgresql", "sqlite", "mysql"
    source_version: str | None  # e.g. "16.2", "3.45.0"
    connector_version: str  # e.g. "0.1.0-dev"
    collection_timestamp: datetime  # RFC 3339 UTC
    completeness: MetadataCompleteness  # COMPLETE, PARTIAL, RESTRICTED, UNSUPPORTED
    source_location: str | None  # e.g. "public.users.email"
    native_identifier: str  # Exact declared native name
    capability_status: str | None  # Capability diagnostic flag
```

---

## 2. Zero Credential Exposure

`MetadataProvenance` explicitly rejects database passwords, private keys, connection strings, or internal filesystem paths. Only sanitized, public-safe logical references are retained.
