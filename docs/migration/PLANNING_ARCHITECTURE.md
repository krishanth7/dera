# Phase 9.3 Migration Planning Architecture

## Overview
Phase 9.3 establishes DERA's **Deterministic Migration Planning and Dependency Ordering Engine**.
It bridges Phase 9.1 (`ComparisonReport`) and Phase 9.2 (`MigrationRiskReport`) into a structured, reviewable, dependency-ordered `MigrationPlanReport`.

```
Phase 9.1 Comparison Report
          │
          ▼
Phase 9.2 Risk Assessment
          │
          ▼
Input Consistency Verification
          │
          ▼
Change-to-Operation Mapping (Catalog-Driven)
          │
          ▼
Operation Dependency DAG Construction (Prerequisite ➔ Dependent)
          │
          ├─────────────────────────┐
          ▼                         ▼
Tarjan SCC Cycle Detection    Deterministic Topological Sorting
          │                   (Stable Lexicographical Tie-Breaking)
          ▼                         │
Blocked Operation Annotation        ▼
          │                   Stage Grouping (7 Sequential Stages)
          └─────────────────────────┼─────────────────────────┘
                                    │
                                    ▼
                      Manual Gates & Preconditions Attachment
                                    │
                                    ▼
                      Rollback Considerations & Validations
                                    │
                                    ▼
                      Canonical SHA-256 Plan Fingerprinting
                                    │
                                    ▼
                      Structured MigrationPlanReport
```

## Architectural Tenets
1. **Zero-AI / Zero-Probabilistic Logic:** Purely deterministic, reproducible, evidence-based graph analysis.
2. **Explicit Edge Direction:** Directed edge is always `Prerequisite Operation -> Dependent Operation`.
3. **No Silent Cycle Breaking:** Any strongly connected component (circular dependency) marks the involved operations as `BLOCKED` with detailed explanatory reasons.
4. **Read-Only & Advisory:** Never mutates databases; migration SQL generation and execution are strictly out of scope.
5. **Deterministic Serialization:** RFC 8785 canonical JSON formatting with cryptographic SHA-256 fingerprints.
