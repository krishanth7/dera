# Schema Maintainability Diagnostics Overview

## Purpose and Scope

Phase 8.4 establishes the deterministic schema maintainability diagnostics module in DERA. Maintainability diagnostics evaluate structural complexity, naming consistency, namespace organization, column composition patterns, and relational coupling across canonical metadata representations without executing customer SQL or performing database mutations.

All rules operate strictly without AI/ML models or opaque heuristics, delivering explainable findings with verifiable evidence and deterministic recommendations.

## Core Rules Catalog

| Rule ID | Version | Title | Category | Scope | Default Severity |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `DERA-MNT-001` | 1.0.0 | Excessive Table Width (Wide Table Pattern) | `MAINTAINABILITY` | Table | `LOW` |
| `DERA-MNT-002` | 1.0.0 | High Column Nullability Ratio | `MAINTAINABILITY` | Table | `INFORMATIONAL` |
| `DERA-MNT-003` | 1.0.0 | Identifier Naming Convention Inconsistency | `MAINTAINABILITY` | Schema / Table / Column | `INFORMATIONAL` |
| `DERA-MNT-004` | 1.0.0 | Reserved Word Identifier Usage | `MAINTAINABILITY` | Table / Column | `MEDIUM` |
| `DERA-MNT-005` | 1.0.0 | Namespace Object Imbalance & Monolithic Schema | `MAINTAINABILITY` | Namespace | `INFORMATIONAL` |
| `DERA-MNT-006` | 1.0.0 | High Relationship Structural Coupling | `MAINTAINABILITY` | Table Node | `LOW` |
| `DERA-MNT-007` | 1.0.0 | Complex Dependency Topology | `MAINTAINABILITY` | Component (SCC) | `LOW` |
| `DERA-MNT-008` | 1.0.0 | Excessive Text/Binary LOB Column Concentration | `MAINTAINABILITY` | Table | `INFORMATIONAL` |

## Execution Architecture

```text
Canonical Schema / Snapshot
           │
           ├──> Table & Column Metrics (Width, Nullability, LOBs)
           ├──> Naming & Reserved Word Evaluation
           ├──> Namespace Distribution & Imbalance
           └──> Relational Multigraph & Dependency Metrics (Coupling, Cycles)
                     │
                     ▼
          Configurable Thresholds
                     │
                     ▼
        Deterministic Rule Engine (Phase 8.1)
                     │
                     ▼
      Evidence, Findings & Stable Fingerprints
                     │
                     ▼
          Diagnostic Report (Phase 8.4)
```

## Architectural Principles

1. **Non-Subjective Defect Distinction**: Deviations from style preferences are classified as `INFORMATIONAL` or `LOW` severity maintainability concerns, distinct from structural data corruption defects.
2. **Deterministic Evaluation**: Rules evaluated across shuffled inputs produce strictly bitwise-identical results and fingerprints.
3. **Engine-Specific Semantics**: Identifier rules respect dialect-specific quoting, case folding, and reserved keywords for PostgreSQL, Supabase, MySQL, MariaDB, and SQLite.
4. **Zero AI/ML Dependencies**: Metrics rely exclusively on deterministic formulas, regular expressions, and verified graph algorithms.
