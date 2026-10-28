# Phase 6.5 Schema Snapshots & Deterministic Fingerprints Overview

## 1. Executive Summary

Milestone 6.5 of the DERA Reverse Engineering Core Engine introduces the **Schema Snapshot & Deterministic Fingerprint Subsystem** (`dera.reverse_engineering.snapshots`).

This subsystem captures canonical, immutable, strongly typed structural representations of database schemas and produces deterministic, content-based cryptographic SHA-256 fingerprints with domain separation.

```text
Phase 5 Canonical Metadata
          │
          ▼
Phase 6.1 Schema Representation
          │
          ▼
Phase 6.2 Structural Reconstruction
          │
          ▼
Phase 6.3 Foreign Key Relationship Graph
          │
          ▼
Phase 6.4 Dependency Analysis & Cycle Detection
          │
          ▼
Phase 6.5 Schema Snapshot Builder
    ├── Immutable Structural Payload
    ├── Canonical RFC 8785 Serialization
    ├── SHA-256 Fingerprint (Domain: DERA:SCHEMA:STRUCTURAL:V1)
    ├── Operational Envelope & Provenance
    ├── Metadata Completeness Preservation
    ├── Cryptographic Integrity Verification
    └── Secure Workspace-Isolated Storage
          │
          ▼
Versioned Schema Snapshot (`dera.schema.snapshot.v1`)
```

---

## 2. Core Non-Negotiable Tenets

1. **Deterministic Fingerprints**: Equivalent canonical structural schema content produces identical SHA-256 fingerprints under the same fingerprint contract version, regardless of capture time or platform.
2. **Payload vs. Envelope Separation**: Volatile operational metadata (capture timestamps, requester identities, workspace IDs, storage paths) are strictly isolated in the snapshot envelope and excluded from the structural fingerprint.
3. **Snapshot Immutability**: All snapshot domain models (`SchemaSnapshot`, `SnapshotStructuralPayload`, `SnapshotTablePayload`, etc.) are frozen Pydantic v2 models (`extra="forbid"`, `frozen=True`). Storage backends prevent silent overwriting of existing records.
4. **Stable Identity Separation**: DERA strictly distinguishes Snapshot Record Identity (`snap_<hex32>`), Database Identity, and Structural Content Fingerprint (`sha256:<hex64>`).
5. **Cryptographic Domain Separation**: Structural fingerprints use SHA-256 prefixed with the explicit domain separator `DERA:SCHEMA:STRUCTURAL:V1\n`.
6. **RFC 8785 Canonical JSON**: Byte-level deterministic serialization enforces lexicographical key sorting, compact delimiters (`,`, `:`), UTF-8 encoding with unescaped Unicode, RFC 3339 UTC timestamps (`Z`), and strict rejection of non-finite numbers (`NaN`, `Infinity`).
7. **Completeness-Awareness**: Metadata completeness (`COMPLETE`, `PARTIAL`, `RESTRICTED`, `UNSUPPORTED`, `UNKNOWN`) is preserved in the structural payload and bound to the fingerprint.
8. **Multi-Engine Semantics**: Canonical structures preserve native engine types and attributes across PostgreSQL, SQLite, MySQL, and MariaDB.
9. **Zero Database Mutations**: Snapshots are generated in-memory from passive metadata collectors. Zero customer database mutations or arbitrary SQL commands are executed.
10. **Zero AI/ML Dependencies**: 100% deterministic, cryptographic, reproducible algorithms without LLMs or machine learning heuristics.

---

## 3. Package Structure

The Phase 6.5 subsystem is located at `packages/core/src/dera/reverse_engineering/snapshots/`:

| Module | Description |
| :--- | :--- |
| `models.py` | Strongly typed Pydantic v2 frozen models (`SchemaSnapshot`, `SnapshotStructuralPayload`, `SnapshotEnvelope`, `SnapshotTablePayload`, etc.). |
| `builder.py` | Deterministic `SchemaSnapshotBuilder` validating cross-phase inputs and constructing verified snapshots. |
| `canonicalization.py` | Normalizes structural tables, columns, constraints, indexes, views, and graph summaries into canonical orderings. |
| `serialization.py` | RFC 8785 canonical JSON serializer and safe deserializer enforcing resource limits. |
| `fingerprints.py` | Cryptographic SHA-256 fingerprint generation with domain separation. |
| `identity.py` | Stable snapshot identifier generation (`snap_<hex32>`) and validation. |
| `validation.py` | Structural validation, referential integrity verification, and limit enforcement. |
| `integrity.py` | Cryptographic integrity verification (`verify_snapshot_integrity`) detecting tampering or corruption. |
| `compatibility.py` | Snapshot format version checks and equivalence level evaluations (`EXACT_BYTE_IDENTICAL`, `STRUCTURAL_FINGERPRINT_MATCH`, `NONE`). |
| `provenance.py` | Engine source provenance, connector version, and collection consistency records. |
| `limits.py` | Algorithmic resource limits (`SnapshotResourceLimits`) guarding against payload DoS. |
| `storage.py` | Abstract `SnapshotStorage` contract and filtering criteria (`SnapshotFilter`). |
| `repository.py` | In-memory and atomic filesystem storage implementations with tenant isolation and deduplication. |
| `retention.py` | Retention policies (`SnapshotRetentionPolicy`) and execution manager (`RetentionManager`). |
| `errors.py` | Comprehensive typed exception hierarchy (`SnapshotError`, `SnapshotValidationError`, `SnapshotIntegrityError`, etc.). |

---

## 4. Phase 6.5 vs. Phase 9 Boundary

Phase 6.5 focuses strictly on capturing validated canonical schema structures, computing deterministic fingerprints, verifying integrity, and managing immutable storage.

Phase 6.5 provides snapshot equality checks (`is_equivalent_to`). Object-level schema diffing, breaking change classification, migration path planning, and DDL generation are strictly reserved for Phase 9.
