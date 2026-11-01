# Phase 9.4 Baseline Audit: Migration SQL Generation & Dialect-Aware Validation

**Base Commit SHA:** `853f73e3c94fc3541c28cfea4de27f4f236e2d25`  
**Date:** 2026-11-01  
**Repository:** [https://github.com/krishanth7/dera](https://github.com/krishanth7/dera)  
**Branch:** `feat/phase-9.4-migration-sql-generation`  

---

## 1. Verified Prerequisites
- [PHASE_9_1_COMPARISON_ACCEPTANCE.md](PHASE_9_1_COMPARISON_ACCEPTANCE.md) — **VERIFIED PASS**
- [PHASE_9_2_RISK_ANALYSIS_ACCEPTANCE.md](PHASE_9_2_RISK_ANALYSIS_ACCEPTANCE.md) — **VERIFIED PASS**
- [PHASE_9_3_MIGRATION_PLANNING_ACCEPTANCE.md](PHASE_9_3_MIGRATION_PLANNING_ACCEPTANCE.md) — **VERIFIED PASS**
- Phase 9.3 Abstract Planning Engine & Operation Models:
  - `MigrationPlanReport`, `AbstractMigrationOperation`, `OperationCatalog` (v1.0.0), `PlanningStage`, `ManualDecisionGate`.

## 2. Supported Dialects & Capabilities
- **PostgreSQL / Supabase PostgreSQL:**
  - Full transactional DDL, quoted identifiers (`"ident"`), `ALTER TABLE ... ADD/DROP COLUMN`, `ADD CONSTRAINT`, `CREATE INDEX [CONCURRENTLY]`.
- **SQLite:**
  - Version-aware capabilities. Direct column modifications/drops without table rebuild require SQLite $\ge 3.35.0$. Constraint additions/FK additions without table recreation are unsupported and flagged as conditional or manual table rebuild. Identifiers quoted with double quotes (`"ident"`).
- **MySQL:**
  - Backtick quoting (``` `ident` ```), non-transactional DDL (implicit commits), `ALTER TABLE ... ADD/DROP/MODIFY COLUMN`.
- **MariaDB:**
  - MariaDB-specific syntax and strict SQL mode handling.

## 3. Strict Non-Negotiables
- AI/LLM/ML models: **Strictly Prohibited**.
- Customer Database Mutation: **Strictly Prohibited**.
- Automatic SQL Execution: **Strictly Prohibited**.
- Deterministic, Review-Only Output: **Mandatory**.
- Traceability: Every SQL statement must trace back to a source `AbstractMigrationOperation`.

## 4. Implementation Plan
1. `packages/core/src/dera/migration/sql/enums.py`: SQL generation status, dialect types, transaction modes.
2. `packages/core/src/dera/migration/sql/models.py`: Generated statement models, AST structures, transaction blocks, preflight checks, rollback statements.
3. `packages/core/src/dera/migration/sql/identifiers.py`: Deterministic dialect-aware quoting and injection prevention.
4. `packages/core/src/dera/migration/sql/dialects/`:
   - `base.py`: Abstract dialect renderer interface.
   - `postgresql.py`: PostgreSQL & Supabase SQL compiler.
   - `sqlite.py`: SQLite SQL compiler.
   - `mysql.py`: MySQL SQL compiler.
   - `mariadb.py`: MariaDB SQL compiler.
5. `packages/core/src/dera/migration/sql/registry.py`: Dialect registry and version capabilities.
6. `packages/core/src/dera/migration/sql/transaction_planner.py`: Transaction grouping vs nontransactional DDL (e.g. concurrent indexes).
7. `packages/core/src/dera/migration/sql/validation.py`: Structural and syntax validation.
8. `packages/core/src/dera/migration/sql/fingerprint.py`: RFC 8785 canonical JSON SHA-256 artifact fingerprinting.
9. `packages/core/src/dera/migration/sql/reports.py`: `SqlMigrationArtifact` top-level reviewable model.
10. `packages/core/src/dera/migration/sql/compiler.py`: Main `SqlMigrationCompiler` orchestrator.
11. `packages/core/src/dera/migration/sql/tests/`: Comprehensive test suite (unit, dialect, injection, transaction, validation, determinism).
