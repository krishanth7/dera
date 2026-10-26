# DERA Architecture & Source Code Assessment

> **Phase:** 1.1 Technical Audit  
> **Audited Commit:** [`52dcc8df395f464172ea019b3df716e36b62134f`](https://github.com/krishanth7/dera/commit/52dcc8df395f464172ea019b3df716e36b62134f)  

---

## 1. Architectural Philosophy & Constraints

DERA is engineered as a **strictly deterministic** database engineering platform. Its primary architectural directive is:
- **No Generative AI Models:** No LLM inference, OpenAI API, Gemini API, Anthropic API, Groq, or local model runtime weights.
- **Reproducibility:** All schema extraction, dependency graphs, cycle detection, and diagnostics produce 100% deterministic, bite-for-bite reproducible JSON structures given identical input catalogs.
- **Read-Only Database Safety:** Database connectors must execute strictly read-only catalog queries with zero DDL/DML mutation privileges.

---

## 2. Module-by-Module Technical Audit

### Module 1: `packages/core/src/dera/models.py`
- **Language:** Python 3.12+
- **Purpose:** Core domain primitives and immutable value objects for database entities.
- **Public Interfaces:**
  - `DataType(Enum)`: Canonical SQL data type classifications (`INTEGER`, `BIGINT`, `VARCHAR`, `TEXT`, `BOOLEAN`, `TIMESTAMP`, `JSON`, `BLOB`, `DECIMAL`, `UNKNOWN`).
  - `Column`: Immutable dataclass representing a database column (`name`, `data_type`, `nullable`, `primary_key`, `default_value`, `is_unique`).
  - `ForeignKey`: Foreign key constraint linking source table column to target table column.
  - `Index`: Table index representation (`name`, `columns`, `is_unique`).
  - `Table`: Database table representation containing columns, primary key definitions, foreign keys, and indices.
  - `SchemaSnapshot`: Aggregated schema model containing multiple tables, database dialect identifier, and creation timestamp.
- **Dependencies:** Standard library only (`dataclasses`, `enum`, `typing`). Zero external dependencies.
- **Configuration Requirements:** None.
- **Error Handling:** Dataclass type-hinting; validation occurs at construction.
- **Test Coverage:** Directly tested in `tests/unit/test_models.py::TestDeraModels::test_model_creation`.
- **Security-Sensitive Behavior:** Pure data representation; no network, I/O, or credential access.
- **Architectural Assessment:** Excellent. High cohesion, low coupling, decoupled from any specific database engine.

---

### Module 2: `packages/core/src/dera/graph.py`
- **Language:** Python 3.12+
- **Purpose:** Dependency graph construction, cycle detection, and topological sorting for database migration order.
- **Public Interfaces:**
  - `SchemaGraph`: Directed acyclic graph (DAG) builder that constructs edges based on table foreign key relationships.
  - `SchemaGraph.add_table(table: Table)`: Ingests table metadata into graph adjacency list.
  - `SchemaGraph.get_dependencies(table_name: str) -> List[str]`: Retrieves prerequisite referenced tables.
  - `SchemaGraph.topological_sort() -> List[str]`: Computes deterministic table creation order using in-degree reduction (Kahn's algorithm). Raises `ValueError` upon cycle detection.
  - `SchemaGraph.find_cycles() -> List[List[str]]`: Identifies strongly connected components and circular dependency paths using Tarjan's algorithm.
- **Dependencies:** Standard library only (`typing`, `collections`).
- **Configuration Requirements:** None.
- **Error Handling:** Clear exception raising (`ValueError` on cycles during topological sort).
- **Test Coverage:** Tested in `tests/unit/test_models.py::TestDeraModels::test_graph_topological_sort` and `test_graph_cycle_detection`.
- **Security-Sensitive Behavior:** Pure algorithmic in-memory processing. Guaranteed finite termination with $O(V + E)$ complexity.
- **Architectural Assessment:** Clean, mathematical separation of graph theory from schema ingestion.

---

### Module 3: `packages/core/src/dera/diagnostics.py`
- **Language:** Python 3.12+
- **Purpose:** Rule-based diagnostic engine for identifying schema anti-patterns and performance risks.
- **Public Interfaces:**
  - `DiagnosticSeverity(Enum)`: `INFO`, `WARNING`, `ERROR`, `CRITICAL`.
  - `DiagnosticFinding`: Value object representing an issue (`rule_id`, `table_name`, `severity`, `message`, `remediation`).
  - `SchemaRule(ABC)`: Abstract base class for all deterministic rules.
  - `MissingPrimaryKeyRule(SchemaRule)`: Emits `ERROR` for tables without a declared primary key.
  - `UnindexedForeignKeyRule(SchemaRule)`: Emits `WARNING` for foreign key columns lacking a supporting index.
  - `DiagnosticEngine`: Registry and execution pipeline that evaluates registered rules against a `SchemaSnapshot`.
- **Dependencies:** Standard library only (`abc`, `enum`, `dataclasses`, `typing`).
- **Configuration Requirements:** Extensible rule registry.
- **Error Handling:** Isolated execution; individual rule evaluations are side-effect free.
- **Test Coverage:** Tested in `tests/unit/test_models.py::TestDeraModels::test_diagnostics_engine`.
- **Security-Sensitive Behavior:** Safe read-only evaluation.
- **Architectural Assessment:** Excellent adherence to the Open-Closed Principle (OCP); new rules can be added without modifying the engine.

---

### Module 4: `apps/api/src/dera_api/main.py`
- **Language:** Python 3.12+
- **Purpose:** REST API gateway for exposing deterministic schema analysis to web consumers.
- **Public Interfaces:**
  - `GET /health`: System liveness and deterministic engine readiness check.
  - `GET /api/v1/meta`: Engine metadata and zero-AI platform declaration.
- **Dependencies:** `fastapi`, `pydantic`.
- **Configuration Requirements:** Optional port/host environment variables.
- **Error Handling:** FastAPI standard HTTPException handling.
- **Test Coverage:** Tested in `tests/unit/test_api.py::TestApi::test_health_endpoint` (skipped when FastAPI is not locally installed).
- **Security-Sensitive Behavior:** Network listener. Needs CORS hardening, rate limiting, and request payload size caps in Phase 4.
- **Architectural Assessment:** Clean decoupling from core domain logic.

---

### Module 5: `packages/contracts/src/index.ts`
- **Language:** TypeScript 5.x
- **Purpose:** Shared data contracts for frontend and external API consumers.
- **Public Interfaces:**
  - `DataType`: String union matching Python `DataType`.
  - `ColumnContract`, `ForeignKeyContract`, `IndexContract`, `TableContract`, `SchemaSnapshotContract`: TypeScript interfaces matching Python models.
  - `DiagnosticFindingContract`: Type definition for diagnostic findings.
- **Dependencies:** None.
- **Configuration Requirements:** None.
- **Test Coverage:** Verified via `npx -p typescript tsc --noEmit`.
- **Architectural Assessment:** Enables end-to-end type safety between Python backend and Next.js frontend without code duplication.

---

## 3. Structural Architectural Evaluation

| Evaluation Criteria | Current Status | Assessment & Observations |
|---|---|---|
| **Separation of Concerns** | **Strong** | Domain models (`core/models.py`), algorithms (`core/graph.py`), rules (`core/diagnostics.py`), and HTTP transport (`apps/api`) are strictly separated into discrete modules. |
| **Modularity** | **Good** | Core libraries have zero third-party dependencies, allowing them to run in embedded CLI, WASM, or server environments. |
| **Dependency Direction** | **Inverted / Clean** | `apps/api` depends on `packages/core`. `packages/core` depends on nothing outside Python stdlib. |
| **Maintainability** | **High** | High clarity, strict type annotations, standard docstrings, and simple dataclasses. |
| **Testability** | **High** | All core functions are pure and stateless, enabling fast unit testing without mocking or database containers. |
| **Connector Isolation** | **Foundation Stage** | Connector architecture must be formally isolated into `packages/connectors/` with explicit abstract interfaces (`DatabaseConnector`) in Phase 1.2 and Phase 5. |
| **Database Safety Boundaries** | **Strong Intent** | System design strictly forbids DDL execution against target databases; all reverse engineering is read-only. Formal catalog query whitelisting needed. |

---

## 4. Current Architecture vs. Proposed Monorepo Architecture

```mermaid
graph TD
    subgraph Current Baseline (Phase 1.1)
        A[apps/api] --> B[packages/core]
        C[apps/web] -.-> D[packages/contracts]
    end

    subgraph Proposed Target Architecture (Phase 1.2+)
        API[apps/api (FastAPI)] --> CORE[packages/core]
        CLI[apps/cli] --> CORE
        WEB[apps/web (Next.js / React Flow)] --> CONTRACTS[packages/contracts]
        API --> CONTRACTS
        
        CORE --> PARSER[packages/sql-parser (SQLGlot)]
        CORE --> CONNECTORS[packages/connectors]
        CORE --> DIFF[packages/diff]
        
        CONNECTORS --> PG[PostgreSQL Adapter (psycopg)]
        CONNECTORS --> SQLITE[SQLite Adapter]
        CONNECTORS --> MYSQL[MySQL Adapter]
    end
```
