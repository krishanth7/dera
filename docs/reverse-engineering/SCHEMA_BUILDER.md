# Schema Builder Construction Pipeline (Phase 6.1)

## 1. Overview

`SchemaBuilder` provides a deterministic, secure, and resource-bounded construction pipeline that transforms input metadata into an immutable, registry-backed `SchemaRepresentation`.

```python
from dera.reverse_engineering.builder import SchemaBuilder, SchemaResourceLimits
```

---

## 2. Construction Pipeline

The construction pipeline follows 10 strict sequential stages:

```text
[1. Input & Contract Validation]
        │ Verify contract version is supported ('1.0.0').
        ▼
[2. Resource Bounds Pre-Check]
        │ Verify identifier lengths do not exceed max_identifier_length.
        ▼
[3. ObjectRegistry Initialization]
        │ Initialize registry with optional workspace_id scope.
        ▼
[4. Deterministic Collection Sorting]
        │ Sort namespaces, tables, columns, constraints, indexes, triggers, views.
        ▼
[5. Object Registration & Duplicate Detection]
        │ Register every object under its canonical ObjectId.
        │ Strictly raise DuplicateRegistrationError on collision.
        ▼
[6. Foreign Key Reference Resolution]
        │ Resolve referenced_table_id and establish ResolutionStatus.
        ▼
[7. Capability & Completeness Profiling]
        │ Assess supported, unsupported, and restricted catalog features.
        ▼
[8. Referential Integrity Validation]
        │ Verify parents, column existence, and foreign key endpoints.
        ▼
[9. Frozen Representation Finalization]
        │ Encapsulate immutable tuples and private backing structures.
        ▼
[10. Return Validated SchemaRepresentation]
```

---

## 3. Resource Limits Configuration

To prevent Denial-of-Service (DoS) and Out-Of-Memory (OOM) vulnerabilities from malicious or pathological database schemas, `SchemaBuilder` enforces configurable limits:

```python
class SchemaResourceLimits(BaseModel):
    max_total_objects: int = 100_000  # Maximum schema objects allowed
    max_nesting_depth: int = 10  # Maximum hierarchy tree depth
    max_identifier_length: int = 256  # Maximum chars for tables, columns, constraints
    max_definition_bytes: int = 1_000_000  # Maximum bytes for raw view/trigger SQL
    max_references: int = 50_000  # Maximum foreign key/typed references
```

Breaches trigger `SchemaResourceLimitError` immediately, preventing unbounded memory consumption.

---

## 4. Usage Examples

### From CanonicalDatabase
```python
schema = SchemaBuilder.from_canonical_database(
    database=canonical_db,
    workspace_id="ws_finance",
    strict_validation=True,
)
```

### From Universal Connector Report
```python
# Directly accepts Phase 5 DatabaseMetadataReport:
schema = SchemaBuilder.from_metadata(
    metadata_report=connector_report,
    workspace_id="ws_finance",
)
```

### Custom Resource Limits
```python
strict_limits = SchemaResourceLimits(
    max_total_objects=10_000,
    max_identifier_length=128,
)
schema = SchemaBuilder.from_canonical_database(
    database=canonical_db,
    limits=strict_limits,
)
```
