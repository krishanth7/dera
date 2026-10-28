# Phase 6.3 Baseline Audit: Foreign Key Relationship Graph

**Project:** DERA — Database Engineering & Reverse Analysis  
**Repository:** [https://github.com/krishanth7/dera](https://github.com/krishanth7/dera)  
**Milestone:** Phase 6.3 — Foreign Key Relationship Graph  
**Base Commit SHA:** `bba3b79e1f3fa146102c39f41ba567c8ba07c92a`  
**Head Branch:** `feat/phase-6.3-foreign-key-graph`  
**Date:** October 28, 2026  
**Auditor:** Principal Database Reverse Engineering Architect & Engineering Team  
**Audit Status:** Verified Complete Baseline  

---

## 1. Executive Summary & Objectives

Phase 6.3 establishes the core **Foreign Key Relationship Graph Engine** (`packages/core/src/dera/reverse_engineering/graph/`) for DERA. Built directly on top of verified Phase 6.2 structural reconstruction models (`ReconstructedTable`, `ReconstructedForeignKey`) and Phase 6.1 canonical schemas (`SchemaRepresentation`, `ObjectRegistry`), Phase 6.3 transforms verified foreign key referential constraints into a deterministic, strongly typed, immutable directed multigraph.

### Primary Objectives
1. **Canonical Graph Contract (`ForeignKeyGraph`)**: Strongly typed, frozen, auditable graph model with contract versioning, source database identity, table nodes, foreign key edges, unresolved reference records, capability profiles, and SHA-256 fingerprinting.
2. **Table Nodes (`TableNode`)**: Strongly typed nodes preserving stable canonical table `ObjectId`, namespace `ObjectId`, native table name, namespace name, table classification, metadata completeness, and extraction provenance.
3. **Foreign Key Edges (`ForeignKeyEdge`)**: Strongly typed directed edges representing verified constraints. Canonical edge direction is defined strictly as:
   $$\text{Source child table (declaring FK)} \longrightarrow \text{Referenced parent table (holding PK/UQ)}$$
4. **Stable Edge Identities**: Identified by the unique canonical foreign key constraint `ObjectId` (not merely source/target pairs), fully supporting parallel edges (multiple distinct FKs between the same tables) and self-referencing loops.
5. **Composite Foreign Keys**: Strict preservation of ordered `(source_column, referenced_column)` column pairings without splitting composite keys into separate graph edges.
6. **Cross-Namespace Foreign Keys**: Comprehensive support for foreign keys spanning schemas/namespaces while preserving stable namespace `ObjectId`s and qualified names.
7. **Adjacency Indexes**: Fast $O(1)$ indexed access for outgoing edges, incoming edges, direct relationship queries (`relationships_between(src, tgt)`), and neighbor queries (outgoing, incoming, all neighbors).
8. **Bounded Graph Traversal**: Deterministic BFS and DFS traversal engines with strict resource bounds: `max_depth`, `max_visited_nodes`, `max_returned_edges`, and direction selection (`OUTGOING`, `INCOMING`, `BOTH`).
9. **Connected Component Discovery**: Weakly connected components (WCC) partitioned deterministically, treating directed edges as undirected strictly for this topological operation. (Strongly connected components and cyclic dependency engine deferred to Phase 6.4).
10. **Referential Integrity & Graph Validation**: Auditable two-tier validation (`ERROR` vs `WARNING`), checking node uniqueness, edge uniqueness, endpoint existence, column pair fidelity, adjacency symmetry, workspace scope isolation, and unresolved reference tracking.
11. **Strict Determinism**: Input-order-independent construction, deterministic canonical sorting of nodes, edges, adjacency mappings, traversal paths, and JSON serialization.
12. **Resource Limits & Security**: Configurable `GraphResourceLimits` preventing denial-of-service, unbounded recursion, or memory exhaustion. Zero database queries executed; zero AI/LLM/heuristic inference.

---

## 2. Prerequisites Verification

All prerequisite milestones have been thoroughly audited and verified:

| Prerequisite Subsystem | Status | Verification Detail |
| :--- | :--- | :--- |
| **Phase 5.1 Universal Connector Protocol** | **PASS** | `DatabaseConnector`, `CapabilityRegistry`, `DatabaseMetadataReport`. |
| **Phase 5.2 PostgreSQL & Supabase Adapter** | **PASS** | Schema namespaces, array/JSON types, check constraints, domain types. |
| **Phase 5.3 SQLite Adapter** | **PASS** | Filesystem isolation, PRAGMA catalogs, generated columns, STRICT tables. |
| **Phase 5.4 MySQL & MariaDB Adapters** | **PASS** | INFORMATION_SCHEMA queries, ENUM/SET types, AUTO_INCREMENT, FK actions. |
| **Phase 5.5 Canonical Normalization & Identity** | **PASS** | `compute_stable_object_id`, length-prefixed SHA-256 stable identity, canonical models. |
| **Phase 5.6 Read-Only Enforcement & Safety** | **PASS** | Read-only enforcement, static regex mutation blockers, connection safety. |
| **Phase 6.1 Canonical Schema Representation** | **PASS** | `SchemaRepresentation`, `ObjectRegistry`, `TypedRef`, `SchemaHierarchy`, deterministic serialization. |
| **Phase 6.2 Structural Reconstruction** | **PASS** | `ReconstructedTable`, `ReconstructedForeignKey`, `StructuralReconstructionResult`, composite key order preservation. |

---

## 3. Existing Graph Functionality & Reusable Modules

### Legacy Graph Prototype (`dera/graph.py`)
An initial prototype (`compute_topological_sort`, `build_dependency_graph`) existed in `packages/core/src/dera/graph.py` for early Kahn's algorithm regression tests on un-normalized `DatabaseTable` strings. It does not utilize canonical `ObjectId`s, cannot handle parallel relationships, lacks composite key column mappings, provides no bidirectional adjacency, and lacks bounds or validation.

### Reusable Core Modules
- **`dera.metadata.identity`**: `ObjectId`, `compute_stable_object_id` for deterministic length-prefixed SHA-256 identities.
- **`dera.metadata.enums`**: `ObjectKind`, `ForeignKeyAction`, `TableType`, `MetadataCompleteness`, `IdentityScope`.
- **`dera.metadata.models`**: `CanonicalForeignKey`, `ForeignKeyMapping`, `MetadataProvenance`.
- **`dera.reverse_engineering.registry`**: `ObjectRegistry` for $O(1)$ schema lookup and kind filtering.
- **`dera.reverse_engineering.references`**: `ResolutionStatus`, `ForeignKeyReference`.
- **`dera.reverse_engineering.schema`**: `SchemaRepresentation`, resource bounds baseline.
- **`dera.reverse_engineering.reconstruction.models`**: `ReconstructedTable`, `ReconstructedColumn`, `ReconstructedForeignKey`, `StructuralReconstructionResult`.

---

## 4. Gap Analysis & Missing Functionality

Prior to Phase 6.3, DERA lacked a dedicated foreign key graph engine:
1. **No Typed Graph Contract**: No immutable container encapsulating nodes, edges, adjacency, and unresolved references.
2. **No Discrete Node & Edge Abstractions**: Foreign keys were stored as flat arrays within tables, without first-class graph edge semantics or adjacency indexing.
3. **No Parallel Edge Support**: Tables with multiple foreign keys between them (e.g. `orders.created_by` and `orders.approved_by` referencing `users.id`) were not indexed as distinct multigraph edges.
4. **No Bidirectional Adjacency Indexes**: Navigating from parent table to referencing child tables required $O(V \cdot E)$ linear table scans.
5. **No Traversal Engine**: No bounded breadth-first search (BFS) or depth-first search (DFS) with termination guarantees and loop protection.
6. **No Weakly Connected Component Partitioning**: No ability to isolate disjoint schema clusters for incremental analysis.
7. **No Unresolved Reference Registry**: Foreign keys referencing external, inaccessible, or incomplete tables were either dropped or raised fatal errors without structured preservation.

---

## 5. Architectural Strategy & Design

### Package Structure
```text
packages/core/src/dera/reverse_engineering/graph/
├── __init__.py                # Module exports
├── models.py                  # Core graph contracts (ForeignKeyGraph, UnresolvedReference)
├── nodes.py                   # TableNode model and factory
├── edges.py                   # ForeignKeyEdge and ColumnPairMapping models
├── builder.py                 # ForeignKeyGraphBuilder pipeline
├── adjacency.py               # AdjacencyIndex container and bidirectional lookup
├── traversal.py               # Bounded BFS & DFS traversal engines
├── relationships.py           # Direct relationship & neighbor query service
├── validation.py              # Referential integrity and structural validation
├── ordering.py                # Deterministic canonical sorting for graph elements
├── serialization.py           # Deterministic JSON export and deserialization
├── capabilities.py            # Graph capability and completeness assessment
├── limits.py                  # GraphResourceLimits configuration
└── errors.py                  # Graph-specific error hierarchy
```

### Architectural Principles
1. **Zero AI / LLM / Probabilistic Inference**: Every edge is backed 100% by a verified relational foreign key constraint. No edge is inferred from column names (e.g. `user_id`) or naming conventions.
2. **Canonical Directionality**: Edges strictly point from child (referencing) table to parent (referenced) table:
   $$\text{Edge: } \text{Source Table} \xrightarrow{\quad\text{FK}\quad} \text{Referenced Table}$$
3. **Directed Multigraph**: Tables may have multiple parallel edges between them and valid self-referencing loops.
4. **Strict Immutability**: `ForeignKeyGraph`, `TableNode`, and `ForeignKeyEdge` are frozen Pydantic v2 models (`frozen=True`).
5. **Algorithmic Bounds**: Traversal enforces `max_depth`, `max_visited_nodes`, and `max_returned_edges` to prevent unbounded cycles or denial of service.

---

## 6. Risk Assessment & Mitigations

| Risk | Severity | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- |
| **Self-Referencing Cycles in Traversal** | HIGH | Infinite loops in recursive graph traversal | Track visited node and edge sets; enforce `max_depth` and `max_visited_nodes`. |
| **Parallel Edge Collapsing** | HIGH | Loss of distinct foreign key constraints between same tables | Key edges by unique constraint `ObjectId`, not by `(source_id, target_id)`. |
| **Composite Column Order Corruption** | HIGH | Invalid join criteria in downstream tools | Maintain ordered tuple of `ColumnPairMapping` matching declared ordinal sequences. |
| **Cross-Workspace Identity Leakage** | CRITICAL | Security isolation breach between tenants | Validate that all nodes and edges belong to the identical workspace scope. |
| **Missing Target Table Crash** | MEDIUM | Reconstruction crash on partial database dumps | Store missing targets as structured `UnresolvedReference` records; mark edge resolution status. |

---

## 7. Implementation Plan

1. **Error Hierarchy & Limits (`errors.py`, `limits.py`)**: Define `ForeignKeyGraphError`, `GraphTraversalError`, `GraphValidationError`, and `GraphResourceLimits`.
2. **Domain Models (`nodes.py`, `edges.py`, `models.py`)**: Implement `TableNode`, `ColumnPairMapping`, `ForeignKeyEdge`, `UnresolvedReference`, and `ForeignKeyGraph`.
3. **Adjacency & Query Indexing (`adjacency.py`, `relationships.py`)**: Implement bidirectional adjacency maps and direct relationship/neighbor lookups.
4. **Bounded Traversal & Components (`traversal.py`)**: Implement bounded BFS, DFS, and weakly connected components (WCC).
5. **Validation & Ordering (`validation.py`, `ordering.py`)**: Implement two-tier validation findings and deterministic sorting.
6. **Graph Builder (`builder.py`)**: Orchestrate graph construction from `StructuralReconstructionResult`, `SchemaRepresentation`, or `CanonicalDatabase`.
7. **Serialization (`serialization.py`)**: Implement deterministic JSON export with SHA-256 fingerprinting.
8. **Comprehensive Test Suite (`tests/reverse_engineering/phase_6_3/`)**: Unit, contract, composite key, cross-namespace, traversal, security, determinism, golden, and integration tests.
9. **Documentation & Acceptance Audit**: Author 12 markdown documents in `docs/reverse-engineering/` and `docs/audit/PHASE_6_3_GRAPH_ACCEPTANCE.md`.
