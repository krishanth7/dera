# Phase 9.3 Baseline Audit: Deterministic Migration Planning & Dependency Ordering

**Base Commit SHA:** `676a7f5875440ac357b49b1609d22a6fb13f02d9`  
**Date:** 2026-11-01  
**Repository:** [https://github.com/krishanth7/dera](https://github.com/krishanth7/dera)  
**Branch:** `feat/phase-9.3-migration-planning-dependency-ordering`  
**Prerequisites Verified:**
- [PHASE_9_1_COMPARISON_ACCEPTANCE.md](PHASE_9_1_COMPARISON_ACCEPTANCE.md) — VERIFIED PASS
- [PHASE_9_2_RISK_ANALYSIS_ACCEPTANCE.md](PHASE_9_2_RISK_ANALYSIS_ACCEPTANCE.md) — VERIFIED PASS
- Phase 6 Canonical Schema Representation & Graph (`ForeignKeyGraph`, `TableNode`, `ForeignKeyEdge`, `TarjanSCC`) — VERIFIED PASS
- Phase 8 Deterministic Diagnostic Contracts & Evidence Models — VERIFIED PASS

---

## 1. Scope & Objective
Phase 9.3 implements the **Deterministic Migration Planning & Dependency Ordering Engine**.
It transforms verified Phase 9.1 `SchemaComparisonReport` diffs and Phase 9.2 `MigrationRiskReport` assessments into a structured, dependency-ordered, reviewable `MigrationPlanReport`.

The engine answers:
1. Which schema changes map to which abstract migration operations?
2. Which operations structurally depend on other operations (e.g., namespace before table, table before column/index/foreign key, foreign key removal before table removal)?
3. What is the deterministic topological sequence of operations with stable tie-breaking?
4. Are there dependency cycles (SCCs), and which operations are blocked vs require manual engineering resolution?
5. Which preconditions (existence, absence, existing data validation), manual gates, validation requirements, and rollback considerations attach to each operation?
6. Can the plan be deterministically fingerprinted and reproduced without AI/probabilistic logic?

## 2. Verified Contracts & Interfaces
- **Phase 9.1 Comparison Report:** Contains `SchemaChange` instances (`change_type`, `target_object_id`, `target_object_type`, `target_object_name`, `diff_details`, `change_fingerprint`).
- **Phase 9.2 Risk Report:** Contains `MigrationRiskAssessment` mapped to each change with `risk_level`, `reversibility`, `blast_radius`, `overall_score`, `risk_fingerprint`.
- **Phase 6 Graph Models:** `ForeignKeyGraph`, `TableNode`, `ForeignKeyEdge`, strongly connected component algorithms (`compute_strongly_connected_components`).
- **Dependency Direction Convention:**
  - **Prerequisite Operation $\to$ Dependent Operation**
  - E.g., `CREATE_TABLE parent` $\to$ `CREATE_TABLE child` (when child references parent in target state).
  - E.g., `DROP_FOREIGN_KEY child_fk` $\to$ `DROP_TABLE parent` (when removing parent table).

## 3. Strict Prohibitions
- AI/LLM/ML models or external heuristics: STRICTLY PROHIBITED.
- Executable SQL generation or execution: OUT OF SCOPE.
- Database mutation: PROHIBITED (Planner is 100% read-only).
- Silent cycle breaking or unsupported rollback guarantees: PROHIBITED.

## 4. Implementation Plan
1. `packages/core/src/dera/migration/planning/enums.py`: Operation types, plan statuses, stage types, manual gate statuses.
2. `packages/core/src/dera/migration/planning/models.py`: Abstract migration operations, preconditions, postconditions, manual decision gates, stages, rollback considerations, validation requirements.
3. `packages/core/src/dera/migration/planning/operation_catalog.py`: Catalog defining rules, engine applicability, preconditions, and validation for each operation type.
4. `packages/core/src/dera/migration/planning/change_mapper.py`: Traceable mapping from Phase 9.1 `SchemaChange` & Phase 9.2 `ClassifiedChange` to `AbstractMigrationOperation`.
5. `packages/core/src/dera/migration/planning/graph.py`: Operation dependency DAG builder with prerequisite $\to$ dependent edge semantics.
6. `packages/core/src/dera/migration/planning/ordering.py`: Deterministic topological sorting with stable tie-breaking and stage grouping.
7. `packages/core/src/dera/migration/planning/cycles.py`: Tarjan SCC-based cycle detection and blocking semantics.
8. `packages/core/src/dera/migration/planning/fingerprint.py`: RFC 8785 canonical JSON SHA-256 plan fingerprinting.
9. `packages/core/src/dera/migration/planning/reports.py`: `MigrationPlanReport` & `MigrationPlanSummary`.
10. `packages/core/src/dera/migration/planning/engine.py`: `MigrationPlanningEngine` facade.
11. `packages/core/src/dera/migration/planning/tests/`: Comprehensive test suite (unit, dependency ordering, cycle, determinism, cross-engine, integration).
12. Documentation & Acceptance Audit in `docs/migration/` and `docs/audit/`.
