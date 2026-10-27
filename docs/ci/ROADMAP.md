# DERA CI/CD & Automation Roadmap

This document outlines active, in-progress, and deferred GitHub Actions workflows as the DERA platform expands.

---

## 1. Active Workflows (Authoritative & Specialized)

The active workflow suites are fully verified and maintained:
* **Authoritative Main CI:** `ci.yml` (consolidates Python matrix, frontend, contracts, database integration, and docs)
* **Security:** `codeql.yml`, `dependency-review.yml`, `security-tests.yml`
* **Governance:** `pr-title.yml`, `pr-readiness.yml`
* **Documentation & i18n:** `documentation.yml`, `i18n.yml`, `external-links.yml`
* **Database & Engine:** `schema-regression.yml`, `sqlite-compatibility.yml`
* **Packaging & Container:** `docker.yml`, `release.yml`, `release-recovery.yml`
* **Reliability & Maintenance:** `mutation.yml`, `ci-performance.yml`, `cache-maintenance.yml`, `issue-triage.yml`

---

## 2. Deferred Workflows & Implementation Prerequisites

To ensure integrity and avoid superficial or non-functional workflows, the following pipelines are intentionally deferred until their genuine platform components are developed:

### 1. `pages.yml` (Documentation Static Site Deployment)
* **Status:** Deferred
* **Prerequisite:** Introduction of a static documentation generator (e.g., MkDocs Material, VitePress, or Docusaurus).
* **Rationale:** DERA currently maintains clean, GitHub-rendered Markdown across `README.md` and `docs/i18n/`. Deploying an empty GitHub Pages shell without a configured SSG is avoided.
* **Planned Capabilities:** Multi-language documentation build, localized search indexing, automated preview deployments on PRs.

### 2. `mysql-integration.yml` / `mariadb-integration.yml`
* **Status:** Deferred
* **Prerequisite:** Completion of `packages/core/src/dera/connectors/mysql.py`.
* **Planned Capabilities:** Ephemeral MySQL 8.0 and MariaDB 11.x service containers, testing information_schema catalog extraction, character sets, and collation metadata.

### 3. `sqlserver-integration.yml`
* **Status:** Deferred
* **Prerequisite:** Completion of `packages/core/src/dera/connectors/sqlserver.py`.
* **Planned Capabilities:** SQL Server 2022 Linux container testing for sys catalog tables, schema-qualified objects, and identity columns.

### 4. `benchmark-harness.yml`
* **Status:** Deferred
* **Prerequisite:** Large-scale synthetic schema generator (1,000+ tables, 50,000+ foreign keys).
* **Planned Capabilities:** Memory profiling and execution timing regressions for DAG topological sort and cycle resolution.
