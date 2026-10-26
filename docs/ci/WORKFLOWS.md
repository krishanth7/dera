# DERA Workflow Inventory & Technical Reference

This document provides a granular catalog of all 18 GitHub Actions workflows configured in the `.github/workflows/` directory.

---

## 1. Master Workflow Catalog

| Workflow File | Display Name | Trigger Events | Primary Objective | Default Permissions |
|---|---|---|---|---|
| [`ci.yml`](../../.github/workflows/ci.yml) | `DERA \| CI` | `push`, `pull_request`, `workflow_dispatch` | Primary quality gate: Python matrix, TypeScript typecheck, contract parity | `contents: read` |
| [`ci-full-pr.yml`](../../.github/workflows/ci-full-pr.yml) | `DERA \| Full PR Qualification` | `pull_request` (`ci:full`), `workflow_dispatch` | Deep qualification for connectors, schema diffs, and release candidate PRs | `contents: read` |
| [`codeql.yml`](../../.github/workflows/codeql.yml) | `DERA \| CodeQL Advanced Security` | `push`, `pull_request`, `schedule`, `workflow_dispatch` | Advanced static application security testing for Python, JS/TS, and Actions | `contents: read`, `security-events: write` |
| [`pr-title.yml`](../../.github/workflows/pr-title.yml) | `DERA \| PR Title Validator` | `pull_request` (open, sync, reopen, edit) | Conventional Commit pull request title format validation | `contents: read` |
| [`pr-readiness.yml`](../../.github/workflows/pr-readiness.yml) | `DERA \| PR Readiness` | `pull_request` (open, sync, reopen, edit, ready) | Description length, checklist verification, and security disclosure check | `contents: read` |
| [`documentation.yml`](../../.github/workflows/documentation.yml) | `DERA \| Documentation Validation` | `push`, `pull_request`, `workflow_dispatch` | Markdown heading hierarchy, internal file links, and UTF-8 validation | `contents: read` |
| [`i18n.yml`](../../.github/workflows/i18n.yml) | `DERA \| Multilingual Validation` | `push`, `pull_request`, `workflow_dispatch` | 10-language parity, bidirectional cross-navigation links, and Arabic RTL checks | `contents: read` |
| [`dependency-review.yml`](../../.github/workflows/dependency-review.yml) | `DERA \| Dependency Review` | `pull_request` (manifest changes) | Supply chain security, known vulnerability detection, and license auditing | `contents: read`, `pull-requests: read` |
| [`security-tests.yml`](../../.github/workflows/security-tests.yml) | `DERA \| Security Tests` | `push`, `pull_request`, `schedule`, `workflow_dispatch` | Bandit SAST scanner, credential sanitization checks, and read-only limits | `contents: read` |
| [`database-integration.yml`](../../.github/workflows/database-integration.yml) | `DERA \| Database Integration` | `push`, `pull_request`, `workflow_dispatch` | Ephemeral PostgreSQL 16 container and SQLite connector integration tests | `contents: read` |
| [`schema-regression.yml`](../../.github/workflows/schema-regression.yml) | `DERA \| Schema Regression` | `push`, `pull_request`, `workflow_dispatch` | Deterministic SHA-256 fingerprinting and topological sort stability | `contents: read` |
| [`sqlite-compatibility.yml`](../../.github/workflows/sqlite-compatibility.yml) | `DERA \| SQLite Runtime Compatibility` | `push`, `pull_request`, `workflow_dispatch` | SQLite 3 connector validation across supported Python runtimes | `contents: read` |
| [`docker.yml`](../../.github/workflows/docker.yml) | `DERA \| Docker Validation` | `push`, `pull_request`, `workflow_dispatch` | Multi-stage image build validation and non-root execution (UID 10001) | `contents: read` |
| [`mutation.yml`](../../.github/workflows/mutation.yml) | `DERA \| Mutation Sweep` | `schedule` (weekly), `workflow_dispatch` | Mutation testing baseline for DAG algorithms and diagnostic rules | `contents: read` |
| [`release.yml`](../../.github/workflows/release.yml) | `DERA \| Release` | `push` (`v*.*.*` tags), `workflow_dispatch` | Semantic version build, sdist/wheel packaging, SHA-256 manifest generation | `contents: write` |
| [`release-recovery.yml`](../../.github/workflows/release-recovery.yml) | `DERA \| Release Recovery` | `workflow_dispatch` | Post-release audit, commit verification, and checksum manifest validation | `contents: read` |
| [`ci-performance.yml`](../../.github/workflows/ci-performance.yml) | `DERA \| CI Performance` | `schedule` (weekly), `workflow_dispatch` | Workflow execution duration, queue delay, and success rate tracking | `actions: read`, `contents: read` |
| [`cache-maintenance.yml`](../../.github/workflows/cache-maintenance.yml) | `DERA \| Cache Maintenance` | `schedule` (weekly), `workflow_dispatch` | Actions cache storage utilization audit and retention monitoring | `actions: read`, `contents: read` |

---

## 2. Granular Workflow Specifications

### `ci.yml` (Primary CI Gate)
* **Execution Environment:** `ubuntu-latest`
* **Concurrency:** `ci-${{ github.workflow }}-${{ github.ref }}` with cancellation for outdated PR pushes.
* **Matrix:** Python 3.12 and 3.13; Node.js 22 LTS.
* **Required Jobs for Merge:** `CI Gate` (`ci-gate`).

### `codeql.yml` (Advanced SAST)
* **Execution Environment:** `ubuntu-latest`
* **Languages Analyzed:** `python`, `javascript-typescript`, `actions`.
* **Queries:** `security-extended`.
* **Output:** SARIF uploaded to GitHub Security tab and preserved as artifact.

### `database-integration.yml`
* **Services:** Disposable `postgres:16-alpine` container on port 5432 with health check probe (`pg_isready`).
* **Isolation:** Ephemeral in-memory SQLite and containerized PostgreSQL; zero access to external production databases.
