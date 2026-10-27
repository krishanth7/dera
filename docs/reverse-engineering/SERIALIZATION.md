# Deterministic Serialization & Deserialization (Phase 6.1)

## 1. Overview

`dera.reverse_engineering.serialization` provides byte-level deterministic, canonical JSON serialization, SHA-256 fingerprint generation, and safe reconstruction of `SchemaRepresentation` instances.

```python
from dera.reverse_engineering.serialization import (
    serialize_schema_representation,
    compute_schema_hash,
    deserialize_schema_representation,
)
```

---

## 2. Serialization Guarantees

1. **Reuses Phase 5.5 Conventions**: Avoids competing serialization standards. Uses `_canonical_default_serializer` from `dera.metadata.serialization`.
2. **Deterministic UTF-8 Output**: Explicit UTF-8 encoding with `ensure_ascii=False` preserves Unicode table and column names across all alphabets.
3. **Sorted Keys**: Recursively sorts dictionary keys (`sort_keys=True`).
4. **Explicit Nulls**: Omits nothing implicitly; null values appear as explicit `null`.
5. **Zero Credentials**: Credentials, connection strings, and system paths are never serialized.

---

## 3. Safe Reconstruction (Deserialization)

Deserialization safely restores a `SchemaRepresentation` without arbitrary code execution:

```python
schema = deserialize_schema_representation(json_string, workspace_id="ws_finance")
```

### Safety Controls

- **No Pickle / No Eval**: Pure JSON parsing using standard library `json.loads`.
- **Contract Version Check**: Verifies `contract_version == "1.0.0"`; raises `UnsupportedSchemaContractError` on version mismatch.
- **Resource Bounds Enforcement**: Rejects oversized payloads exceeding `max_serialized_payload_bytes`.
- **Full Structural Re-Validation**: Runs through `SchemaBuilder` to repopulate `ObjectRegistry`, re-resolve foreign keys, and verify referential integrity.
