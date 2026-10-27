# Metadata Testing & Golden Files

**Subsystem:** `tests/metadata/`  

---

## 1. Test Suite Structure

```text
tests/metadata/
├── unit/
│   ├── test_identifiers.py       # Quoting, unquoting, case-folding across dialects
│   ├── test_ordering.py          # Deterministic multi-key sorting
│   ├── test_capabilities.py      # Completeness mapping
│   └── test_serialization.py   # Byte-level JSON and hash stability
├── identity/
│   └── test_object_identity.py   # Collision resistance, length framing, determinism
├── contracts/
│   └── test_canonical_contracts.py # Model immutability, contract v1.0.0
├── cross_engine/
│   ├── test_type_normalization.py  # Cross-dialect type mapping matrix
│   └── test_cross_engine_normalization.py # End-to-end multi-engine normalization
├── security/
│   └── test_security_bounds.py   # Payload limits, duplicate detection, reference checks
├── integration/
│   └── test_connector_integration.py # Ingestion of Phase 5 connector models
└── golden/
    └── test_golden_files.py      # Byte-level golden output verification
```

---

## 2. Running Tests

```bash
# Execute full metadata test suite
python -m unittest discover tests/metadata

# Execute specific cross-engine test
python -m unittest tests/metadata/cross_engine/test_cross_engine_normalization.py
```
