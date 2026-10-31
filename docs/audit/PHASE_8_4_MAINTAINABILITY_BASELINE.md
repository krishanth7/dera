# DERA Phase 8.4 — Schema Maintainability Diagnostics Baseline Audit

## 1. Executive Summary & Verification Context
- **Milestone**: Phase 8.4 — Schema Maintainability Diagnostics
- **Target Branch**: `feat/phase-8.4-schema-maintainability`
- **Base Commit SHA**: `5fa80bea9b4d6a5fd1d34ece2cc0213bc7cce713`
- **Date**: 2026-10-31
- **Engine Execution**: Deterministic, strictly read-only, evidence-based, zero AI/LLM/ML models or APIs.

---

## 2. Verified Prerequisites

| Milestone | Capability Component | Contract Status | Verified Test Count | Notes |
| :--- | :--- | :---: | :---: | :--- |
| Phase 5 | Connectors (PostgreSQL, Supabase, SQLite, MySQL, MariaDB) | VERIFIED | 50+ | Verified read-only connectors and capability profiles |
| Phase 6.1 | Canonical Schema Representation | VERIFIED | 40+ | `CanonicalDatabase`, `CanonicalSchema`, `CanonicalTable`, `CanonicalColumn` |
| Phase 6.2 | Structural Schema Reconstruction | VERIFIED | 35+ | Topological reconstruction from raw connector metadata |
| Phase 6.3 | Relational Multigraph Engine | VERIFIED | 30+ | `ForeignKeyGraph`, `TableNode`, `ForeignKeyEdge`, `UnresolvedReference` |
| Phase 6.4 | Dependency & SCC Analysis | VERIFIED | 45+ | Tarjan SCC, Johnson elementary cycles, Condensation DAG, topological levels |
| Phase 6.5 | Cryptographically Verified Snapshots | VERIFIED | 50+ | SHA-256 canonical serialization, immutable audit trails |
| Phase 8.1 | Deterministic Diagnostic Rules Engine | VERIFIED | 25+ | `DiagnosticContext`, `DiagnosticFinding`, `DiagnosticEvidence`, `RuleRegistry` |
| Phase 8.2 | Index & Constraint Diagnostics | VERIFIED | 45+ | Exact/prefix index duplicates, FK index coverage, constraint integrity |
| Phase 8.3 | Relationship & Dependency Diagnostics | VERIFIED | 27+ | Graph integrity, composite FKs, cycles, depth, fan-in/fan-out, blast radius |

All prerequisites are present, functional, and 100% green (978 tests passing in main test suite).

---

## 3. Available Canonical Metadata for Maintainability Analysis

From Phase 6.1 canonical metadata:
- **Database & Schemas**: Database name, namespaces, completeness indicator, engine capability profile.
- **Tables**: Name, schema/namespace, column count, primary key definition, row counts where available, table comments.
- **Columns**: Name, ordinal position, data type, native type name, is_nullable, default expression, generated/computed definition, identity column definition, precision, scale, collation.
- **Constraints**: Primary key, foreign keys (with column pair mappings), unique constraints, check constraints.
- **Indexes**: Name, columns, expressions, is_unique, index type, operator classes.
- **Multigraph & Dependencies** (Phase 6.3 & 6.4):
  - Directed edges: Referencing child table $\to$ Referenced parent table.
  - Per-node metrics: `in_degree`, `out_degree`, `depth_level`, `transitive_dependency_count`, `transitive_dependent_count`.
  - Topological metrics: `strongly_connected_components`, `cycle_report`, `condensation_nodes`.

---

## 4. Missing Capabilities Addressed by Phase 8.4

1. **Maintainability Metrics Engine**:
   - Absence of structured, strongly typed maintainability metrics models (`MaintainabilityMetric`, `MaintainabilityMetricsReport`).
   - Lack of standard schema complexity counters (raw and normalized).
   - Missing table width and column composition metrics (nullability ratio, LOB columns).
2. **Naming Convention Engine**:
   - Absence of configurable naming convention profiles (`snake_case`, `camelCase`, `PascalCase`, `kebab-case`).
   - Lack of engine-specific identifier case folding and dialect-aware reserved word checking.
