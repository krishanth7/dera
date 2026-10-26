**Read this documentation in:** [English](README.md) | [Español](docs/i18n/README.es.md) | [Français](docs/i18n/README.fr.md) | [Deutsch](docs/i18n/README.de.md) | [Português](docs/i18n/README.pt.md) | [日本語](docs/i18n/README.ja.md) | [한국어](docs/i18n/README.ko.md) | [简体中文](docs/i18n/README.zh-CN.md) | [العربية](docs/i18n/README.ar.md) | [Русский](docs/i18n/README.ru.md)

---

<div align="center">

# DERA

### Database Engineering & Reverse Analysis

**Understand Every Schema. Engineer Every Change.**

An enterprise-grade open-source, deterministic database reverse-engineering platform for software engineers, database architects, and engineering teams.

Explore database structures, reconstruct entity relationships, evaluate structural risks, and track schema migrations — completely deterministic, without AI models or external inference APIs.

<br/>

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg?style=for-the-badge)](LICENSE)
[![CI Gate](https://img.shields.io/github/actions/workflow/status/krishanth7/dera/ci.yml?branch=main&label=CI%20Gate&style=for-the-badge&logo=githubactions)](https://github.com/krishanth7/dera/actions/workflows/ci.yml)
[![CodeQL Security](https://img.shields.io/github/actions/workflow/status/krishanth7/dera/codeql.yml?branch=main&label=CodeQL&style=for-the-badge&logo=githubactions)](https://github.com/krishanth7/dera/actions/workflows/codeql.yml)
[![Documentation](https://img.shields.io/github/actions/workflow/status/krishanth7/dera/documentation.yml?branch=main&label=Docs&style=for-the-badge&logo=githubactions)](https://github.com/krishanth7/dera/actions/workflows/documentation.yml)
[![Python 3.12 | 3.13](https://img.shields.io/badge/Python-3.12%20%7C%203.13-3776AB?style=for-the-badge&logo=python&logoColor=white)](pyproject.toml)
[![TypeScript](https://img.shields.io/badge/TypeScript-Strict-3178C6?style=for-the-badge&logo=typescript&logoColor=white)](tsconfig.json)
[![Strict Non-AI](https://img.shields.io/badge/AI-None%20(Deterministic)-orange?style=for-the-badge)](#-strict-non-ai-architecture)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg?style=for-the-badge)](CONTRIBUTING.md)

<br/>

[Overview](#-overview) ·
[Feature Matrix](#-feature-status-matrix) ·
[Architecture](#-architecture-overview) ·
[Monorepo Structure](#-repository-structure) ·
[Getting Started](#-getting-started) ·
[Database Support](#-database-compatibility-matrix) ·
[Security](#-security-principles) ·
[Roadmap](#-master-roadmap) ·
[Contributing](#-contributing) ·
[Community](#-community)

</div>

---

## 🌍 Language Support

DERA provides synchronized documentation in 10 international languages. Use the navigation table below to access localized references:

| Language | Code | Documentation Link | Status |
|---|---|---|---|
| 🇬🇧 English | `en` | [English Primary (Root)](README.md) · [Synchronized Copy](docs/i18n/README.en.md) | Authoritative Reference |
| 🇪🇸 Español | `es` | [Documentación en Español](docs/i18n/README.es.md) | Full Translation |
| 🇫🇷 Français | `fr` | [Documentation en Français](docs/i18n/README.fr.md) | Full Translation |
| 🇩🇪 Deutsch | `de` | [Dokumentation auf Deutsch](docs/i18n/README.de.md) | Full Translation |
| 🇵🇹 Português | `pt` | [Documentação em Português](docs/i18n/README.pt.md) | Full Translation |
| 🇯🇵 日本語 | `ja` | [日本語ドキュメント](docs/i18n/README.ja.md) | Full Translation |
| 🇰🇷 한국어 | `ko` | [한국어 문서](docs/i18n/README.ko.md) | Full Translation |
| 🇨🇳 简体中文 | `zh-CN` | [简体中文文档](docs/i18n/README.zh-CN.md) | Full Translation |
| 🇸🇦 العربية | `ar` | [الوثائق باللغة العربية](docs/i18n/README.ar.md) | Full Translation (RTL) |
| 🇷🇺 Русский | `ru` | [Документация на русском](docs/i18n/README.ru.md) | Full Translation |

---

## 📖 Overview

Modern relational databases are the foundational backbone of software infrastructure. However, understanding an unfamiliar, evolving schema can be challenging: enterprise systems often encompass hundreds of tables, thousands of columns, intricate foreign-key dependencies, composite indexes, and cascading constraints.

Auditing and understanding these structures manually requires substantial engineering effort and is prone to human oversight.

**DERA is engineered to solve this challenge.**

DERA provides a unified, secure workspace for exploring database architecture, reconstructing entity relationships, evaluating structural risks, and tracking schema migrations through purely deterministic algorithms.

### Core Engineering Principles

1. **Deterministic by Design:** Reproducible analysis using mathematical graph algorithms and static rules.
2. **Strictly No Generative AI:** Zero LLMs, zero machine learning models, and zero external AI inference APIs.
3. **Read-Only Database Safety:** Enforced read-only connections, static mutation blockers, and catalog-only introspection.
4. **Zero Customer Row-Data Extraction:** Pure structural metadata analysis (`information_schema`, `pg_catalog`, `sqlite_master`). Table-row records are never extracted or stored.
5. **Decoupled Monorepo Architecture:** Clean separation of concerns between core algorithms, database connectors, API gateway, and visual studio.
6. **Open Source & Permissive:** Developed under the MIT license with transparent governance and evidence-based findings.

---

## 🧠 Strict Non-AI Architecture

DERA is intentionally engineered without artificial intelligence or machine learning models.

```text
┌───────────────────────────────────────────────────────────┐
│               STRICT NON-AI ARCHITECTURE                  │
│                                                           │
│   ❌  No OpenAI, Anthropic Claude, or Google Gemini       │
│   ❌  No Groq, DeepSeek, or Hosted Model APIs            │
│   ❌  No Local LLMs (Ollama, vLLM, llama.cpp)            │
│   ❌  No Stochastic Predictions or Hallucinations         │
│                                                           │
│   ✅  Native System Catalog Queries (information_schema)   │
│   ✅  Mathematical Graph Algorithms (NetworkX / Tarjan)   │
│   ✅  Abstract Syntax Tree SQL Parsers (SQLGlot)          │
│   ✅  Reproducible Static Rule Engines                    │
│   ✅  Cryptographic Hash Fingerprints (SHA-256)           │
└───────────────────────────────────────────────────────────┘
```

**Why DERA is Deterministic:**
- **Mathematical Auditability:** Every relationship, cycle warning, and diagnostic finding cites concrete catalog evidence.
- **Byte-for-Byte Reproducibility:** Running an audit on the same schema snapshot always yields identical results across all developer machines.
- **Enterprise Data Sovereignty:** Database schemas and structural topologies never leave your network to third-party model inference providers.
- **Zero Operating Overhead:** Zero token pricing, zero rate-limiting, and zero network inference latency.

---

## 📊 Feature Status Matrix

DERA maintains transparent, evidence-based feature reporting. Status reflects actual code implemented in the repository:

| Capability | Status | Implementation Evidence | Monorepo Location |
|---|---|---|---|
| **Repository Foundation & Audit** | **Implemented** | Complete baseline audit & gap analysis | [`docs/audit/`](docs/audit/README.md) |
| **Enterprise Monorepo Architecture** | **Implemented** | Modular monolith packaging (Python & TS) | [`docs/architecture/`](docs/architecture/README.md) |
| **Git Governance & Conventions** | **Implemented** | Conventional Commits, PR title & readiness | [`docs/development/`](docs/development/README.md) |
| **DevSecOps Qualification Gate** | **Implemented** | 15+ CI workflows, CodeQL, Bandit, Pytest | [`.github/workflows/`](.github/workflows/) |
| **Canonical Schema Models** | **Implemented** | `Column`, `Table`, `ForeignKey`, `Index` | [`packages/core/src/dera/models.py`](packages/core/src/dera/models.py) |
| **Dependency Graph Processing** | **Implemented** | Cycle-resistant DAG & topological sorting | [`packages/core/src/dera/graph.py`](packages/core/src/dera/graph.py) |
| **Read-Only Mutation Interceptor** | **Implemented** | Static query AST blocking destructive SQL | [`packages/connectors/src/dera_connectors/base/`](packages/connectors/src/dera_connectors/base/connector.py) |
| **SQLite Catalog Introspection** | **Implemented** | Tables, columns, PKs, FKs, index discovery | [`packages/connectors/src/dera_connectors/sqlite/`](packages/connectors/src/dera_connectors/sqlite/connector.py) |
| **PostgreSQL Catalog Connector** | **In Progress** | Ephemeral PostgreSQL service integration | [`tests/integration/`](tests/integration/) |
| **API Gateway & Health Telemetry** | **Implemented** | FastAPI service with loopback defaults | [`apps/api/src/dera_api/main.py`](apps/api/src/dera_api/main.py) |
| **Web Studio Application Base** | **Implemented** | Next.js 15 TypeScript base & status card | [`apps/web/src/app/page.tsx`](apps/web/src/app/page.tsx) |
| **Visual ER Studio Canvas** | Planned | React Flow interactive diagram canvas | Phase 7 Roadmap |
| **Deterministic Rule Matrix** | Planned | Missing PK, unindexed FK, redundant index | Phase 8 Roadmap |
| **Schema Snapshot Diff Engine** | Planned | Semantic snapshot comparison & DDL preview | Phase 9 Roadmap |
| **SQL AST Performance Analyzer** | Planned | SQLGlot query complexity & EXPLAIN viewer | Phase 10 Roadmap |

---

## 🏗️ Architecture Overview

DERA organizes its capabilities into decoupled workspaces following our [Monorepo Architecture Specification](docs/architecture/README_ARCHITECTURE.md):

```mermaid
flowchart TD
    subgraph Client_Tier["Client Presentation Tier"]
        WEB["apps/web (Next.js 15 / React / TypeScript)"]
        STUDIO["Visual ER Studio (React Flow)"]
        WEB --- STUDIO
    end

    subgraph API_Tier["Application Gateway Tier"]
        API["apps/api (FastAPI / Python 3.12+)"]
        MW["Security Middleware (127.0.0.1 default / Headers)"]
        API --- MW
    end

    subgraph Contracts_Tier["Shared Data Contracts"]
        CONTRACTS["packages/contracts (JSON Schemas & DTOs)"]
    end

    subgraph Core_Tier["Deterministic Analysis Engine"]
        CORE["packages/core (Canonical Models & Graph Algorithms)"]
        DAG["Dependency Graph (NetworkX / Tarjan SCC)"]
        NORM["Metadata Normalizer"]
        CORE --- DAG
        CORE --- NORM
    end

    subgraph Connectors_Tier["Isolated Database Connectors"]
        CONN["packages/connectors (Read-Only Dialect Adapters)"]
        GUARD["Static Query Mutation Interceptor"]
        SQLITE["SQLite Connector (Working Baseline)"]
        PG["PostgreSQL Connector (In Progress)"]
        CONN --- GUARD
        CONN --- SQLITE
        CONN --- PG
    end

    subgraph Target_DBs["Target Data Tier (Read-Only)"]
        TARGET_SQLITE[("SQLite Database")]
        TARGET_PG[("PostgreSQL Catalogs")]
    end

    WEB -->|HTTP / JSON| API
    WEB -.->|Consumes Contracts| CONTRACTS
    API -->|Orchestrates| CORE
    API -->|Invokes| CONN
    API -.->|Validates via| CONTRACTS
    CORE -.->|Conforms to| CONTRACTS
    CONN -->|Outputs Canonical Models| CORE
    SQLITE -->|Read-Only Pragma| TARGET_SQLITE
    PG -->|Read-Only Catalogs| TARGET_PG
```

For complete technical specifications:
- [Architecture & Blueprint Guide](docs/architecture/README_ARCHITECTURE.md)
- [Module Boundaries & Dependency Rules](docs/architecture/MODULE_BOUNDARIES.md)
- [Monorepo Directory Layout](docs/architecture/MONOREPO_STRUCTURE.md)
- [Architecture Decision Record (ADR 0001)](docs/architecture/adr/0001-monorepo-architecture.md)

---

## 📁 Repository Structure

The actual monorepo layout of DERA is structured as follows:

```text
dera/
├── apps/
│   ├── api/                      # FastAPI backend application & health endpoints
│   │   ├── src/dera_api/         # Gateway routes, middleware, and schemas
│   │   └── pyproject.toml        # API packaging specification
│   └── web/                      # Next.js 15 TypeScript frontend studio
│       ├── src/                  # App router, components, and API client
│       └── package.json          # Web workspace configuration
├── packages/
│   ├── core/                     # Canonical schema models & graph processing engine
│   │   └── src/                  # Schema models, DAG algorithms, and exceptions
│   ├── connectors/               # Database-specific metadata extraction adapters
│   │   └── src/dera_connectors/  # Base connector, mutation guards, and SQLite adapter
│   └── contracts/                # Shared JSON schemas and serialization contracts
│       └── schemas/              # Versioned snapshot and API contracts
├── tests/
│   ├── architecture/             # AST import boundary & dependency tests
│   ├── integration/              # Real SQLite and PostgreSQL catalog tests
│   ├── regression/               # Deterministic DAG and hash regression tests
│   └── unit/                     # Schema model, PR title, and readiness tests
├── scripts/
│   ├── ci/                       # CI validation scripts (docs, i18n, PR title/readiness)
│   └── development/              # Unified cross-platform CLI runner (dev.py)
├── docs/
│   ├── audit/                    # Phase 1.1 repository audit and baseline reports
│   ├── architecture/             # Monorepo blueprint, boundaries, and ADRs
│   ├── development/              # Onboarding, commands, and Git workflow guides
│   ├── roadmap/                  # Master 12-Phase development roadmap
│   └── i18n/                     # Synchronized 10-language technical documentation
├── .github/
│   ├── workflows/                # Enterprise CI/CD, CodeQL, and gate automation
│   ├── ISSUE_TEMPLATE/           # Structured bug report & feature request forms
│   ├── CODEOWNERS                # Maintainer code ownership definitions
│   └── PULL_REQUEST_TEMPLATE.md  # Standardized pull request qualification template
├── .editorconfig                 # Unified indentation and whitespace rules
├── .gitattributes                # Consistent LF normalization and text handling
├── .gitignore                    # Comprehensive monorepo artifact exclusions
├── .env.example                  # Safe local development environment template
├── .pre-commit-config.yaml       # Optional local developer pre-commit hook configuration
├── Makefile                      # Standard developer command automation
├── pyproject.toml                # Root Python workspace configuration (PEP 621)
├── package.json                  # Root npm workspace configuration
└── CONTRIBUTING.md               # End-to-end contributor workflow guide
```

---

## 🚀 Getting Started

DERA provides a unified cross-platform CLI tool (`scripts/development/dev.py`) to install, verify, and run the monorepo across Windows, Linux, and macOS.

### Prerequisites

- **Python:** Version 3.12 or 3.13
- **Node.js:** LTS (v20 or v22)
- **Git:** Version 2.30+

### 1. Clone the Repository

```bash
git clone https://github.com/krishanth7/dera.git
cd dera
```

### 2. Configure Environment

Copy the safe environment template:

```bash
# Windows PowerShell
Copy-Item .env.example .env

# Linux / macOS
cp .env.example .env
```

### 3. Run the Full Validation Suite

Verify that all Python packages, TypeScript compilers, test suites, and documentation links pass:

```bash
python scripts/development/dev.py all
```

*(Output: 32 tests passing, TypeScript compiler clean, 52 docs files valid, 10 language READMEs synchronized.)*

### 4. Developer Commands Reference

| Task | Cross-Platform CLI (`dev.py`) | GNU Make (UNIX / macOS) |
|---|---|---|
| **Run all tests** | `python scripts/development/dev.py test` | `make test` |
| **Run TypeScript check** | `python scripts/development/dev.py typecheck` | `make typecheck` |
| **Byte-compile Python** | `python scripts/development/dev.py compile` | `make build` |
| **Validate documentation** | `python scripts/development/dev.py validate-docs` | `make lint` |
| **Validate PR / commit title** | `python scripts/development/dev.py validate-title "<title>"` | `make validate-title TITLE="..."` |
| **Install local Git hook** | `python scripts/development/dev.py install-hooks` | `make install-hooks` |
| **Run local API server** | `python -m uvicorn dera_api.main:app --reload --port 8000` | `make dev-api` |

For detailed onboarding instructions, consult the [Getting Started Guide](docs/development/GETTING_STARTED.md) and [Commands Catalog](docs/development/COMMANDS.md).

---

## 🗄️ Database Compatibility Matrix

DERA adopts a pluggable database connector architecture. Support levels are based on concrete implementation evidence:

| Database Engine | Version Coverage | Connector Status | Introspection Mechanism | Read-Only Enforcement |
|---|---|---|---|---|
| **SQLite** | 3.35+ | **Working Baseline** | `sqlite_master`, `PRAGMA table_info` | Static mutation guard |
| **PostgreSQL** | 12 – 17 | **In Progress** | `pg_catalog`, `information_schema` | Read-only session pragma |
| **Supabase PostgreSQL** | Cloud / Local | **In Progress** | PostgreSQL native connector | Read-only session pragma |
| **MySQL** | 8.0+ | Planned | `information_schema` | Read-only transaction |
| **MariaDB** | 10.5+ | Planned | `information_schema` | Read-only transaction |
| **Microsoft SQL Server** | 2019+ | Planned | `sys.tables`, `INFORMATION_SCHEMA` | Read-only transaction |

---

## 🔒 Security Principles

Security is the primary engineering pillar of DERA. Because the platform interacts with enterprise databases, it enforces strict defense-in-depth controls:

1. **Static Query Mutation Interceptor:** Before executing any SQL, queries pass through an AST keyword validator. Statements containing `DROP`, `ALTER`, `TRUNCATE`, `INSERT`, `UPDATE`, `DELETE`, `GRANT`, or `REVOKE` are immediately blocked.
2. **Catalog-Only Extraction:** Inspection is restricted exclusively to system metadata catalogs (`information_schema`, `pg_catalog`, `sqlite_master`). Application table-row records are never queried.
3. **Loopback Address Default:** Development servers and API endpoints bind to `127.0.0.1` by default to prevent unintended exposure to external networks.
4. **Least-Privilege Database Accounts:** DERA operates entirely using unprivileged, read-only database roles without administrative access.
5. **Zero Committed Secrets:** Credentials are never written to disk, included in version control, or logged in application traces.
6. **Responsible Disclosure:** Security vulnerabilities are handled through coordinated private reporting via our [Security Policy](SECURITY.md).

For specialized security architecture and policy documents:
- [**Database Security Policy**](docs/security/DATABASE_SECURITY.md) — Catalog-only inspection, credential encryption, and session isolation.
- [**Secure Development Standards**](docs/security/SECURE_DEVELOPMENT.md) — Pydantic input validation, parameterization, and DevSecOps gates.
- [**Vulnerability Response Process**](docs/security/VULNERABILITY_RESPONSE.md) — 5-stage triage workflow and private advisory disclosure.
- [**Threat Model Matrix**](docs/security/model.md) — Attack vector analysis and defensive mitigations.

---

## 🗺️ Master Roadmap

DERA is executing a structured **12-Phase Roadmap** to build a complete database reverse-engineering platform:

- [x] **Phase 1: Repository Foundation & Governance (Completed)**
  - [x] Phase 1.1: Complete repository audit & baseline verification
  - [x] Phase 1.2: Enterprise monorepo folder architecture (`apps/`, `packages/`)
  - [x] Phase 1.3: Git branching, Conventional Commits, and PR governance
  - [x] Phase 1.4: Professional README, project identity, and architecture diagrams
  - [x] Phase 1.5: Security policy, vulnerability reporting, and community governance
  - [x] Phase 1.6: GitHub issue forms, Discussions guide, and community operations ([Audit](docs/audit/PHASE_1_COMPLETION.md))
- [ ] **Phase 2: Multilingual Documentation & Internationalization**
- [x] **Phase 3: GitHub Actions, CI/CD & DevSecOps Automation**
- [ ] **Phase 4: Backend & Platform Infrastructure**
- [ ] **Phase 5: Database Connectors & Metadata Inspection**
- [ ] **Phase 6: Reverse Engineering Core Engine**
- [ ] **Phase 7: Frontend & Visual Engineering Studio**
- [ ] **Phase 8: Diagnostics & Schema Intelligence**
- [ ] **Phase 9: Schema Comparison & Migration Engineering**
- [ ] **Phase 10: SQL Analysis & Engineering Tools**
- [ ] **Phase 11: Enterprise Security, Reliability & Large-Scale QA**
- [ ] **Phase 12: Release, Deployment & Open-Source Growth**

For the complete milestone breakdown, timeline, and deliverables, read the [Master Development Roadmap](docs/roadmap/README.md).

---

## 🤝 Contributing

We warmly welcome contributions from software engineers, database administrators, security researchers, and technical writers worldwide!

### Contributor Resources

- **[Community Hub](docs/community/README.md):** Central community portal, discussions guide, and operational procedures.
- **[First-Time Contributor Guide](docs/community/FIRST_CONTRIBUTION.md):** Beginner-friendly walkthrough from repository setup to your first PR.
- **[Contribution Workflow](docs/development/CONTRIBUTION_WORKFLOW.md):** Complete step-by-step guide from forking to opening a qualified pull request.
- **[Discussions Guide](docs/community/DISCUSSIONS_GUIDE.md):** How to ask technical questions and propose architectural changes.
- **[Branching Strategy](docs/development/BRANCHING_STRATEGY.md):** Trunk-based development and branch naming conventions (`feat/...`, `fix/...`).
- **[Commit Conventions](docs/development/COMMIT_CONVENTIONS.md):** Conventional Commits 1.0.0 format specification and SemVer mapping.
- **[Code Review Policy](docs/development/CODE_REVIEW_POLICY.md):** Peer review criteria, code owner approval, and qualification gates.
- **[Maintainer Governance](docs/governance/MAINTAINERS.md):** Project stewardship, review SLAs, security escalation, and release authority.
- **[Third-Party License Compliance](docs/governance/THIRD_PARTY_LICENSES.md):** Open-source licensing inventory and MIT compatibility.
- **[Governance Decisions](docs/governance/GOVERNANCE_DECISIONS.md):** Formal decision records (GADs) guiding architecture and policy.
- **[Code of Conduct](CODE_OF_CONDUCT.md):** Community standards and professional conduct guidelines.

---

## 💬 Community

- [GitHub Discussions](https://github.com/krishanth7/dera/discussions) — Ask questions, share ideas, and discuss database reverse engineering.
- [GitHub Issues](https://github.com/krishanth7/dera/issues) — Report bugs or submit feature proposals.
- [GitHub Pull Requests](https://github.com/krishanth7/dera/pulls) — Submit code, test, and documentation contributions.

---

## 📜 License

DERA is distributed under the permissive **[MIT License](LICENSE)**.

```text
Copyright (c) 2026 Krishanth
```

---

## 👨‍💻 Maintainer

**Krishanth**  
Founder & Lead Maintainer

- GitHub: [@krishanth7](https://github.com/krishanth7)  
- Repository: [github.com/krishanth7/dera](https://github.com/krishanth7/dera)  
- Contact: `krishanth.b.2008@gmail.com`

*DERA is an independent open-source project maintained by Krishanth. OVIC Labs is acknowledged as part of the maintainer's broader engineering ecosystem.*

---

<div align="center">

### DERA — Database Engineering & Reverse Analysis

**Understand Every Schema. Engineer Every Change.**

*Built with mathematical determinism, engineering precision, and open-source transparency.*

© 2026 DERA Contributors. Distributed under the MIT License.

[Back to Top](#dera)

</div>
