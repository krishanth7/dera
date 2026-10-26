# DERA Monorepo Architecture & Directory Structure

> **Project:** DERA — Database Engineering & Reverse Analysis  
> **Maintainer:** Krishanth  
> **Status:** Authoritative Repository Specification  
> **Last Verified:** 2026-10-26 (Commit `e550fdd`)  

---

## 1. Monorepo Architectural Philosophy

DERA is organized as a **Modular Monolith** within a single version-controlled repository. This structure balances cross-module development velocity with strict encapsulation and dependency boundaries.

Key architectural motivations for this structure:
1. **Atomic Cross-Stack Commits:** Core model changes, shared contracts, connector updates, and frontend presentations can be developed and validated in a single atomic Git pull request.
2. **Unified Continuous Integration:** A single CI pipeline tests Python byte-compilation, unit tests, TypeScript typechecks, documentation link integrity, and security gates simultaneously.
3. **Decoupled Packaging:** Packages under `packages/` maintain independent package manifests (`pyproject.toml` or `package.json`) allowing future independent publication if demanded.

---

## 2. Directory Layout Overview

```
dera/
├── .github/                      # GitHub configuration, issue templates, and CI/CD workflows
├── apps/                         # Deployable application workspaces
│   ├── api/                      # FastAPI REST HTTP gateway service
│   └── web/                      # Next.js 15 studio and schema visualization interface
├── packages/                     # Reusable engineering libraries
│   ├── connectors/               # Read-only database introspection adapters
│   ├── contracts/                # Cross-language schema contracts (TypeScript & JSON Schema)
│   └── core/                     # Pure Python domain models, graph algorithms, and diagnostics
├── tests/                        # Multi-tier automated test suites
│   ├── architecture/             # Module boundary and Zero-AI enforcement tests
│   ├── docs/                     # Language navigation and documentation parity tests
│   ├── integration/              # Real-world SQLite and ephemeral database integration tests
│   ├── regression/               # Deterministic DAG and hash stability tests
│   └── unit/                     # Fast in-memory unit tests for core primitives and API routes
├── scripts/                      # Developer CLI runners and CI automation tools
│   ├── ci/                       # Automated PR readiness, title, and documentation validators
│   ├── development/              # Cross-platform runner (dev.py)
│   └── docs/                     # Multi-language navigation generator
├── docs/                         # Enterprise technical documentation knowledge base
│   ├── architecture/             # System overview, monorepo design, ADRs, module boundaries
│   ├── audit/                    # Baseline and sub-phase audit and acceptance reports
│   ├── backend/                  # FastAPI gateway architecture and API contracts
│   ├── connectors/               # Connector architecture and database capability matrix
│   ├── contracts/                # Shared data contracts and schema definitions
│   ├── core/                     # Domain models, graph algorithms, and deterministic design
│   ├── development/              # Getting started, commands, testing, and troubleshooting
│   ├── frontend/                 # Next.js architecture and UI component reference
│   ├── i18n/                     # 10-language documentation translations and navigation manifest
│   └── security/                 # Threat model, database security, and vulnerability policies
├── .env.example                  # Sanitized environment variable configuration template
├── Makefile                      # Standard UNIX development target interface
├── package.json                  # Root npm workspace configuration
├── pyproject.toml                # Root Python packaging and test configuration
├── README.md                     # Authoritative English landing page and 10-language navigation
└── tsconfig.json                 # Root TypeScript compilation and alias mapping
```

---

## 3. Detailed Workspace & Package Specifications

### 3.1 `packages/core` — Deterministic Domain & Graph Engine
- **Purpose:** Houses canonical database schema domain primitives, mathematical graph algorithms, rule-based diagnostic linting, and SHA-256 fingerprinting.
- **Languages & Runtimes:** Python 3.12+ (Pure Standard Library).
- **Public Interface:**
  - Models: `DatabaseTable` (alias `Table`), `DatabaseColumn` (alias `Column`), `PrimaryKeyConstraint`, `ForeignKeyConstraint` (alias `ForeignKey`), `TableIndex` (alias `Index`), `SchemaSnapshot`.
  - Graph: `build_dependency_graph(tables)`, `compute_topological_sort(tables)`.
  - Diagnostics: `evaluate_missing_primary_keys(tables)`, `evaluate_unindexed_foreign_keys(tables)`, `run_all_diagnostics(tables)`.
  - Exceptions: `DeraError`, `SchemaParsingError`, `CycleDetectedError`, `DiagnosticRuleError`, `ReadOnlyViolationError`.
