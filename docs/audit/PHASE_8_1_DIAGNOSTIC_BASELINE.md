# DERA Phase 8.1 Diagnostic Rules Engine — Baseline & Readiness Audit

**Document Reference:** `docs/audit/PHASE_8_1_DIAGNOSTIC_BASELINE.md`  
**Milestone:** Phase 8.1 — Deterministic Schema Diagnostic Rules Engine  
**Base Commit SHA:** `807a86886b220dcbd624b69e27b27826651216b8`  
**Date:** 2026-10-31  
**Author:** DERA Core Engineering & Reliability Architecture  
**Status:** APPROVED / BASELINE VERIFIED  

---

## 1. Executive Summary

Phase 8.1 establishes DERA's foundational deterministic diagnostic rules engine. The engine inspects canonical database metadata, snapshot graphs, and dependency models using explicit, versioned, reproducible rules to detect schema defects, structural anomalies, and metadata gaps without non-deterministic AI models, heuristic hallucinations, or external telemetry.

This baseline audit assesses:
1. Prerequisites across Phase 5 connectors, Phase 6 canonical schema, graph representation, dependency analysis, snapshots, and Phase 6.6 / Phase 7 APIs.
2. The architectural transition from legacy prototype diagnostics (`packages/core/src/dera/diagnostics.py`) to the production-grade `packages/core/src/dera/diagnostics/` modular engine while guaranteeing 100% backwards compatibility.
3. Strict execution invariants: Zero AI, read-only guarantees, stable cryptographic fingerprints, deterministic output ordering, and error isolation.

---

## 2. Verified Base Commit & Repository State

- **Repository:** `https://github.com/krishanth7/dera`
- **Branch:** `feat/phase-8.1-diagnostic-rules-engine`
- **Base Commit SHA:** `807a86886b220dcbd624b69e27b27826651216b8`
- **Working Tree:** Clean at audit inception.
- **Python Test Baseline:** 878 passed, 2 skipped, 0 failures across existing test suites (`tests/`).
- **Python Linting:** `ruff check packages/core` passing with 0 errors.

---

## 3. Prerequisite Verification

| Component | Repository Path | Baseline Status | Notes |
| :--- | :--- | :--- | :--- |
| **Phase 5 Connectors** | `packages/connectors/src/dera_connectors/` | **VERIFIED** | PostgreSQL, Supabase, SQLite, MySQL, MariaDB connectors provide standard provenance and capabilities. |
| **Phase 6.1 Canonical Schema** | `packages/core/src/dera/reverse_engineering/schema.py` | **VERIFIED** | `SchemaRepresentation`, `ObjectRegistry`, `TypedRef`, stable object IDs. |
| **Phase 6.2 Structural Hierarchy** | `packages/core/src/dera/reverse_engineering/hierarchy.py` | **VERIFIED** | `SchemaHierarchy` tree reconstruction, parent-child navigation. |
| **Phase 6.3 Relationship Graph** | `packages/core/src/dera/reverse_engineering/graph/` | **VERIFIED** | `RelationshipGraph`, foreign-key directional edges, self-reference tracking. |
| **Phase 6.4 Dependency Engine** | `packages/core/src/dera/reverse_engineering/dependencies/` | **VERIFIED** | Tarjan's SCC, condensation DAG, topological sort, cycle breakability. |
| **Phase 6.5 Schema Snapshots** | `packages/core/src/dera/reverse_engineering/snapshots/` | **VERIFIED** | Immutable `SchemaSnapshot`, SHA-256 fingerprint, canonical serialization. |
| **Phase 6.6 REST APIs** | `apps/api/src/dera_api/api/v1/endpoints/reverse_engineering/` | **VERIFIED** | Schemas, namespaces, tables, columns, constraints, relationships, snapshots. |
| **Phase 7 UI Integration** | `apps/web/` | **VERIFIED** | Workspaces, schema explorer, interactive ER canvas, table inspector. |

---

## 4. Gap Analysis & Architecture Transition

### 4.1 Legacy Diagnostic Prototype
The repository currently contains a single file `packages/core/src/dera/diagnostics.py` (86 lines) implementing:
- `RuleSeverity` (`INFO`, `WARNING`, `ERROR`)
- `DiagnosticFinding` (simple dataclass with `rule_id`, `category`, `table`, `message`, `remediation_ddl`)
- `evaluate_missing_primary_keys` (`RULE-INT-001`)
- `evaluate_unindexed_foreign_keys` (`RULE-PERF-002`)
- `run_all_diagnostics`

