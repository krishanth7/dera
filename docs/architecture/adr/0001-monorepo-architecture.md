# ADR 0001: Modular Monolith Monorepo Architecture for DERA

> **Status:** Proposed (Under Review by Maintainer Krishanth)  
> **Date:** 2026-10-26  
> **Deciders:** Principal Software Architect, DevSecOps Architect, Maintainer  
> **Technical Scope:** Repository Architecture, Module Boundaries, Package Organization  

---

## 1. Context and Problem Statement

**DERA (Database Engineering & Reverse Analysis)** is an open-source, deterministic database engineering platform. Its functional requirements encompass:
1. Deep database schema introspection and catalog metadata extraction across multiple relational and cloud database engines (PostgreSQL, SQLite, MySQL, MariaDB, Snowflake).
2. Directed acyclic graph (DAG) modeling, topological dependency sorting, and Tarjan's strongly connected components cycle detection.
3. Rule-based static diagnostic analysis (missing primary keys, unindexed foreign keys, redundant constraints).
4. Structural schema difference analysis and automated migration generation.
5. Interactive schema visualization, ER diagram rendering, and data dictionary browsing via a modern web interface.
6. A strict architectural constraint: **Zero Generative AI models, zero LLMs, zero cloud inference APIs, and zero non-deterministic runtime components**.

As DERA expands, the engineering team requires an architectural structure that enables independent development of the core mathematical algorithms, database connectors, HTTP API gateway, shared TypeScript contracts, and web visualizer without creating synchronization friction, repository sprawl, or premature distributed complexity.

---

## 2. Decision

We choose to implement a **Modular Monolith Monorepo** architecture managed through a unified Git repository containing discrete Python and TypeScript packages:

```
dera/
├── apps/
│   ├── api/          # FastAPI HTTP gateway
│   └── web/          # Next.js / React Flow web studio
├── packages/
│   ├── core/         # Deterministic domain models, DAG algorithms, diagnostics
│   ├── connectors/   # Read-only database introspection adapters (Base, SQLite, PG, etc.)
│   └── contracts/    # Shared TypeScript contracts and JSON schemas
├── tests/            # Architecture, integration, regression, and unit test suites
└── infrastructure/   # Local development compose and container definitions
```

---

## 3. Alternatives Considered and Rationale

| Architecture Option | Description | Evaluation & Reasons for Rejection |
|---|---|---|
| **Single Application Repository** | All Python and web code merged into a flat layout without package isolation. | **Rejected**: Violates separation of concerns. Causes cyclic dependencies, leaks web framework primitives into core mathematical algorithms, and prevents using DERA core as a standalone CLI or embedded Python library. |
| **Multi-Repository Architecture** | Separate GitHub repositories for `dera-core`, `dera-connectors`, `dera-api`, and `dera-web`. | **Rejected**: Extreme development friction for an early-stage open-source project. Every schema contract update requires synchronized cross-repository PRs, version bumping, package publishing, and complex CI matrix coordination. |
| **Microservices Architecture** | Independent containerized services communicating over gRPC/HTTP for parsing, graph algorithms, and introspection. | **Rejected**: Premature distributed complexity. Adds network serialization overhead, distributed tracing requirements, and deployment fragility with zero performance benefits for read-only schema analysis. |
| **Modular Monolith (Selected)** | Single Git repository with strict internal boundaries, isolated packages, and unidirectional dependency rules. | **Selected**: Combines rapid cross-module development velocity with clean architectural boundaries. Enables atomic pull requests, unified CI/CD qualification, and simple local onboarding. |

---

## 4. Module Boundaries & Dependency Flow

The modular monolith enforces a strict unidirectional dependency hierarchy:

```mermaid
graph TD
    WEB[apps/web (Next.js)] --> CONTRACTS[packages/contracts (TypeScript)]
    API[apps/api (FastAPI)] --> CONTRACTS
    API --> CONNECTORS[packages/connectors (Python)]
    API --> CORE[packages/core (Python)]
    CONNECTORS --> CORE
    
    subgraph Zero AI Boundary
        CORE
        CONNECTORS
        CONTRACTS
    end
```

### Key Architectural Rules
1. **Framework Independence of Core:** `packages/core` must never import `fastapi`, `starlette`, React, Next.js, or external database network drivers. It depends solely on standard Python libraries.
2. **Connector Decoupling:** Connectors depend on `packages/core` models and interfaces, but `packages/core` must never depend on concrete connector implementations.
3. **Read-Only Database Safety:** Connectors enforce read-only execution modes (`SET TRANSACTION READ ONLY` / `PRAGMA query_only = ON`). Any SQL mutation (`DROP`, `ALTER`, `TRUNCATE`, `INSERT`, `UPDATE`, `DELETE`) is intercepted and rejected by static query validators before transmission.
4. **Credential Security:** Database credentials must never be passed to or stored in `apps/web` client state. All introspection occurs server-side via `apps/api` and `packages/connectors`.

---

## 5. Consequences & Operational Implications

### Positive Consequences
- **Atomic Pull Requests:** Features touching contracts, backend models, and frontend views can be submitted, tested, and reviewed in a single atomic Git commit.
- **Unified DevSecOps:** A single automated CI pipeline validates Python tests, TypeScript compilation, documentation parity, and security scanning on every pull request.
- **Developer Velocity:** New contributors can clone a single repository and run the entire platform locally using standard Python and Node tooling (`python scripts/development/dev.py all`).
- **Zero-AI Guarantee:** Enforced globally through automated architectural boundary tests (`tests/architecture/test_module_boundaries.py`).

### Negative Consequences / Trade-offs
- **Monorepo Tooling Coordination:** Requires coordinating both Python (`pyproject.toml`) and Node.js (`package.json`) package managers in the same repository.
- **Repository Size Growth:** Over time, as database fixtures and frontend assets accumulate, Git repository size requires monitoring.

---

## 6. Future Migration Considerations

If specific components (such as `packages/core` or `packages/connectors`) achieve high external demand as standalone libraries (e.g. for PyPI distribution), their clear directory and dependency boundaries allow them to be extracted or published as independent distribution packages with zero code refactoring.