- **Internal Responsibilities:** Canonical schema normalization, deterministic Kahn's topological sort, Tarjan strongly connected components cycle detection, rule evaluation, hash computation.
- **Allowed Dependencies:** Python Standard Library only (`dataclasses`, `hashlib`, `json`, `datetime`, `typing`, `enum`, `abc`, `re`).
- **Forbidden Dependencies:** Web frameworks (`fastapi`, `starlette`), database drivers (`psycopg`, `sqlite3`), generative AI libraries (`openai`, `google.genai`, `torch`).
- **Configuration:** None (pure functional domain logic).
- **Test Location:** `tests/unit/test_models.py`, `tests/regression/test_schema_regression.py`.
- **Current Maturity:** **Implemented & Production-Ready**.
- **Extension Points:** Additional diagnostic rules in `dera.diagnostics`, new domain models in `dera.models`.

### 3.2 `packages/connectors` — Read-Only Database Adapters
- **Purpose:** Manages database connection lifecycles, enforces read-only query safety, queries database catalogs, and maps native database metadata into canonical `DatabaseTable` primitives.
- **Languages & Runtimes:** Python 3.12+.
- **Public Interface:**
  - `BaseConnector`: Abstract base class with `connect()`, `disconnect()`, `test_connection()`, `inspect_tables()`, `inspect_schema()`, and `validate_query_read_only()`.
  - `ConnectionConfig`: Immutable configuration dataclass with connection parameters and credential masking.
  - `SqliteConnector`: SQLite catalog extractor.
- **Internal Responsibilities:** Session configuration (`PRAGMA query_only = ON;`, `SET TRANSACTION READ ONLY`), dialect-specific catalog queries (`sqlite_master`, PRAGMAs, `information_schema`), static mutation interception.
- **Allowed Dependencies:** `packages/core` (`dera.models`, `dera_core.exceptions`), standard library `sqlite3`, native database drivers.
- **Forbidden Dependencies:** Web frameworks (`fastapi`, `starlette`), frontend code (`apps/web`), generative AI libraries.
- **Configuration:** `ConnectionConfig` instances populated via environment variables or API parameters.
- **Test Location:** `tests/integration/test_sqlite_connector.py`, `tests/architecture/test_module_boundaries.py`.
- **Current Maturity:** `BaseConnector` and `SqliteConnector` **Implemented**; PostgreSQL/MySQL **In Progress/Planned**.
- **Extension Points:** Implement new dialects by subclassing `BaseConnector`.

### 3.3 `packages/contracts` — Shared Cross-Language Contracts
- **Purpose:** Defines formal data transfer objects and JSON schemas to guarantee protocol parity between Python backend services and TypeScript frontend studios.
- **Languages & Runtimes:** TypeScript, JSON Schema (Draft 2020-12).
- **Public Interface:**
  - JSON Schema: `packages/contracts/schemas/schema-snapshot.json`.
  - TypeScript Types: `DatabaseColumn`, `PrimaryKeyConstraint`, `ForeignKeyConstraint`, `TableIndex`, `DatabaseTable`, `SchemaSnapshot`, `DiagnosticFinding`, `TableDependencyGraph`.
- **Internal Responsibilities:** Type definitions, serialization validation, contract versioning.
- **Allowed Dependencies:** Zero runtime dependencies.
- **Forbidden Dependencies:** Framework or transport libraries.
- **Configuration:** `package.json` with npm workspace configuration.
- **Test Location:** Verified via TypeScript compilation (`tsc --noEmit`) in `scripts/development/dev.py`.
- **Current Maturity:** **Implemented**.
- **Extension Points:** New JSON schema definitions for diagnostics and migration plans.

### 3.4 `apps/api` — FastAPI Gateway Service
- **Purpose:** HTTP gateway providing REST endpoints for system health verification, platform metadata, and future schema inspection orchestration.
- **Languages & Runtimes:** Python 3.12+, FastAPI, Uvicorn, Pydantic.
- **Public Interface:**
  - HTTP Endpoints: `GET /health`, `GET /info`, `GET /api/v1/meta`.
  - Middleware: `SecurityHeadersMiddleware`.
  - Configuration: `ApiSettings` in `dera_api.core.config`.
- **Internal Responsibilities:** HTTP routing, CORS validation, security header injection, request validation, error formatting.
- **Allowed Dependencies:** `packages/core`, `packages/connectors`, `fastapi`, `starlette`, `pydantic`, `uvicorn`.
- **Forbidden Dependencies:** Client-side frontend code (`apps/web`), generative AI libraries.
- **Configuration:** Managed via `apps/api/src/dera_api/core/config.py` using `DERA_ENV`, `DERA_API_HOST`, `DERA_API_PORT`, `DERA_CORS_ORIGINS`.
- **Test Location:** `tests/unit/test_api.py`.
- **Current Maturity:** **Scaffold Active (Implemented)**.
- **Extension Points:** Additional sub-routers for schema inspection (`/api/v1/inspect`) and diffing (`/api/v1/diff`).