### 4.2 Identified Gaps
1. **No Typed Rule Interface / Protocol:** Rules are ad-hoc free functions rather than versioned, metadata-declaring objects.
2. **Missing Rule Metadata:** Lacks declarations for category, version, supported object kinds, required capabilities, applicability conditions, and evidence requirements.
3. **No Rule Registry:** Cannot discover, register, look up, or filter rules by category or database engine.
4. **No Explicit Diagnostic Context:** Functions take a raw `Iterable[DatabaseTable]` rather than an immutable evaluation context encompassing canonical schema, snapshot identity, graph edges, and capabilities.
5. **No Applicability & Coverage Distinction:** Lacks ability to distinguish between:
   - Evaluated & passed
   - Findings detected
   - Rule not applicable
   - Unsupported database engine
   - Insufficient metadata (missing capabilities)
   - Rule evaluation error
6. **No Stable Finding Fingerprints:** Findings lack deterministic SHA-256 fingerprints based on rule ID, rule version, canonical object ID, and evidence tuples.
7. **No Typed Evidence Model:** Evidence is embedded in freeform strings rather than structured, typed references.
8. **No Resource Limits & Error Isolation:** No bounding of object counts, edge traversals, or finding counts; an unhandled exception in one rule could terminate the entire run.

---

## 5. Non-Negotiable System Invariants

1. **Strictly Zero AI/LLM/ML:** No neural networks, LLM prompts, heuristic hallucinations, or external AI services.
2. **Read-Only Operation:** No DDL execution, no source database mutations, no modification of input snapshots.
3. **Deterministic Output & Reproducibility:**
   - Stable rule IDs (`DERA-SCHEMA-001` through `DERA-SCHEMA-005`).
   - Deterministic rule evaluation order sorted by `rule_id`.
   - Deterministic object traversal sorted by canonical object identity tuples.
   - Deterministic finding fingerprints computed via SHA-256 over `(rule_id, rule_version, object_id, canonical_evidence)`. Volatile timestamps are excluded from fingerprints.
4. **Evidence-Based Finding Model:** Every finding must cite verified canonical object references and observed attributes. Missing metadata must be recorded as `INSUFFICIENT_METADATA` rather than an invented defect.
5. **Backwards Compatibility:** Legacy symbols (`RuleSeverity`, `run_all_diagnostics`, `evaluate_missing_primary_keys`, `evaluate_unindexed_foreign_keys`) remain fully functional and importable via `dera.diagnostics`.

---

## 6. Implementation Strategy & Deliverables

### Phase 8.1 Package Structure
`packages/core/src/dera/diagnostics/`
- `__init__.py`: Package exports, public API, and legacy backwards-compatibility shims.
- `enums.py`: `DiagnosticSeverity`, `ApplicabilityStatus`, `EvaluationStatus`, `RuleCategory`.
- `evidence.py`: `DiagnosticEvidence`, typed evidence models, sanitization filters.
- `models.py`: `RuleMetadata`, `DiagnosticFinding`, `RuleEvaluation`, `DiagnosticReport`, `RuleOutcome`.
- `protocols.py`: `DiagnosticRule` Protocol.
- `context.py`: `DiagnosticContext` (immutable context wrapping canonical schema, snapshot metadata, graph, capabilities, limits).
- `applicability.py`: Rule applicability checks against engine profiles.
- `registry.py`: `DiagnosticRuleRegistry` (deterministic registration, ID validation, category/engine filtering).
- `evaluator.py`: `DiagnosticEvaluator` (orchestration, deterministic sorting, error isolation, resource limits).
- `fingerprint.py`: SHA-256 stable fingerprint generation.
- `serialization.py`: Canonical JSON serialization for diagnostic reports.
- `exceptions.py`: Domain exceptions (`DuplicateRuleError`, `ResourceLimitExceededError`, etc.).
- `rules/foundational/`:
  - `DERA-SCHEMA-001`: Unresolved canonical relationship target.
  - `DERA-SCHEMA-002`: Duplicate canonical object identity collision.
  - `DERA-SCHEMA-003`: Invalid canonical relationship mapping.
  - `DERA-SCHEMA-004`: Missing required canonical structural metadata.
  - `DERA-SCHEMA-005`: Unsupported or incomplete inspection capability.

### Test Suites
`tests/diagnostics/`
- `test_models.py`, `test_registry.py`, `test_context.py`, `test_applicability.py`, `test_fingerprint.py`, `test_serialization.py`, `test_evaluator.py`, `test_foundational_rules.py`, `test_determinism.py`, `test_cross_engine.py`, `test_snapshots.py`, `test_security.py`.

### Documentation Suite
15 documentation files in `docs/diagnostics/` and `docs/audit/PHASE_8_1_DIAGNOSTIC_ACCEPTANCE.md`.

---

## 7. Baseline Audit Sign-Off

- **Baseline Verdict:** PASS — All prerequisites verified; codebase is ready for Phase 8.1 implementation.
- **Base Commit SHA:** `807a86886b220dcbd624b69e27b27826651216b8`
- **Target Branch:** `feat/phase-8.1-diagnostic-rules-engine`
