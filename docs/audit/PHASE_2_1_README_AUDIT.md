# Phase 2.1 — README Content Audit & Technical Baseline

**Project:** DERA — Database Engineering & Reverse Analysis  
**Repository:** [https://github.com/krishanth7/dera](https://github.com/krishanth7/dera)  
**Lead Maintainer:** [Krishanth](https://github.com/krishanth7) (`@krishanth7`)  
**Audit Date:** October 2026  
**Document Status:** Complete & Verified Baseline  

---

## 1. Executive Summary

This audit evaluates the root [English README](../../README.md) of **DERA — Database Engineering & Reverse Analysis** to establish an authoritative, technically accurate, and accessible documentation foundation for Phase 2.

The audit inspects technical claims, badge accuracy, quick-start reproducibility, architecture diagrams, database compatibility statements, feature matrices, and accessibility compliance against actual repository implementation.

---

## 2. Detailed Audit Findings Matrix

| Finding ID | Location in README | Severity | Evidence / Observed Issue | Recommended Correction | Resolution Status |
|:---|:---|:---:|:---|:---|:---:|
| **AUD-2.1-01** | Line 13 (Header hero) | **Medium** | Phrasing *"enterprise-grade open-source"* could be misconstrued as claiming formal commercial enterprise certification. | Refine phrasing to *"An independent, enterprise-oriented open-source database reverse-engineering platform"*. Clarify that DERA is an independent project. | **Resolved** |
| **AUD-2.1-02** | Lines 118–135 (Feature Matrix) | **Medium** | Feature matrix lists components but lacks explicit engine capabilities (e.g. SQLite table/column discovery vs. PostgreSQL in-progress introspection vs. planned rule engine). | Expand the feature status matrix into distinct capabilities matching actual source code and automated tests. Use only `Implemented`, `Experimental`, `In Progress`, `Planned`. | **Resolved** |
| **AUD-2.1-03** | Lines 142–192 (Mermaid Architecture) | **Low** | Architecture diagram depicts `TARGET_PG` connection without visually distinguishing that PostgreSQL catalog extraction is currently in-progress via ephemeral integration tests. | Add dotted/dashed visual styling (`-.->`) or status callouts to differentiate implemented components (SQLite connector, Core models) from in-progress modules (PostgreSQL). | **Resolved** |
| **AUD-2.1-04** | Line 291 (Quick Start Output) | **Low** | Quick start sample output states *"52 docs files valid"*, whereas the actual CI validator inspects and verifies **69 markdown documentation files**. | Update sample output to reflect current test suite counts: 32 tests passing, 69 documentation files verified, 10 language READMEs valid. | **Resolved** |
| **AUD-2.1-05** | Lines 313–320 (Database Compatibility) | **Medium** | PostgreSQL and Supabase rows list *"Read-only session pragma"*, which conflates SQLite's `PRAGMA query_only = ON` with PostgreSQL transaction-level controls (`SET default_transaction_read_only = ON`). | Standardize terminology: specify `PRAGMA query_only = ON` for SQLite, and `SET default_transaction_read_only = ON` / connection-level read-only flags for PostgreSQL. | **Resolved** |
| **AUD-2.1-06** | Lines 347–352 (Roadmap Checklist) | **Medium** | Roadmap checklist shows *"Phase 1.5 ... (Current)"*, neglecting the completion of Phase 1.6 governance and recovery. | Update roadmap summary: Phase 1 (Foundation & Governance) marked complete (with PR #20 under maintainer review); Phase 2 (Multilingual Documentation) active with Sub-phase 2.1 in progress. | **Resolved** |
| **AUD-2.1-07** | Lines 19–26 (Badges Section) | **Low** | Badges use shields.io images with generic styling; need explicit alt text and verified target URLs ensuring every badge points to an active CI workflow or config file. | Verify all badge target URLs (`ci.yml`, `codeql.yml`, `documentation.yml`, `LICENSE`, `pyproject.toml`, `tsconfig.json`). | **Resolved** |
| **AUD-2.1-08** | Lines 325–334 (Security Principles) | **Low** | Security principles are clear, but need explicit clarification that DERA does not claim formal compliance certifications (e.g., SOC 2, ISO 27001). | Add an explicit disclaimer that DERA enforces engineering defense-in-depth principles without claiming formal third-party regulatory certification. | **Resolved** |
| **AUD-2.1-09** | General Document Accessibility | **Low** | Visual Mermaid diagrams lack companion text descriptions for screen readers and text-based browsing. | Add structured textual architecture breakdowns immediately following the Mermaid diagram to guarantee full a11y compliance. | **Resolved** |

---

## 3. Verification of Core Invariants

- **Maintainer Identity:** Strictly attributed to **`Krishanth`** (`@krishanth7`). Zero occurrences of deprecated naming patterns.
- **Strict Non-AI Mandate:** The README prominently highlights DERA's deterministic, non-AI architecture (zero LLMs, zero vector stores, zero external inference APIs).
- **Database Safety:** Enforces read-only system catalog queries exclusively; zero table-row extraction.
- **Link Integrity:** 100% of internal documentation links resolve to existing files.

---

## 4. Conclusion & Next Actions

The identified audit findings have been formulated into actionable corrections incorporated directly into the Phase 2.1 primary English `README.md`, `docs/README.md`, `docs/development/GETTING_STARTED.md`, and `docs/development/README_MAINTENANCE.md`.
