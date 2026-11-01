# DERA Phase 9.1 — Schema Snapshot Comparison Baseline Audit

**Project:** DERA — Database Engineering & Reverse Analysis  
**Tagline:** Understand Every Schema. Engineer Every Change.  
**Repository:** [https://github.com/krishanth7/dera](https://github.com/krishanth7/dera)  
**Phase:** 9 — Schema Comparison & Migration Engineering  
**Milestone:** 9.1 — Deterministic Schema Snapshot Comparison Engine  
**Branch:** `feat/phase-9.1-schema-snapshot-comparison`  
**Base Commit SHA:** `c213d259647df1da2be126434a07abc6f2b6a175`  
**Date:** November 1, 2026  
**Auditor:** Principal Database Architect, Senior Python Engineer, Database Reverse-Engineering Specialist  

---

## 1. Executive Summary & Prerequisite Gate

Before designing and implementing Phase 9.1, a full repository audit was conducted against `c213d259647df1da2be126434a07abc6f2b6a175`.

### Prerequisite Audit Findings
- `docs/audit/PHASE_1_8_FINAL_COMPLETION_REPORT.md` exists and certifies 100.0% completion of Phases 1 through 8 across all 48 milestones.
- Repository test execution via `.venv\Scripts\python -m pytest -q` was run directly:
  - **1064 passed, 2 skipped, 407 subtests passed** in 109.36s.
  - Zero test failures across backend, connectors, reverse engineering, graph, diagnostics, and security suites.
- **Phase 5 Connector Contracts:** Verified pluggable connector protocol and read-only AST/catalog isolation for PostgreSQL, Supabase, SQLite, MySQL, and MariaDB.
- **Phase 6 Canonical Schema & Snapshots:** Verified `SchemaSnapshot`, `SnapshotStructuralPayload`, `SnapshotEnvelope`, `ObjectId` identity derivation, RFC 8785 canonical JSON formatting, and SHA-256 structural fingerprinting (`DERA:SCHEMA:STRUCTURAL:V1`).
- **Phase 8 Diagnostics Contracts:** Verified deterministic rule execution, typed diagnostic evidence, priority scoring, and unified reporting contracts.
- **Zero AI/LLM/ML Invariant:** Confirmed. The entire stack operates on static analysis, deterministic graph algorithms (Tarjan SCC, Johnson, Kahn), and rule evaluations. Zero heuristic or generative inference is present.

**Prerequisite Gate Verdict:** **PASS — FULLY QUALIFIED FOR PHASE 9.1**

---

## 2. Baseline Architecture Specifications

| Dimension | Repository Baseline Specification |
| :--- | :--- |
| **Base Commit SHA** | `c213d259647df1da2be126434a07abc6f2b6a175` |
| **Canonical Model Version** | `SNAPSHOT_FORMAT_VERSION = "dera.schema.snapshot.v1"`, `schema_format = "dera.structural.v1"` |
| **Snapshot Contract Version** | `FINGERPRINT_CONTRACT_VERSION = "dera.fingerprint.v1"` |
| **Fingerprint Algorithm** | `SHA-256`, domain prefix `DERA:SCHEMA:STRUCTURAL:V1\n` over canonical payload bytes |
| **Object Identity Rules** | Length-prefixed SHA-256 digest: `dera:{kind}:{hash24}` via `compute_stable_object_id` |
| **Engine Capabilities** | Supported: `postgresql`, `supabase`, `sqlite`, `mysql`, `mariadb` |
| **Serialization Rules** | RFC 8785 canonical JSON, deterministic keys, UTF-8 encoded, float/int/bool preservation |
| **Tenant Isolation** | Workspace boundary enforcement on snapshot envelope retrieval |

---

## 3. Phase 9.1 Architecture & Implementation Plan

### 3.1 Core Package Layout
The comparison engine will be structured under `packages/core/src/dera/comparison/`:
```
packages/core/src/dera/comparison/
├── __init__.py
├── models.py            # Strongly typed change records, property diffs, report models
├── contracts.py         # Protocols and comparison request/result contracts
├── enums.py             # ChangeType, DiffGranularity, ComparisonStatus, ObjectType
├── errors.py            # Hierarchical domain exceptions
├── limits.py            # Resource bounding (object counts, diff counts, execution limits)
├── compatibility.py     # Snapshot format, engine, and version compatibility validation
├── matching.py          # Deterministic canonical object matching (baseline vs target)
├── evidence.py          # Verifiable before-and-after evidence structures
├── fingerprint.py       # Stable change and report SHA-256 fingerprints
├── ordering.py          # Deterministic ordering for changes and property diffs
├── summary.py           # Change metrics aggregation without double-counting
├── engine.py            # Main ComparisonEngine orchestrator with fast-path optimization
├── serializers.py       # RFC 8785 canonical JSON serializer
└── comparators/
    ├── __init__.py
    ├── namespaces.py    # Schema / namespace additions and removals
    ├── tables.py        # Table existence, type, and comment changes
    ├── columns.py       # Column type, nullability, defaults, ordinals, generated expressions
    ├── constraints.py   # Primary keys, foreign keys (ordered pairs), unique, check
    ├── indexes.py       # Index existence, uniqueness, access method, columns, predicates
    ├── relationships.py # ForeignKeyGraph directed edge diffs
    └── views.py         # View existence, definition, and materialized flag diffs
```

### 3.2 Non-Negotiable Operational Invariants
1. **Zero LLM / Generative AI:** Strict heuristic-free, deterministic matching based exclusively on canonical object identities (`ObjectId`, namespaces, native names).
2. **Read-Only Operation:** Zero database queries; operates entirely on in-memory immutable `SchemaSnapshot` inputs.
3. **Immutability:** Snapshots are strictly frozen Pydantic models; no mutation occurs during comparison.
4. **No Renames as Facts:** An added object and a removed object are reported as separate changes (`ADDED` and `REMOVED`), never conflated as a rename without authoritative lineage metadata.
5. **No Migrations in Phase 9.1:** Migration script generation and risk classification are deferred to Phase 9.2 / 9.3.

---

## 4. Security & Resource Bounding

- **Tenant Isolation:** Comparing snapshots requires workspace authorization validation when loaded through API services. The pure comparison engine itself receives immutable domain snapshots without needing network or database access.
- **Resource Limits:** Enforced via `ComparisonResourceLimits`:
  - Maximum tables: 5,000
  - Maximum columns: 50,000
  - Maximum diff entries: 100,000
  - Maximum execution time limit (wall-clock bounded)
- **Serialization Safety:** No pickle or arbitrary object unpickling; RFC 8785 deterministic JSON only.
