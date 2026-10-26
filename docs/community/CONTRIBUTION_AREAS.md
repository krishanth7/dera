# DERA Contribution Areas & Opportunity Map

> **Project:** DERA — Database Engineering & Reverse Analysis  
> **Tagline:** Understand Every Schema. Engineer Every Change.  
> **Maintainer:** Krishanth (`krishanth7`)  
> **Parent Guide:** [`CONTRIBUTING.md`](../../CONTRIBUTING.md)  

---

## 1. Overview

DERA is a modular database engineering and reverse-analysis platform. Because the project spans database catalog introspection, deterministic graph algorithms, an HTTP gateway, TypeScript contracts, a web studio, and multilingual documentation, there are opportunities for contributors with diverse skills and backgrounds.

To help contributors find impactful work, this guide categorizes available contribution areas and distinguishes **currently active opportunities** from **future roadmap phases**.

---

## 2. Contribution Areas Overview

| Domain | Primary Technologies | Current Availability | Issue Labels | Primary Documentation |
|---|---|:---:|---|---|
| **Documentation & Guides** | Markdown, Mermaid | **Active** | `documentation` | [`docs/development/DOCUMENTATION_STYLE_GUIDE.md`](../development/DOCUMENTATION_STYLE_GUIDE.md) |
| **International Translations** | Markdown, UTF-8 | **Active** | `i18n`, `documentation` | [`docs/i18n/CONTRIBUTING_TRANSLATIONS.md`](../i18n/CONTRIBUTING_TRANSLATIONS.md) |
| **Automated Testing & QA** | Python `unittest`, pytest | **Active** | `test` | [`docs/development/TESTING.md`](../development/TESTING.md) |
| **Database Connectors** | Python, SQL Catalogs | **Active** | `connectors`, `database` | [`docs/connectors/CONNECTOR_ARCHITECTURE.md`](../connectors/CONNECTOR_ARCHITECTURE.md) |
| **Core DAG & Models** | Python, NetworkX, AST | **Active** | `core`, `algorithms` | [`docs/core/README.md`](../core/README.md) |
| **API Gateway & Middleware** | FastAPI, Pydantic v2 | **Active** | `api`, `backend` | [`docs/backend/APPLICATION_ARCHITECTURE.md`](../backend/APPLICATION_ARCHITECTURE.md) |
| **Contracts & Schemas** | TypeScript, JSON Schema | **Active** | `contracts`, `typescript` | [`packages/contracts/`](../../packages/contracts/) |
| **Security & Hardening** | Python, Bandit, CodeQL | **Active** | `security` | [`docs/security/README.md`](../security/README.md) |
| **Accessibility (a11y)** | Semantic HTML, ARIA | **Active** | `accessibility` | [`docs/frontend/APPLICATION_ARCHITECTURE.md`](../frontend/APPLICATION_ARCHITECTURE.md) |
| **DevSecOps & Tooling** | GitHub Actions, Shell | **Active** | `ci`, `devops` | [`docs/ci/README.md`](../ci/README.md) |
| **Web Studio (React Flow)** | Next.js 15, React Flow | Planned (Phase 7) | `frontend`, `studio` | [`docs/frontend/APPLICATION_ARCHITECTURE.md`](../frontend/APPLICATION_ARCHITECTURE.md) |
| **Schema Diff Engine** | Python, AST SQLGlot | Planned (Phase 9) | `diff`, `migrations` | [`docs/roadmap/README.md`](../roadmap/README.md) |

---

## 3. Detailed Contribution Domains

### 3.1 Technical Documentation & Developer Experience
- **Focus:** Expanding architectural guides, writing database connector tutorials, improving developer setup documentation, and verifying code examples.
- **Good For:** Technical writers, educators, and developers getting familiar with the platform.
- **Key Invariant:** Strict truth-in-documentation. Clearly distinguish implemented features from planned roadmap capabilities.

### 3.2 Multilingual Translations
- **Focus:** Maintaining synchronization between the authoritative English documentation and our **ten official languages**:
  `en`, `es`, `fr`, `de`, `pt`, `it`, `ja`, `ko`, `zh-CN`, `ru`.
- **Good For:** Bilingual and multilingual developers, technical translators.
- **Key Invariant:** Do not translate code fences, CLI commands, or programming identifiers. Strictly adhere to [`docs/i18n/languages.json`](../i18n/languages.json).

### 3.3 Database Connectors & Catalog Inspection
- **Focus:** Implementing and hardening read-only system catalog inspection routines for supported database engines:
  - SQLite (`sqlite_master`, PRAGMAs)
  - PostgreSQL (`pg_catalog`, `information_schema`)
  - MySQL / MariaDB (Beta v0.2.0)
- **Good For:** Database administrators, SQL specialists, backend engineers.
- **Key Invariant:** **Strict read-only safety**. Connectors must enforce `SET TRANSACTION READ ONLY`, static query mutation blocks (`DROP`, `ALTER`, `INSERT`, `UPDATE`, `DELETE`), and zero customer row-data extraction.

### 3.4 Core Deterministic Algorithms
- **Focus:** Enhancing canonical schema data structures, foreign-key dependency graphs, topological sorting, and cycle detection (Tarjan SCC).
- **Good For:** Algorithm enthusiasts, Python software engineers, graph theory specialists.
- **Key Invariant:** **Strict Non-AI Policy**. All algorithms must be deterministic, reproducible, and explainable without probabilistic heuristics or neural models.

### 3.5 API Gateway & Services
- **Focus:** Expanding REST endpoints in `apps/api` for schema snapshot upload, graph export, and diagnostic evaluation.
- **Good For:** Python/FastAPI backend developers.
- **Key Invariant:** Loopback interface binding defaults (`127.0.0.1`), structured domain exceptions, and non-AI telemetry.

### 3.6 Automated Testing & Test Baseline
- **Focus:** Expanding unit tests, regression tests, edge-case catalog parsing fixtures, and cross-platform compatibility suites.
- **Good For:** QA engineers, test automation specialists.
- **Key Invariant:** Zero external network dependencies. Tests must run fully hermetic and fast (< 1s locally).

---

## 4. Planned Future Contribution Areas (Roadmap)

The following areas are defined in DERA's master roadmap but are not yet open for implementation. Contributors are invited to participate in architecture discussions on GitHub Discussions prior to milestone openings:
- **Phase 7: Visual ER Studio Canvas** (Interactive React Flow schema visualization canvas)
- **Phase 8: Deterministic Diagnostics Rule Engine** (Missing PK, unindexed FK rule matrix)
- **Phase 9: Snapshot Diff & Migration Preview** (Semantic schema delta generator)
- **Phase 10: SQL AST Performance & Query Complexity** (SQLGlot query analyzer)

---

## 5. Getting Assigned to an Issue

1. Visit [GitHub Issues](https://github.com/krishanth7/dera/issues).
2. Filter by label (e.g. `is:issue is:open label:"good first issue"`).
3. Post a comment expressing your intent to work on the issue.
4. Wait for maintainer confirmation or assignment before starting major work to avoid duplicate effort.
