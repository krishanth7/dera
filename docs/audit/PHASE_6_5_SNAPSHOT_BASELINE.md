# Phase 6.5 Baseline Audit: Schema Snapshots & Deterministic Fingerprints

**Project:** DERA — Database Engineering & Reverse Analysis  
**Repository:** [https://github.com/krishanth7/dera](https://github.com/krishanth7/dera)  
**Milestone:** Phase 6.5 — Schema Snapshots & Deterministic Fingerprints  
**Base Commit SHA:** `5b665c86cae22f05505dabc17bd6d8fd1c14b591`  
**Head Branch:** `feat/phase-6.5-schema-snapshots`  
**Date:** October 28, 2026  
**Auditor:** Principal Database Reverse Engineering Architect & Engineering Team  
**Audit Status:** Verified Complete Baseline  

---

## 1. Executive Summary & Objectives

Phase 6.5 delivers the **Production Schema Snapshot & Deterministic Fingerprint Engine** (`packages/core/src/dera/reverse_engineering/snapshots/`) for DERA. Built upon the verified foundation of Phases 6.1 through 6.4, Phase 6.5 captures immutable, canonical structural representations of database schemas and produces deterministic, content-based cryptographic fingerprints (SHA-256) with domain separation.

### Primary Objectives

1. **Canonical Schema Snapshot Contract (`SchemaSnapshot`)**:
   - Strongly typed, immutable Pydantic v2 domain model (`dera.schema.snapshot.v1`) encapsulating structural payload, cryptographic fingerprint, metadata completeness, capture envelope, and source provenance.
2. **Strict Separation of Structural Payload vs. Snapshot Envelope**:
   - **Structural Payload (`SnapshotStructuralPayload`)**: Contains schema-defining attributes (namespaces, tables, columns, data types, constraints, indexes, views, triggers, relationships, dependencies).
   - **Snapshot Envelope (`SnapshotEnvelope`)**: Contains volatile operational metadata (snapshot ID, workspace ID, capture timestamp, source reference, tags, validation status). Volatile metadata is strictly excluded from the structural fingerprint.
3. **Deterministic RFC 8785 Canonical JSON Serialization**:
   - Byte-level deterministic serialization with lexicographical key sorting, compact delimiters (`","` and `":"`), UTF-8 encoding, deterministic numeric representations, and explicit null values.
4. **Cryptographic Fingerprinting with Domain Separation**:
   - SHA-256 structural fingerprinting bound to domain identifier `DERA:SCHEMA:STRUCTURAL:V1` and algorithm version `dera.fingerprint.v1`.
   - Invariant across captures at different timestamps or execution environments when structural schema content is identical.
5. **Deterministic Ordering Across Collections**:
   - Strictly ordered namespaces, tables (by namespace and name), columns (preserving semantic ordinal position), constraints (by type, name, columns), indexes, views, triggers, relationship edges, and dependency components.
6. **Integrity Verification Subsystem (`verify_snapshot_integrity`)**:
   - Independent verification engine that re-computes the structural digest from the canonical payload and flags `VALID`, `MISMATCH`, `UNSUPPORTED_VERSION`, or `INVALID_PAYLOAD`.
7. **Storage Abstraction & Multi-Engine Persistence**:
   - Pluggable `SnapshotStorage` interface with workspace isolation, safe atomic writes, and path traversal prevention (`InMemorySnapshotStorage`, `FileSystemSnapshotStorage`).
8. **Retention Management (`SnapshotRetentionPolicy`, `RetentionManager`)**:
   - Rule-based retention controls enforcing maximum snapshot count, maximum age, protected tags, and distinct fingerprint preservation.
9. **Version Compatibility & Equivalence Semantics**:
   - Explicit distinction between byte-identical payloads, structural fingerprint equality, and semantic schema equivalence.
10. **Zero AI/ML & Zero Database Mutation Policy**:
    - Strictly zero machine-learning or probabilistic models; purely in-memory, deterministic algorithms; zero customer database mutations.

---

## 2. Prerequisites Verification

All prerequisite milestones have been thoroughly audited and verified on commit `5b665c86cae22f05505dabc17bd6d8fd1c14b591`:

| Prerequisite Subsystem | Status | Verification Detail |
| :--- | :--- | :--- |
| **Phase 5.5 Canonical Metadata & Identity** | **PASS** | Stable length-prefixed SHA-256 `ObjectId` computation, canonical types, and serialization in `dera.metadata`. |
| **Phase 5.6 Connector Safety & Guardrails** | **PASS** | SSRF prevention, IP validation, resource bounds, query timeout enforcement. |
| **Phase 6.1 Canonical Schema Representation** | **PASS** | `SchemaRepresentation`, `ObjectRegistry`, `TypedRef`, `SchemaHierarchy`, deterministic serialization in `dera.reverse_engineering`. |
| **Phase 6.2 Structural Reconstruction** | **PASS** | `StructuralReconstructionResult`, `ReconstructedTable`, `ReconstructedColumn`, constraint reconstruction. |
| **Phase 6.3 Foreign Key Relationship Graph** | **PASS** | `ForeignKeyGraph`, `TableNode`, `ForeignKeyEdge`, directed multigraph traversal, WCC discovery. |
| **Phase 6.4 Dependency Analysis & Cycle Detection** | **PASS** | `DependencyAnalysisResult`, Tarjan SCC decomposition, Johnson cycle enumeration, breakability analysis, topological ordering, condensation DAG. |

---

## 3. Existing Reusable Contracts & Capabilities

The following verified components in `packages/core/src/dera/` are directly reused in Phase 6.5:

1. **`ObjectId` & Identity Machinery** (`dera.metadata.identity`):
   - Canonical identifiers for databases, namespaces, tables, columns, constraints, indexes, views, triggers.
2. **Metadata Enums & Normalization** (`dera.metadata.enums`):
   - `MetadataCompleteness`, `CanonicalTypeCategory`, `TableType`, `ConstraintType`, `ForeignKeyAction`.
3. **Serialization Conventions** (`dera.metadata.serialization`, `dera.reverse_engineering.serialization`):
   - `_canonical_default_serializer`, compact JSON formatting conventions, RFC 8785 compliance patterns.
4. **Core Domain Models** (`dera.reverse_engineering.schema`, `dera.reverse_engineering.graph.models`, `dera.reverse_engineering.dependencies.models`):
   - Full structural hierarchy to assemble snapshot payloads without duplicate extraction logic.

---

## 4. Gap Analysis

Prior to Phase 6.5, DERA lacked:
1. A unified, immutable snapshot envelope separating volatile operational capture metadata from structural schema definitions.
2. An explicit domain-separated cryptographic fingerprinting contract (`DERA:SCHEMA:STRUCTURAL:V1`).
3. An integrity verification service to validate snapshots against corruption or tampering.
4. A safe, multi-engine persistence interface with workspace isolation and retention lifecycle management.
5. Systematic determinism and cross-engine golden snapshots across PostgreSQL, SQLite, MySQL, and MariaDB.

---

## 5. Security & Safety Risks

| Security Risk | Severity | Mitigation Strategy |
| :--- | :--- | :--- |
| **Credential Exposure** | Critical | Structural payload and envelope strictly prohibit credentials, passwords, or connection strings. |
| **Cross-Tenant Storage Access** | High | Storage interface strictly enforces `workspace_id` scoping on all operations; cross-workspace lookups return null/unauthorized. |
| **Path Traversal on Storage** | High | Storage paths are sanitized, normalized, and validated to prevent directory traversal (`../`). |
| **Denial of Service (DoS) via Oversized Payloads** | High | Strict resource limits: `max_snapshot_size_bytes` (50MB), `max_object_count` (100k), `max_nesting_depth` (32), `max_serialized_bytes`. |
| **Hash Collision / Domain Cross-Use** | Medium | Domain separation prefix `DERA:SCHEMA:STRUCTURAL:V1` prepended to payload bytes prior to SHA-256 hashing. |
| **Arbitrary Deserialization Attacks** | High | Safe JSON deserialization with Pydantic type validation; no `pickle`, `eval`, or executable code deserialization. |

---

## 6. Implementation Plan & Execution Sequence

1. **Snapshot Contracts & Domain Models** (`packages/core/src/dera/reverse_engineering/snapshots/models.py`)
2. **Resource Limits & Error Handling** (`limits.py`, `errors.py`)
3. **Identity & Provenance** (`identity.py`, `provenance.py`)
4. **Canonicalization Engine** (`canonicalization.py`)
5. **Deterministic RFC 8785 Serialization** (`serialization.py`)
6. **SHA-256 Fingerprinting with Domain Separation** (`fingerprints.py`)
7. **Integrity Verification Subsystem** (`integrity.py`)
8. **Snapshot Builder & Cross-Phase Validator** (`builder.py`, `validation.py`, `compatibility.py`)
9. **Storage Abstractions & Implementations** (`storage.py`, `repository.py`)
10. **Retention Engine** (`retention.py`)
11. **Comprehensive Test Suite** (`tests/reverse_engineering/phase_6_5/`):
    - Unit tests, determinism tests, cryptographic test vectors, property-based tests, cross-engine tests, storage tests, retention tests, security tests, integration tests, performance benchmarks, and golden file tests.
12. **Technical Documentation & Acceptance Audit**:
    - 15 dedicated architecture and specification documents under `docs/reverse-engineering/`.
    - Final acceptance audit in `docs/audit/PHASE_6_5_SNAPSHOT_ACCEPTANCE.md`.
