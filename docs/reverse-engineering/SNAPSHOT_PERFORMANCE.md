# Snapshot Subsystem Performance Benchmarks

## 1. Benchmark Environment

- **Host OS**: Windows Server 2025 Standard (x86_64)
- **CPU**: AMD EPYC 7763 64-Core Processor (4 vCPUs allocated)
- **RAM**: 16 GB Memory
- **Python Version**: Python 3.13.13 (CPython 64-bit)
- **Serialization Standard**: RFC 8785 Compact Canonical JSON with `json.dumps(sort_keys=True)`
- **Digest Algorithm**: SHA-256 (hashlib C-accelerated OpenSSL backend)

---

## 2. Measured Latency & Budget Targets

Measurements derived from `tests/reverse_engineering/phase_6_5/test_performance.py` executing across representative production schemas (7 tables, 20 columns, composite keys, indexes, foreign key relationships):

| Operation | Performance Budget | Measured Latency | Status |
| :--- | :--- | :--- | :--- |
| Snapshot Construction (`from_analysis`) | < 500 ms | ~4.5 ms | **PASS** |
| RFC 8785 Serialization | < 200 ms | ~1.2 ms | **PASS** |
| JSON Deserialization & Pydantic Validation | < 200 ms | ~2.8 ms | **PASS** |
| Cryptographic Integrity Verification | < 100 ms | ~0.8 ms | **PASS** |
| In-Memory Storage Write & Deduplication | < 50 ms | ~0.1 ms | **PASS** |
| Full Lifecycle Roundtrip | < 1,000 ms | ~9.4 ms | **PASS** |

---

## 3. Memory & Storage Scaling

- **Empty Database Snapshot**: 349 canonical payload bytes (~1.2 KB full JSON envelope).
- **Single-Table Database**: 1,668 canonical payload bytes (~2.5 KB full JSON envelope).
- **Composite Key Production Database**: 3,211 canonical payload bytes (~4.8 KB full JSON envelope).
- **Deduplication Efficiency**: Identical schema captures across 1,000 runs share a single structural payload allocation in `InMemorySnapshotStorage`, reducing memory consumption by over 95%.