### 3.5 `apps/web` — Next.js Visualization Studio
- **Purpose:** Web-based studio interface for exploring schemas, inspecting database health status, and (in future phases) rendering interactive ER diagrams.
- **Languages & Runtimes:** TypeScript, Next.js 15, React.
- **Public Interface:** Web pages and components: `HomePage`, `Navbar`, `StatusCard`, `DeraApiClient`.
- **Internal Responsibilities:** Client-side presentation, API communication, status display.
- **Allowed Dependencies:** `packages/contracts` (`@dera/contracts`), `react`, `next`.
- **Forbidden Dependencies:** Backend Python packages, raw database passwords, generative AI SDKs.
- **Configuration:** `apps/web/package.json`, `apps/web/tsconfig.json`.
- **Test Location:** Verified via static compilation (`tsc --noEmit`).
- **Current Maturity:** **Scaffold Active (Implemented)**.
- **Extension Points:** Integration of React Flow interactive canvas in Phase 7.

### 3.6 `tests/` — Automated Quality & Architecture Verification
- **Purpose:** Multi-layered test suites validating domain correctness, mathematical invariants, connector safety, documentation links, and architectural boundaries.
- **Test Suites:**
  - `tests/architecture/`: Asserts zero-AI imports, core framework independence, and mutation rejection.
  - `tests/docs/`: Asserts 10-language navigation consistency across markdown files.
  - `tests/integration/`: Validates real SQLite catalog extraction against created in-memory and disk tables.
  - `tests/regression/`: Asserts that schema snapshots compute identical SHA-256 digests across test runs.
  - `tests/unit/`: Validates domain models, Kahn's algorithm, diagnostic rules, and FastAPI endpoints.
- **Execution:** `python scripts/development/dev.py test` or `python -m unittest discover tests/`.

### 3.7 `scripts/` — Developer Tooling & Automation
- **Purpose:** Cross-platform CLI runner and CI automation scripts.
- **Components:**
  - `scripts/development/dev.py`: Cross-platform CLI runner executing build, test, typecheck, doc validation, and PR readiness.
  - `scripts/ci/validate_docs.py`: Validates internal markdown links, heading hierarchy (H1), and UTF-8 encoding.
  - `scripts/ci/validate_i18n.py`: Validates 10-language parity and canonical manifest integrity.
  - `scripts/docs/generate_language_navigation.py`: Synchronizes the 10-language navigation banner across README documents.

### 3.8 `docs/` — Technical Documentation Knowledge Base
- **Purpose:** Enterprise-grade engineering documentation covering architecture, development onboarding, security policies, multilingual translations, and audit reports.
- **Standards:** Markdown formatted, verified internal links, level-1 H1 headings, UTF-8 encoding, strictly non-AI.

### 3.9 `.github/` — DevSecOps Automation
- **Purpose:** Hosts GitHub repository configurations, issue templates, PR forms, funding links, and 18 GitHub Actions CI/CD workflows (CI, CodeQL, Bandit, Dependency Review, i18n, etc.).

---

## 4. Architectural Boundary Violations & Technical Debt

During the Phase 2.4 audit, the following architectural observations and technical debt items were recorded:

1. **Dual Core Namespace (`dera` vs `dera_core`):**
   - *Observation:* The `packages/core` directory contains both `src/dera/` (models, graph, diagnostics) and `src/dera_core/` (exceptions).
   - *Impact:* While functional and properly isolated, having two namespaces within one package creates potential confusion for new contributors.
   - *Guidance:* In Phase 3, consolidate domain exceptions into `dera.exceptions` while maintaining backward-compatible re-exports in `dera_core`.
2. **Connector Coupling with Legacy Module:**
   - *Observation:* `packages/connectors/src/dera_connectors/sqlite/connector.py` imports `dera.connectors.sqlite.SqliteConnector` for legacy table inspection.
   - *Impact:* Direct coupling between connector implementations across package boundaries.
   - *Guidance:* Re-implement SQLite catalog queries directly in `dera_connectors.sqlite` without delegating to `dera.connectors`.
3. **Frontend React Flow Canvas Status:**
   - *Observation:* Past documentation occasionally referenced visual ER diagrams as operational.
   - *Impact:* Contributor confusion regarding UI capabilities.
   - *Guidance:* Explicitly document that visual canvas components are scheduled for Phase 7.

---

## 5. Related Architecture Specifications

- [System Overview & Invariants](SYSTEM_OVERVIEW.md)
- [Module Boundaries & Dependency Rules](MODULE_BOUNDARIES.md)
- [End-to-End Introspection Data Flow](DATA_FLOW.md)
- [Technology Stack Decisions](TECHNOLOGY_DECISIONS.md)
- [Architecture Decision Records (ADRs)](adr/README.md)
