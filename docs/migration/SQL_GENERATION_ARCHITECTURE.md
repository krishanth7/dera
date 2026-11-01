# Phase 9.4 SQL Generation Architecture

## Overview
Phase 9.4 implements DERA's **Deterministic, Dialect-Aware Migration SQL Generation and Validation Engine**.
It translates verified Phase 9.3 `MigrationPlanReport` specifications into offline, review-only SQL artifacts.

```
Phase 9.3 Migration Plan
          │
          ▼
Input Plan Consistency Verification
          │
          ▼
Dialect Registry & Compiler Resolution
(PostgreSQL, Supabase, SQLite, MySQL, MariaDB)
          │
          ▼
Deterministic Abstract Operation Compilation
(Preserving Phase 9.3 Topological Ordering)
          │
          ▼
Safe Dialect Identifier Quoting & Sanitization
(Injection Prevention & Double/Backtick Quoting)
          │
          ▼
Dialect Transaction Planning
(BEGIN...COMMIT vs Implicit Commits)
          │
          ▼
Offline Structural & Syntax Validation
(Semicolon Termination, Balanced Quotes)
          │
          ▼
Advisory Rollback & Preflight Check Assembly
          │
          ▼
Canonical RFC 8785 SHA-256 Artifact Fingerprinting
          │
          ▼
Review-Only SqlMigrationArtifact
("GENERATED FOR REVIEW — NOT EXECUTED")
```

## Architectural Tenets
1. **Zero-AI / Zero-Probabilistic Logic:** Pure deterministic AST and template translation based on verified metadata.
2. **Review-Only & Non-Executing:** SQL output is strictly advisory; automatic database execution and mutation are prohibited.
3. **Traceability:** Every rendered SQL statement references its source operation, canonical object ID, and source risk assessment.
4. **Injection Safety:** Identifiers are strictly escaped using dialect conventions (double quotes for Postgres/SQLite, backticks for MySQL/MariaDB) with rejection of null bytes and control characters.
