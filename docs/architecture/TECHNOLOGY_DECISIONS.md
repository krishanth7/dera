# DERA Technology Decisions & Architecture Rationale

> **Project:** DERA — Database Engineering & Reverse Analysis  
> **Maintainer:** Krishanth  
> **Status:** Authoritative Technology Specification  
> **Last Verified:** 2026-10-26 (Commit `e550fdd`)  

---

## 1. Overview & Verification Standard

This document records the technology stack decisions made in the DERA platform. In accordance with DERA's engineering standard, every technology choice is classified by its actual implementation status in the codebase, its specific architectural role, documented selection rationale, evaluated alternatives, current limitations, and future considerations.

Where an architectural rationale was not formally documented in early commits, it is explicitly classified as **Undocumented** rather than retroactively fabricated.

---

## 2. Technology Evaluation & Decision Matrix

### 2.1 Python
- **Implementation Status:** **Implemented & Active**.
- **Version:** Python `3.12+` (tested and running on Python `3.13` in local Windows environment).
- **Architectural Role:** Primary runtime for core domain primitives, graph theory algorithms, diagnostic linting, and database connector introspection.
- **Selection Rationale:** Python provides a robust standard library with built-in dataclasses, graph manipulation capabilities, comprehensive hashing algorithms (`hashlib`), and cross-platform native database drivers.
- **Alternatives Evaluated:** Rust, Go. (Rationale noted in project foundation: Python chosen for rapid algorithmic prototyping, rich database adapter ecosystem, and accessibility for data engineers).
- **Current Limitations:** Python is single-threaded by default via the GIL; CPU-intensive graph traversal on massive schemas (e.g., >10,000 tables) may require process pooling or future Rust extensions.
- **Future Considerations:** Evaluate PyO3/Rust bindings in Phase 6 for high-throughput topological sorting on very large schemas.

### 2.2 FastAPI
- **Implementation Status:** **Implemented & Active**.
- **Version:** `fastapi>=0.110.0` with `uvicorn>=0.28.0` and `pydantic>=2.6.0`.
- **Architectural Role:** Lightweight HTTP gateway in `apps/api` exposing health telemetry, platform metadata, and future introspection endpoints.
- **Selection Rationale:** High asynchronous performance, native Pydantic schema validation, automatic OpenAPI documentation generation (`/docs`), and clean middleware integration.
- **Alternatives Evaluated:** Flask, Django Ninja, Starlette-alone. FastAPI was selected for standard OpenAPI compliance and minimal boilerplate.
- **Current Limitations:** Currently operating as a minimal gateway scaffold; live schema inspection endpoints are not yet registered.
- **Future Considerations:** Implement modular sub-routers for schema inspection, comparison, and export.

### 2.3 TypeScript
- **Implementation Status:** **Implemented & Active**.
- **Version:** TypeScript `5.x` (configured via root `tsconfig.json` and package configs).
- **Architectural Role:** Primary language for shared contracts (`packages/contracts`) and frontend visualization studio (`apps/web`).
- **Selection Rationale:** Static type safety, structural typing matching JSON schema definitions, rich browser ecosystem, and deep integration with React/Next.js.
- **Alternatives Evaluated:** Pure JavaScript. JavaScript was rejected due to lack of compile-time contract verification.
- **Current Limitations:** Type generation between Python dataclasses and TypeScript interfaces is currently maintained by hand rather than automatically compiled.
- **Future Considerations:** Explore automated bidirectional schema generators (`datamodel-code-generator` or `json-schema-to-typescript`).

