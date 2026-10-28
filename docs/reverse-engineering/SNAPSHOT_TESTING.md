# Snapshot Subsystem Testing & Verification

## 1. Test Suite Architecture

The Phase 6.5 test suite is organized under `tests/reverse_engineering/phase_6_5/`:

| Test Module | Coverage Description |
| :--- | :--- |
| `fixtures.py` | Deterministic synthetic schema generators (empty, single table, composite keys, unicode, cyclic). |
| `test_snapshot_models.py` | Pydantic v2 immutability, extra-field rejection, default values, and frozen attribute checks. |
| `test_snapshot_builder.py` | Pipeline construction, cross-phase metadata identity consistency checks, and error handling. |
| `test_canonicalization.py` | Table lexicographical sorting, column ordinal ordering preservation, composite key sequence preservation. |
| `test_fingerprints.py` | Format verification, sensitivity to structural modification, invariance to envelope metadata. |
| `test_identity.py` | Snapshot ID format regex (`^snap_[0-9a-f]{32}$`), cryptographic entropy, and ID validation. |
| `test_integrity.py` | Cryptographic integrity verification, tamper detection, fingerprint mismatch detection, unsupported version handling. |
| `test_serialization.py` | RFC 8785 canonical JSON formatting, lossless roundtrip, non-finite number rejection, Unicode unescaped preservation. |
| `test_storage.py` | In-memory and filesystem storage implementations, atomic writes, workspace isolation, immutability on write. |
| `test_retention.py` | Retention evaluation, max-count pruning, max-age expiration, protected tag preservation, unique fingerprint preservation. |
| `test_compatibility.py` | Version support validation, exact-byte identity vs. structural fingerprint equivalence checks. |
| `test_determinism.py` | Input table permutation invariance, byte-level reproducibility, fingerprint reproducibility. |
| `test_cross_engine.py` | Multi-engine snapshot capture (PostgreSQL, SQLite, MySQL, MariaDB) with native attribute preservation. |
| `test_security.py` | Path traversal blocking, credential leakage prevention, DoS resource limits on oversized payloads. |
| `test_performance.py` | Lifecycle latency benchmarks (build < 500ms, serialize < 200ms, verify < 100ms, storage < 50ms). |
| `test_cryptographic_vectors.py` | Exact SHA-256 byte-length and digest matching against reviewed reference vectors. |
| `test_integration.py` | End-to-end integration across all reverse engineering phases (6.1, 6.2, 6.3, 6.4, 6.5). |

---

## 2. Test Execution Command

To execute the Phase 6.5 test suite:
```powershell
.\.venv\Scripts\python.exe -m pytest tests/reverse_engineering/phase_6_5 -v
```
All 58 test cases pass deterministically in under 1.5 seconds.
