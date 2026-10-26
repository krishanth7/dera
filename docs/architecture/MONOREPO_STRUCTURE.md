# DERA Monorepo Directory Structure & Layout Specification

> **Phase:** 1.2 Monorepo Architecture Foundation  
> **Status:** Authoritative Repository Layout  

---

## 1. Directory Tree & Package Roles

```
dera/
├── .github/                       # GitHub configurations, templates, and workflows
│   ├── ISSUE_TEMPLATE/            # Structured issue submission forms (bug, feature, docs)
│   ├── workflows/                 # 18 DevSecOps GitHub Actions automation workflows
│   ├── FUNDING.yml                # Sponsorship channels
│   └── PULL_REQUEST_TEMPLATE.md   # Pull request qualification checklist
├── apps/                          # Deployable application workspaces
│   ├── api/                       # REST API gateway service (FastAPI)
│   │   ├── src/dera_api/          # Application source (core, middleware, schemas, main.py)
│   │   └── pyproject.toml         # Python packaging configuration
│   └── web/                       # Schema visualization studio (Next.js / TypeScript)
│       ├── src/                   # Web application source (app, components, lib, types)
│       ├── package.json           # Web npm workspace manifest
│       └── tsconfig.json          # Web TypeScript compiler settings
├── packages/                      # Reusable engineering libraries
│   ├── connectors/                # Read-only database introspection adapters
│   │   ├── src/dera_connectors/   # Connector source (base, sqlite, postgresql, mysql)
│   │   └── package.json           # Connector package metadata
│   ├── contracts/                 # Cross-language schema contracts
│   │   ├── schemas/               # Canonical JSON Schema definitions
│   │   ├── src/index.ts           # Type-safe TypeScript protocol interfaces
│   │   └── package.json           # Contracts npm workspace manifest
│   └── core/                      # Core domain primitives and graph algorithms
│       ├── src/                   # Core Python library source (dera, dera_core)
│       └── pyproject.toml         # Root Python build system configuration
├── tests/                         # Comprehensive multi-tier test suites
│   ├── architecture/              # Module boundary and zero-AI guarantee tests
│   ├── integration/               # Database connector integration tests (SQLite, Postgres)
│   ├── regression/                # Deterministic DAG and hash regression tests
│   └── unit/                      # Fast in-memory unit tests (models, graph, diagnostics)
├── scripts/                       # Developer CLI and CI automation utilities
│   ├── ci/                        # Automated CI validation scripts (docs, i18n, PR title)
│   └── development/               # Cross-platform development runner (dev.py)
├── docs/                          # Enterprise technical documentation
│   ├── architecture/              # System architecture, ADRs, and module boundaries
│   ├── audit/                     # 13 Phase 1.1 repository baseline audit reports
│   ├── development/               # Setup, commands, environment, and troubleshooting guides
│   ├── i18n/                      # Localized documentation across 10 languages
│   └── security/                  # Security policy and credential protection model
├── .editorconfig                  # Universal editor indentation and encoding standards
├── .env.example                   # Safe environment template with variable classifications
├── .gitattributes                 # Git text normalization and LF line-ending enforcement
├── .gitignore                     # Multi-ecosystem build and cache exclusion rules
├── Makefile                       # Standard UNIX development command interface
├── package.json                   # Root npm workspace declaration
├── pyproject.toml                 # Root Python project metadata and test configurations
├── README.md                      # Primary repository landing page and language matrix
└── tsconfig.json                  # Root TypeScript configuration and path aliases
```

---

## 2. Package Responsibilities

| Workspace / Package | Language | Key Responsibilities | Runtime External Dependencies |
|---|---|---|---|
| `packages/core` | Python 3.12+ | Canonical schema models, topological sorting, Tarjan's cycle detection, rule diagnostics | **Zero third-party runtime dependencies** (Standard library only) |
| `packages/connectors` | Python 3.12+ | Database catalog queries, read-only safety enforcement, dialect adaptation | Native Python sqlite3; future: psycopg, mysql |
| `packages/contracts` | TypeScript | Shared client-server data transfer contracts, JSON schemas | Zero runtime dependencies |
| `apps/api` | Python 3.12+ | HTTP routing, CORS, security headers, request validation | FastAPI, Pydantic, Uvicorn |
| `apps/web` | TypeScript | Interactive ER diagrams, schema visualization canvas | Next.js, React |