### 2.4 React & Next.js
- **Implementation Status:** **Scaffold Active (Implemented)**.
- **Version:** Next.js `15.x`, React `19.x`.
- **Architectural Role:** Frontend studio application in `apps/web`.
- **Selection Rationale:** Server-side rendering, App Router modular layout, fast build tooling, and rich visual ecosystem for interactive diagrams.
- **Alternatives Evaluated:** Vite + React SPA, Svelte, Vue. Next.js was selected for seamless monorepo workspace integration and hybrid static/SSR capabilities.
- **Current Limitations:** Currently renders platform foundation status dashboard; interactive ER diagram canvas (React Flow) is planned for Phase 7.
- **Future Considerations:** Integrate `@xyflow/react` (React Flow) for visual schema topology rendering.

### 2.5 SQLite
- **Implementation Status:** **Implemented & Active**.
- **Version:** Python standard library `sqlite3` (SQLite 3.x).
- **Architectural Role:** Primary reference database for zero-dependency local testing, integration test fixtures, and prototype catalog introspection.
- **Selection Rationale:** Zero configuration, embedded execution, cross-platform portability across Windows, Linux, and macOS without requiring Docker or network daemons.
- **Alternatives Evaluated:** In-memory mocks. SQLite was selected because real relational database catalogs provide genuine relational constraint testing.
- **Current Limitations:** SQLite has a simplified type affinity system and does not implement full ANSI information_schema catalogs.
- **Future Considerations:** Continue utilizing SQLite as the default offline test fixture engine.

### 2.6 PostgreSQL
- **Implementation Status:** **Integration Verified via Ephemeral Fixtures / Planned for Live Adapter**.
- **Architectural Role:** Target database dialect for enterprise schema reverse-engineering and relational constraint analysis.
- **Selection Rationale:** Dominant open-source enterprise relational database with extensive catalog views (`pg_catalog`, `information_schema`), advanced constraint mechanisms, and partitioned table structures.
- **Alternatives Evaluated:** None; PostgreSQL is a mandatory target engine for DERA.
- **Current Limitations:** Live connector in `packages/connectors/src/dera_connectors/postgresql/` is in development; verified in test suite via ephemeral test fixtures.
- **Future Considerations:** Implement full PostgreSQL adapter in Phase 5 utilizing `psycopg` (binary) with strict `SET TRANSACTION READ ONLY;`.

### 2.7 SQLAlchemy
- **Implementation Status:** **Evaluated & Explicitly Omitted from Core**.
- **Architectural Role:** None in core runtime.
- **Selection Rationale / Rejection:** DERA deliberately avoids SQLAlchemy as an ORM in `packages/core`. DERA's objective is database reverse analysis and raw catalog introspection, not object-relational mapping. Directly querying catalog tables ensures total control over SQL queries and eliminates ORM overhead and abstraction mismatches.
- **Alternatives Evaluated:** SQLAlchemy Core. May be used in optional migration utility scripts in later phases, but core domain models remain pure Python dataclasses.

### 2.8 Docker & Containerization
- **Implementation Status:** **Active in CI / Repository Root**.
- **Architectural Role:** Reproducible test execution environments in GitHub Actions and containerized deployment blueprints.
- **Selection Rationale:** Uniform execution across different developer environments and host operating systems.
- **Current Limitations:** Local development runner (`dev.py`) operates natively without requiring Docker, keeping onboarding friction low.

### 2.9 GitHub Actions
- **Implementation Status:** **Implemented & Active (18 Workflows)**.
- **Architectural Role:** Complete DevSecOps automation, testing, security scanning (Bandit, CodeQL, Dependency Review), documentation validation, and language synchronization.
- **Selection Rationale:** Native GitHub integration, zero external CI infrastructure cost, fine-grained secret management, and branch protection checks.
- **Current Limitations:** Third-party GitHub Actions must be pinned to immutable commit SHAs for supply chain security (enforced in Phase 1.4/1.5).

---

## 3. Related Architecture Specifications

- [System Architecture Overview](SYSTEM_OVERVIEW.md)
- [Monorepo Structure](MONOREPO_STRUCTURE.md)
- [Module Boundaries](MODULE_BOUNDARIES.md)
- [Architecture Decision Records (ADRs)](adr/README.md)
