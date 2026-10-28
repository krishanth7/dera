# Phase 6.2 Baseline Audit: Tables, Columns & Constraint Reconstruction

**Project:** DERA — Database Engineering & Reverse Analysis  
**Repository:** [https://github.com/krishanth7/dera](https://github.com/krishanth7/dera)  
**Milestone:** Phase 6.2 — Tables, Columns & Constraint Reconstruction  
**Base Commit SHA:** `3a87596b745b11aee253c50b84be1bb584cb45f4`  
**Head Branch:** `feat/phase-6.2-structural-reconstruction`  
**Date:** October 27, 2026  
**Auditor:** Principal Database Reverse Engineering Architect & Systems Team  
**Audit Status:** Complete  

---

## 1. Executive Summary & Objectives

The primary mission of Phase 6.2 is to build a deterministic, strongly typed, immutable, and cross-engine compatible **Structural Reconstruction Engine** (`reconstruction/`) on top of Phase 6.1 Canonical Schema Representation (`SchemaRepresentation`) and Phase 5.5 Canonical Metadata (`CanonicalDatabase`).

The structural reconstruction engine transforms schema representations into validated domain models of:
1. **Table Definitions (`ReconstructedTable`)**: Preserving native attributes, storage parameters, namespace context, table kind, ordered columns, primary key, unique constraints, foreign keys, check constraints, and metadata completeness.
2. **Column Definitions (`ReconstructedColumn`)**: Preserving source ordinal positions, native data types, canonical type classification, nullability states (`NULLABLE`, `NOT_NULLABLE`, `UNKNOWN`), inert default value metadata, generated column expressions and storage modes, identity and auto-increment attributes, and collation.
3. **Primary Key Constraints (`ReconstructedPrimaryKey`)**: Reconstructing single and composite primary keys with strict preservation of declared key column order (e.g., `(tenant_id, order_id)`).
4. **Foreign Key Constraints (`ReconstructedForeignKey`)**: Reconstructing single and composite foreign keys with ordered source and target column pairs, referential actions (`CASCADE`, `RESTRICT`, `NO ACTION`, `SET NULL`, `SET DEFAULT`), match types, deferrability, and enforcement states.
5. **Unique Constraints (`ReconstructedUniqueConstraint`)**: Reconstructing unique constraints distinguishing them from secondary unique indexes, preserving multi-column orders and engine-specific NULL semantics.
6. **Check Constraints (`ReconstructedCheckConstraint`)**: Reconstructing check constraints with inert expression storage (strictly non-evaluated text strings) and validation/enforcement states.
7. **Unified Structural Reconstruction Result (`StructuralReconstructionResult`)**: Encapsulating the reconstructed graph, typed references, validation findings, engine capability profiling, and deterministic SHA-256 fingerprinting.

---

## 2. Prerequisites Verification

| Prerequisite Subsystem | Status | Verification Detail |
| :--- | :--- | :--- |
| **Phase 5.1 Universal Connector Protocol** | **PASS** | `DatabaseConnector`, `CapabilityRegistry`, `DatabaseMetadataReport`. |
| **Phase 5.2 PostgreSQL & Supabase Adapter** | **PASS** | Schema namespaces, array/JSON types, check constraints, domain types. |
| **Phase 5.3 SQLite Adapter** | **PASS** | Filesystem isolation, PRAGMA catalogs, generated columns, STRICT tables. |
| **Phase 5.4 MySQL & MariaDB Adapters** | **PASS** | INFORMATION_SCHEMA queries, ENUM/SET types, AUTO_INCREMENT, FK actions. |
| **Phase 5.5 Canonical Normalization & Identity** | **PASS** | `compute_stable_object_id`, length-prefixed SHA-256 stable identity, canonical models. |
| **Phase 5.6 Read-Only Enforcement & Safety** | **PASS** | Read-only enforcement, static regex mutation blockers, connection safety. |
| **Phase 6.1 Canonical Schema Representation** | **PASS** | `SchemaRepresentation`, `ObjectRegistry`, `TypedRef`, `SchemaHierarchy`, deterministic serialization. |

---

## 3. Existing Models & Interfaces Reused

Phase 6.2 strictly avoids redundant models by building upon Phase 5.5 and Phase 6.1 foundations:
- **`dera.metadata.enums`**: `ObjectKind`, `CanonicalTypeCategory`, `ConstraintType`, `ForeignKeyAction`, `IndexType`, `TableType`, `TriggerTiming`, `TriggerEvent`, `GenerationMode`, `MetadataCompleteness`.
- **`dera.metadata.identity`**: `compute_stable_object_id` (deterministic length-prefixed SHA-256 generator with workspace isolation).
- **`dera.metadata.models`**: `CanonicalDatabase`, `CanonicalNamespace`, `CanonicalTable`, `CanonicalColumn`, `CanonicalConstraint`, `CanonicalForeignKey`, `CanonicalIndex`, `CanonicalView`, `CanonicalTrigger`.
- **`dera.reverse_engineering.registry`**: `ObjectRegistry` providing $O(1)$ lookup and kind-indexed filtering.
- **`dera.reverse_engineering.references`**: `TypedRef`, `ForeignKeyReference`, and `ResolutionStatus`.
- **`dera.reverse_engineering.hierarchy`**: `SchemaHierarchy` providing deterministic parent-child ownership navigation.
- **`dera.reverse_engineering.schema`**: `SchemaRepresentation` holding root metadata, provenance, and capability profiles.

---

## 4. Gap Analysis & Missing Functionality

Prior to Phase 6.2, schema objects exist as generic metadata nodes and flat constraint records without contextual structural synthesis:
1. **No High-Level Table Reconstruction**: Tables exist as raw metadata items without aggregated, verified structural views combining their ordered columns, composite keys, and constraint sets.
2. **Missing Granular Column Semantics**: Nullability (`UNKNOWN`), inert default value classification (`NoDefault`, `LiteralDefault`, `ExpressionDefault`, `GeneratedDefault`, `UnknownDefault`), and engine-specific identity/auto-increment metadata need explicit structured modeling.
3. **No Composite Key Integrity Verification**: Composite primary keys and foreign keys require strict ordered column sequence validation, column ownership checks, and pair count matching.
4. **No Structural Constraint Semantics**: Distinctions between table-level unique constraints and unique indexes, deferrability states, and inert check expression storage are not consolidated.
5. **No Two-Tier Validation Architecture**: Lack of structured findings (`Error`, `Warning`, `Informational`) distinguishing metadata incompleteness from actual structural corruption.
6. **No Strict vs. Partial Reconstruction Modes**: Lack of configurable reconstruction behavior allowing graceful handling of incomplete catalog dumps without sacrificing strict validation on complete schemas.

---

## 5. Architectural Strategy & Design

### Package Structure
```text
packages/core/src/dera/reverse_engineering/reconstruction/
├── __init__.py                # Module exports
├── models.py                  # Reconstructed domain models (Table, Column, Constraints, Result)
├── errors.py                  # Reconstruction error taxonomy
├── semantics.py               # Engine-specific semantics (PG, SQLite, MySQL, MariaDB)
├── tables.py                  # Table reconstruction logic
├── columns.py                 # Column reconstruction & type/null/default handling
├── primary_keys.py            # Single & composite primary key reconstruction
├── foreign_keys.py            # Single & composite foreign key reconstruction
├── unique_constraints.py      # Unique constraint reconstruction
├── check_constraints.py       # Check constraint reconstruction (inert expressions)
├── references.py              # Referential resolution & status management
├── validation.py              # Structural validation (findings, severity levels)
├── ordering.py                # Deterministic multi-key sorting
└── builder.py                 # StructuralReconstructionBuilder pipeline
```

### Key Principles
1. **Strict Immutability**: All reconstructed models are frozen Pydantic v2 models (`frozen=True`).
2. **Zero Evaluation**: Default expressions, check constraint expressions, and generated column expressions are preserved as inert text strings and never executed or evaluated.
3. **Deterministic Multi-Key Ordering**: Column lists in composite keys preserve declared ordinal positions; collection sorting is invariant to input dictionary order.
4. **Zero AI / Zero LLM**: 100% deterministic, explainable Python algorithms.

---

## 6. Risk Assessment & Mitigations

| Risk | Severity | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- |
| **Composite Key Ordering Corruption** | HIGH | Incorrect primary/foreign key definitions | Validate column list against source ordinal positions without alphabetical sorting. |
| **Incomplete Catalog False Negatives** | MEDIUM | Erroneously flagging missing constraints on partial dumps | Introduce `ReconstructionMode.PARTIAL` and `ValidationSeverity.WARNING` for restricted/partial completeness states. |
| **Foreign Key Count Mismatch** | HIGH | Invalid composite foreign keys | Validate that source column count strictly matches referenced column count when target table is present. |
| **Default/CHECK Expression Code Execution** | CRITICAL | Security vulnerability | Store all SQL expressions as inert text literals. Never invoke `eval()`, `exec()`, or database parsers. |
| **Exponential Traversal in Reference Resolution** | HIGH | Denial-of-Service on large schemas | Leverage Phase 6.1 `ObjectRegistry` for $O(1)$ lookups. |

---

## 7. Implementation Plan

1. **Architecture & Error Hierarchy**: Create `errors.py` and `models.py` with strongly typed, frozen models.
2. **Engine Semantics**: Create `semantics.py` handling dialect-specific nuances (PostgreSQL identity/deferrability, SQLite affinity/STRICT/WITHOUT ROWID, MySQL/MariaDB AUTO_INCREMENT).
3. **Column & Table Reconstruction**: Implement `columns.py` (nullability, defaults, generated columns, identity) and `tables.py`.
4. **Constraint Reconstruction**: Implement `primary_keys.py`, `foreign_keys.py`, `unique_constraints.py`, and `check_constraints.py`.
5. **Reference Resolution & Validation**: Implement `references.py` and `validation.py` with structured finding classification.
6. **Deterministic Ordering & Serialization**: Implement `ordering.py` and builder pipeline `builder.py`.
7. **Comprehensive Test Suite**: Develop unit, contract, cross-engine, determinism, security, integration, and golden tests.
8. **Documentation & Acceptance**: Author 11 technical documentation files in `docs/reverse-engineering/` and `docs/audit/PHASE_6_2_STRUCTURAL_ACCEPTANCE.md`.
9. **CI Verification & PR**: Extend CI workflow, verify all checks, and open PR.