3. **Namespace Organization Diagnostics**:
   - Lack of automated detection of monolithic schema patterns (e.g., 100 tables in `public` with 5 empty namespaces).
4. **Structural Coupling Diagnostics**:
   - Lack of coupling metrics aggregating graph degree, SCC complexity, and blast radius into maintainability recommendations.

---

## 5. Phase 8.4 Rule Catalog Specification

| Rule ID | Title | Category | Severity | Target Scope | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `DERA-MNT-001` | Excessive Table Width (Wide Table Pattern) | `MAINTAINABILITY` | `INFORMATIONAL` / `LOW` / `MEDIUM` | `CanonicalTable` | Detects tables with excessive column counts exceeding configurable thresholds (default: 30 / 50 / 100). |
| `DERA-MNT-002` | High Column Nullability Ratio | `MAINTAINABILITY` | `INFORMATIONAL` / `LOW` | `CanonicalTable` | Identifies tables where nullable columns exceed configurable ratio thresholds (default: 50% / 75%). |
| `DERA-MNT-003` | Identifier Naming Convention Inconsistency | `MAINTAINABILITY` | `INFORMATIONAL` / `LOW` | `CanonicalTable` / `CanonicalColumn` | Detects tables and columns deviating from the configured naming profile (default: `snake_case`). |
| `DERA-MNT-004` | Reserved Word Identifier Usage | `MAINTAINABILITY` | `MEDIUM` / `LOW` | `CanonicalTable` / `CanonicalColumn` | Audits table and column names matching engine-specific SQL reserved words requiring quoting. |
| `DERA-MNT-005` | Namespace Object Imbalance & Monolith | `MAINTAINABILITY` | `INFORMATIONAL` | `CanonicalSchema` | Identifies extreme object concentration in a single namespace alongside empty/underutilized namespaces. |
| `DERA-MNT-006` | High Relationship Structural Coupling | `MAINTAINABILITY` | `LOW` / `MEDIUM` | `TableNode` | Identifies tables with excessively high combined relational coupling (fan-in + fan-out degree). |
| `DERA-MNT-007` | Complex Dependency Topology | `MAINTAINABILITY` | `LOW` / `MEDIUM` | `StronglyConnectedComponent` | Identifies multi-node cyclic SCCs and deep dependency chains that increase schema maintenance friction. |
| `DERA-MNT-008` | Excessive Text/Binary LOB Column Concentration | `MAINTAINABILITY` | `INFORMATIONAL` / `LOW` | `CanonicalTable` | Audits tables with numerous large text (TEXT, CLOB, VARCHAR(MAX)) or binary (BLOB, BYTEA) columns. |

---

## 6. Implementation Plan & Architecture

```text
Canonical Schema & Graph
          │
          ├──> Maintainability Metrics Engine (packages/core/src/dera/diagnostics/metrics/)
          │     ├── schema_metrics.py       (Object counts, density, normalized ratios)
          │     ├── table_metrics.py        (Width, nullability ratios, LOB counts)
          │     ├── naming_metrics.py       (Naming profiles, case detection, regex)
          │     ├── namespace_metrics.py    (Distribution, empty namespaces, entropy)
          │     └── coupling_metrics.py     (Degree centrality, SCC metrics)
          │
          └──> Diagnostic Rules Engine (packages/core/src/dera/diagnostics/rules/maintainability/)
                ├── table_width.py          (DERA-MNT-001)
                ├── column_nullability.py   (DERA-MNT-002)
                ├── naming_consistency.py   (DERA-MNT-003)
                ├── reserved_words.py       (DERA-MNT-004)
                ├── namespace_imbalance.py  (DERA-MNT-005)
                ├── structural_coupling.py  (DERA-MNT-006)
                ├── complex_dependencies.py (DERA-MNT-007)
                └── lob_concentration.py    (DERA-MNT-008)
```

---

## 7. Security & Non-Negotiable Rules
- **Strictly Non-AI**: No LLMs, prompt templates, or inference APIs.
- **Read-Only**: No DDL, no SQL execution, no customer database modification.
- **Resource Bounded**: Traversal depth capped at 10; visited node ceiling at 1000; string length checks bounded.
- **Tenant Isolation**: Workspace boundaries strictly enforced.
