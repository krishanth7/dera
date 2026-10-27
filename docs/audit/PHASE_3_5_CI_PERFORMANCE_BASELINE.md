# DERA Phase 3.5 — CI Performance, Cache & Artifact Baseline Audit

> **Project:** DERA — Database Engineering & Reverse Analysis  
> **Tagline:** Understand Every Schema. Engineer Every Change.  
> **Repository:** [https://github.com/krishanth7/dera](https://github.com/krishanth7/dera)  
> **Maintainer:** Bunga Krishanth (`@krishanth7`)  
> **Phase:** 3 — GitHub Actions & DevSecOps  
> **Sub-phase:** 3.5 — Artifact, Cache & CI Performance Management  
> **Audit Date:** 2026-10-27  
> **Baseline Commit:** `e33dbaf09e7fa1f3ff6834114dcae32fc2b24da4` (Phase 3.4 Merged)  
> **Classification:** Official DevSecOps Engineering & Telemetry Baseline  

---

## 1. Executive Summary

Sub-phase 3.5 establishes authoritative performance engineering, cache safety, artifact governance, and test observability for DERA's GitHub Actions ecosystem.

This baseline audit evaluates empirical telemetry retrieved from the live GitHub Actions environment, establishes workflow classifications, identifies resource consumption bottlenecks, and provides the quantitative foundation for Phase 3.5 optimizations without compromising security or testing rigor.

---

## 2. Empirical Workflow Telemetry & Durations

Telemetry was gathered directly via the GitHub Actions API across recent representative production runs on the `main` branch and pull request qualifications:

| Workflow | Event Type | Run ID | Typical Duration | Observed Range | Outcome |
|---|:---:|:---:|:---:|:---:|:---:|
| **DERA CI** (`ci.yml`) | `push` (main) | `40456988257` | 41s | 41s – 61s | Success |
| **DERA CI** (`ci.yml`) | `pull_request` | `40456443992` | 49s | 45s – 65s | Success |
| **CodeQL Advanced Security** (`codeql.yml`) | `push` (main) | `40456988207` | 1m 09s | 58s – 1m 15s | Success |
| **CodeQL Advanced Security** (`codeql.yml`) | `pull_request` | `40456443968` | 58s | 55s – 1m 10s | Success |
| **Multilingual Validation** (`i18n.yml`) | `pull_request` | `40456443973` | 8s | 5s – 10s | Success |
| **Documentation Validation** (`documentation.yml`) | `pull_request` | `40456443966` | 18s | 14s – 20s | Success |
| **Security Tests** (`security-tests.yml`) | `pull_request` | `40456444197` | 12s | 10s – 15s | Success |
| **PR Title Validator** (`pr-title.yml`) | `pull_request` | `40456444209` | 7s | 5s – 10s | Success |
| **PR Readiness** (`pr-readiness.yml`) | `pull_request` | `40456444092` | 8s | 5s – 10s | Success |

### Per-Job Duration Breakdown in Primary CI (`ci.yml`)
* `Contracts & Architecture Boundaries`: **8s**
* `Frontend & Monorepo Workspaces`: **7s**
* `Python (3.12)`: **18s – 26s** (Lint, compileall, bandit, unittest, build)
* `Python (3.13)`: **21s – 26s** (Lint, compileall, bandit, unittest, build)
* `Documentation Quality Gate`: **11s**
* `Database Integration (PostgreSQL 16 Service)`: **38s** (Container init + readiness + tests)
* `Qualification Gate (Aggregate Check)`: **4s**

---

## 3. Workflow Inventory & Classification

DERA currently operates 19 workflow definitions categorized into distinct functional tiers:

```text
Workflow Inventory (19 Workflows)
├── 1. Primary PR & Commit Qualification
│   ├── ci.yml (Python matrix, Frontend, Contracts, DB, Docs, Gate)
│   ├── documentation.yml (Markdownlint, internal links, anchors, Mermaid)
│   └── i18n.yml (10-language manifest, navigation sync, parity, tokens)
├── 2. Security & Supply-Chain Protection
│   ├── codeql.yml (SAST: Python, JS/TS, Actions)
│   ├── dependency-security.yml (pip-audit & npm audit)
│   ├── dependency-review.yml (PR dependency delta review)
│   └── security-tests.yml (Bandit SAST & credential checks)
├── 3. Governance & Quality Gates
│   ├── pr-title.yml (Conventional Commits validation)
│   ├── pr-readiness.yml (PR template completeness check)
│   └── issue-triage.yml (Issue labelling and categorization)
├── 4. Specialized Runtime & Regression Verification
│   ├── sqlite-compatibility.yml (SQLite runtime across Python matrix)
│   ├── schema-regression.yml (Deterministic hashing & DAG verification)
│   └── mutation.yml (Mutation testing qualification)
├── 5. Operations, Maintenance & Release
│   ├── cache-maintenance.yml (Actions cache auditing & pruning)
│   ├── ci-performance.yml (Duration & queue observability)
│   ├── external-links.yml (Isolated weekly network link audit)
│   ├── docker.yml (Container image build verification)
│   ├── release.yml (Production release build & verification)
│   └── release-recovery.yml (Rollback & recovery automation)
```

---

## 4. Cache Inventory & Analysis

Direct inspection via `gh cache list` revealed **30 active cache entries** consuming **~320 MB** across two primary tools:

1. **Python `pip` Caching (`setup-python`):**
   * Key pattern: `setup-python-Linux-x64-24.04-Ubuntu-python-{version}-pip-{lock_or_hash}`
   * Entry sizes: ~10.0 MB – 25.6 MB per runtime version.
   * Hit Rate: ~95% on pull request synchronizations.
   * Gaps: `database-integration` and `security-tests.yml` were executing `pip install` without declaring `cache: "pip"`, causing repetitive package downloads.
2. **Node.js `npm` Caching (`setup-node`):**
   * Key pattern: `node-cache-Linux-x64-npm-{package_lock_hash}`
   * Entry sizes: ~4.1 MB – 13.3 MB.
   * Hit Rate: ~98% on pull requests.
   * Consistency: Appropriately bound to `package-lock.json` hash.

---

## 5. Artifact Inventory & Retention Analysis

Direct inspection via GitHub REST API (`actions/artifacts`) identified:
* **Active Artifacts:** CodeQL SARIF analysis exports (`codeql-sarif-python`, `codeql-sarif-javascript-typescript`, `codeql-sarif-actions`).
* **Artifact Sizes:** 19.9 KB to 83.5 KB.
* **Current Retention Period:** Defaulting to 30 days.
* **Gaps Identified:**
  1. No structured test results (JUnit XML or JSON summary) were preserved from `ci.yml`.
  2. Build distributions (`dist/`) generated during CI were discarded without retention.
  3. No diagnostic failure bundle was uploaded when jobs failed.
  4. Artifact naming lacked unified project categorization (`dera-{category}-{platform}-{runtime}-{run-id}-{attempt}`).
  5. Checksum manifests (SHA-256) were not generated prior to upload.

---

## 6. Performance Targets for Phase 3.5

Based on empirical baseline data, the following targets are established:

| Metric | Baseline Measurement | Phase 3.5 Target | Optimization Strategy |
|---|---|---|---|
| **Median PR Qualification** | 55 seconds | **≤ 45 seconds** | Pip caching in DB integration, parallel steps |
| **95th Percentile Qualification** | 65 seconds | **≤ 55 seconds** | Elimination of redundant downloads |
| **Cold-Cache CI Duration** | ~65 seconds | **≤ 60 seconds** | Optimized pip wheel installation |
| **Warm-Cache CI Duration** | ~49 seconds | **≤ 40 seconds** | Universal cache reuse across all python jobs |
| **Test Telemetry Availability** | 0% (Plain text only) | **100% (JUnit XML & JSON)** | Integration of `test_reporter.py` |
| **Artifact Naming Compliance** | 0% | **100%** | Enforcement of canonical naming schema |
| **Flaky Test Containment** | Ad-hoc | **Documented Quarantine Protocol** | Formal `FLAKY_TEST_POLICY.md` |

---

## 7. Baseline Conclusion

DERA's CI workflows exhibit strong baseline performance due to lightweight standard-library tooling and fast native runners. Key opportunities for enterprise hardening lie in universal cache coverage, deterministic artifact naming, SHA-256 manifest integrity, failure diagnostic collection, and formal test reporting standardization.
