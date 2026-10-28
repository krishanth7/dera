# Phase 6.4 Baseline Audit: Dependency Analysis & Cycle Detection

**Project:** DERA — Database Engineering & Reverse Analysis  
**Repository:** [https://github.com/krishanth7/dera](https://github.com/krishanth7/dera)  
**Milestone:** Phase 6.4 — Dependency Analysis & Cycle Detection  
**Base Commit SHA:** `fb3f6befa077229266303f96fb41a3fd776da3ae`  
**Head Branch:** `feat/phase-6.4-dependency-analysis`  
**Date:** October 28, 2026  
**Auditor:** Principal Database Reverse Engineering Architect & Engineering Team  
**Audit Status:** Verified Complete Baseline  

---

## 1. Executive Summary & Objectives

Phase 6.4 establishes the core **Dependency Analysis & Cycle Detection Engine** (`packages/core/src/dera/reverse_engineering/dependencies/`) for DERA. Built directly on top of Phase 6.3 verified Foreign Key Relationship Multigraphs (`ForeignKeyGraph`, `TableNode`, `ForeignKeyEdge`) and Phase 6.1 Canonical Schemas (`SchemaRepresentation`), Phase 6.4 provides mathematically rigorous, deterministic, strongly typed, and auditable dependency analysis, topological resolution, strongly connected component decomposition, elementary cycle enumeration, and cycle breakability evaluation.

### Primary Objectives

1. **Deterministic Dependency Graph Model (`DependencyAnalysisResult`)**:
   - Strongly typed, immutable Pydantic v2 contract (`phase-6.4-dependency-analysis-v1`) capturing global ordering, cycle reports, per-node metrics, parallel execution levels, and RFC 8785 canonical serialization with SHA-256 fingerprinting.
2. **Canonical Directionality Semantics**:
   - Preserves relational semantics: in database migrations, if Table $A$ holds a foreign key referencing Table $B$, then **Table $A$ depends on Table $B$**.
   - **Creation Order**: Table $B$ must precede Table $A$ ($\text{Parent} \to \text{Child}$).
   - **Drop / Destruction Order**: Table $A$ must precede Table $B$ ($\text{Child} \to \text{Parent}$, exact reverse of creation order).
3. **Deterministic Strongly Connected Components (SCC)**:
   - Implements Tarjan's Strongly Connected Components algorithm with stable deterministic tie-breaking based on canonical `ObjectId` sort order.
   - Partitions graph nodes into disjoint SCCs, differentiating trivial single-node components from true cyclic components.
4. **Deterministic Cycle Detection & Enumeration**:
   - Implements bounded elementary cycle enumeration (Johnson's algorithm / deterministic cycle traversal) to locate exact directed cycles within cyclic SCCs.
   - Enforces configurable circuit breakers (`max_cycles`) to prevent combinatorial explosions in dense cyclic subgraphs.
5. **Multi-Category Cycle Classification**:
   - Classifies cycles into four discrete structural categories:
     - `SELF_REFERENCING`: Table with self-referencing foreign key ($1$ node, self-loop).
     - `MUTUAL`: Mutual two-node foreign key dependency ($A \leftrightarrow B$).
     - `INDIRECT`: Simple directed cycle spanning $3$ or more tables ($A \to B \to C \to A$).
     - `COMPLEX`: Intertwined, overlapping cycles sharing nodes within a cyclic SCC.
6. **Cycle Breakability & Remediation Analysis**:
   - Analyzes foreign key column nullability and constraint deferrability to determine if a cycle can be safely broken during data loading.
   - Recommends break strategies: `NULLABLE_FOREIGN_KEY`, `DEFERRABLE_CONSTRAINT`, `POST_DATA_LOAD_CONSTRAINT`, or flags as `UNBREAKABLE`.
7. **Topological Ordering & Condensation DAG**:
   - Kahn's algorithm with min-heap / stable priority sorting to guarantee a single canonical topological order for pure DAGs.
   - For cyclic graphs, constructs the condensation DAG (contracting each cyclic SCC into a single supernode) and determines safe component-level execution stages.
8. **Parallel Execution Layering (Generations / Levels)**:
   - Partitions acyclic tables into zero-indexed dependency levels ($\text{Level } 0$: independent tables; $\text{Level } k$: tables depending strictly on levels $< k$).
   - Enables multi-threaded, parallel database migration and data ingestion tooling.
9. **Granular Dependency Metrics**:
   - Calculates in-degree, out-degree, transitive dependency counts (ancestors/prerequisites), transitive dependent counts (descendants/impact), maximum dependency depth, and identifies root, leaf, and isolated tables.
10. **Strict Validation & Resource Protection**:
    - Two-tier validation (`ERROR` vs `WARNING`) checking ordering completeness, level stratification, unresolved reference handling, and cycle breakability.
    - Zero AI/LLM/ML inference; zero customer database queries; 100% deterministic execution.

---

## 2. Prerequisites Verification

All prerequisite milestones have been thoroughly audited and verified:

| Prerequisite Subsystem | Status | Verification Detail |
| :--- | :--- | :--- |
| **Phase 5.5 Canonical Normalization & Identity** | **PASS** | `ObjectId`, length-prefixed SHA-256 stable identity, canonical models. |
| **Phase 6.1 Canonical Schema Representation** | **PASS** | `SchemaRepresentation`, `ObjectRegistry`, `TypedRef`, `SchemaHierarchy`. |
| **Phase 6.2 Structural Reconstruction** | **PASS** | `ReconstructedTable`, `ReconstructedForeignKey`, composite key order. |
| **Phase 6.3 Foreign Key Relationship Graph** | **PASS** | `ForeignKeyGraph`, `TableNode`, `ForeignKeyEdge`, `AdjacencyIndex`, WCC discovery, RFC 8785 JSON serialization, 348 tests passing. |

---

## 3. Gap Analysis

Prior to Phase 6.4, DERA lacked a comprehensive dependency analysis engine:
1. **No Canonical Dependency Order**: Downstream consumers could not determine deterministic table creation or drop sequences.
2. **No Cycle Detection or Classification**: Circular foreign keys could not be detected, enumerated, or classified.
3. **No Cycle Remediation / Breakability Analysis**: No mechanism existed to evaluate whether circular foreign keys had nullable columns or deferrable enforcement.
4. **No Parallel Execution Stratification**: No dependency layering existed for concurrent migration execution.
5. **No Condensation DAG**: Cyclic schemas could not be condensed for staged migration planning.
6. **No Dependency Metrics**: No calculation of dependency depth, centrality, or impact blast radius.

---

## 4. Architectural Strategy & Design

### Package Structure
```text
packages/core/src/dera/reverse_engineering/dependencies/
├── __init__.py                # Public API exports
├── models.py                  # Core Pydantic v2 contracts (DependencyAnalysisResult, CycleReport, etc.)
├── analyzer.py                # DependencyAnalyzer orchestrator
├── limits.py                  # DependencyResourceLimits configuration
├── errors.py                  # Dependency-specific error hierarchy
├── validation.py              # Two-tier validation and integrity rules
├── ordering.py                # Deterministic canonical sorting helpers
├── serialization.py           # RFC 8785 JSON serialization & SHA-256 fingerprinting
└── algorithms/
    ├── __init__.py            # Algorithm exports
    ├── tarjan.py              # Deterministic Tarjan SCC algorithm
    ├── johnson.py             # Deterministic bounded elementary cycle finder
    ├── topological_sort.py    # Kahn's algorithm & condensation DAG ordering
    ├── cycle_analysis.py      # Cycle classification and breakability evaluation
    └── metrics.py             # Transitive closure, depth, roots, leaves calculation
```

---

## 5. Risk Assessment & Mitigations

| Risk | Severity | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- |
| **Combinatorial Cycle Explosion** | CRITICAL | Out-of-memory or CPU hang on dense cyclic schemas | Enforce `max_cycles` circuit breaker with deterministic truncation; Tarjan SCCs compute in linear time $O(V + E)$ regardless. |
| **Non-Deterministic Topological Order** | HIGH | Diff instability in generated migration scripts | Use stable min-priority ordering based on canonical `ObjectId` sort key at every step of Kahn's algorithm. |
| **Incorrect Cycle Breakability Assessment** | HIGH | Migration failure due to attempting to break an unbreakable NOT NULL constraint | Inspect both column-level nullability (`is_nullable`) and foreign key deferrability (`is_deferrable`). |
| **Self-Referencing Loop Misclassification** | MEDIUM | Treating a table with a parent hierarchy as an intractable mutual cycle | Explicitly detect and categorize self-loops as `SELF_REFERENCING` with level handling. |

---

## 6. Implementation & Verification Plan

1. **Contracts & Errors (`errors.py`, `limits.py`, `models.py`)**: Define all Pydantic v2 contracts with strict validation and immutability.
2. **Core Graph Algorithms (`algorithms/`)**:
   - Deterministic Tarjan SCC algorithm.
   - Bounded deterministic elementary cycle enumeration.
   - Kahn's topological sort with level stratification and condensation DAG.
   - Cycle classification and breakability analysis.
   - Dependency metrics computation (depth, ancestor/descendant counts).
3. **Orchestrator (`analyzer.py`)**: Assemble the complete dependency analysis pipeline.
4. **Validation & Serialization (`validation.py`, `serialization.py`, `ordering.py`)**: Ensure deterministic ordering and RFC 8785 canonical JSON hashing.
5. **Comprehensive Test Suite (`tests/reverse_engineering/phase_6_4/`)**:
   - 16 test modules covering acyclic DAGs, self-loops, mutual cycles, indirect cycles, complex SCCs, breakability, parallel levels, determinism, golden comparisons, and cross-engine schemas.
6. **Documentation & Acceptance Audit**: Author 12 technical markdown documents in `docs/reverse-engineering/` and `docs/audit/PHASE_6_4_DEPENDENCY_ACCEPTANCE.md`.
