# DERA Module Boundaries & Architectural Dependency Rules

> **Phase:** 1.2 Monorepo Architecture Foundation  
> **Status:** Active Architectural Standard  
> **Enforcement:** Automated via [`tests/architecture/test_module_boundaries.py`](../../tests/architecture/test_module_boundaries.py)  


---

## 1. Architectural Dependency Hierarchy

DERA enforces a strict unidirectional dependency hierarchy. Code at lower layers must never import or depend upon code from higher layers.

```mermaid
graph TD
    APPS_WEB[apps/web (Next.js UI)]
    APPS_API[apps/api (FastAPI Gateway)]
    PKG_CONTRACTS[packages/contracts (TypeScript)]
    PKG_CONNECTORS[packages/connectors (Python Database Adapters)]
    PKG_CORE[packages/core (Python Canonical Engine)]

    APPS_WEB --> PKG_CONTRACTS
    APPS_API --> PKG_CONTRACTS
    APPS_API --> PKG_CONNECTORS
    APPS_API --> PKG_CORE
    PKG_CONNECTORS --> PKG_CORE

    classDef core fill:#e1f5fe,stroke:#0288d1,stroke-width:2px;
    classDef conn fill:#e8f5e9,stroke:#388e3c,stroke-width:2px;
    classDef app fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px;
    class PKG_CORE core;
    class PKG_CONNECTORS conn;
    class APPS_WEB,APPS_API app;
```

---

## 2. Forbidden Import Matrix

The following imports are strictly forbidden and will fail architectural linting and CI gate checks:

| Source Package | Forbidden Import Targets | Rationale |
|---|---|---|
| `packages/core` | `fastapi`, `starlette`, `apps/api`, `apps/web` | Core domain must remain a pure, transport-independent library. |
| `packages/core` | Concrete connectors (`psycopg`, `mysql`, `snowflake`) | Core models must be decoupled from specific database drivers. |
| `packages/core` | Generative AI (`openai`, `google.genai`, `anthropic`, `torch`) | Strict platform non-AI requirement. |
| `packages/connectors` | `apps/api`, `apps/web`, `fastapi` | Connectors must remain callable from CLI or standalone scripts. |
| `apps/web` | Backend database credentials (`NEXT_PUBLIC_*PASSWORD*`) | Database credentials must never leak into client-side JavaScript bundles. |
| Any module | Circular imports across package boundaries | Circular dependencies break modularity and static analysis. |

---

## 3. Contribution Guide: How to Extend DERA

### A. How to Add a New Database Connector
1. Create a dedicated directory under `packages/connectors/src/dera_connectors/<dialect>/` (e.g. `postgresql`).
2. Inherit from `BaseConnector` in `dera_connectors.base.connector`.
3. Implement required abstract methods:
   - `connect()`: Enforce read-only transaction parameters (e.g., `SET TRANSACTION READ ONLY`).
   - `disconnect()`: Release connection pool resources safely.
   - `test_connection() -> bool`: Validate connectivity and catalog read privileges.
   - `inspect_tables() -> List[DatabaseTable]`: Query system catalog views (`information_schema` or engine-specific metadata).
4. Add integration tests under `tests/integration/test_<dialect>_connector.py`.
5. Re-export the connector in `packages/connectors/src/dera_connectors/__init__.py`.

### B. How to Add a New Diagnostic Rule
1. Navigate to `packages/core/src/dera/diagnostics.py`.
2. Inherit from `SchemaRule` and implement:
   - `rule_id`: Unique uppercase string identifier (e.g. `RULE_003_OVERINDEXED_TABLE`).
   - `severity`: Value of `RuleSeverity` (`INFO`, `WARNING`, `ERROR`, `CRITICAL`).
   - `description`: Plain-language explanation of the structural anti-pattern.
   - `evaluate(table: DatabaseTable) -> Optional[DiagnosticFinding]`: Deterministic evaluation function.
3. Register the rule in `run_all_diagnostics` or the `DiagnosticEngine`.
4. Add unit test coverage in `tests/unit/test_models.py`.

### C. How to Add a New Schema Model
1. Update Python dataclasses in `packages/core/src/dera/models.py`. Ensure immutability via `@dataclass(frozen=True)`.
2. Update shared TypeScript contracts in `packages/contracts/src/index.ts` to maintain schema parity.
3. Update JSON exchange schemas in `packages/contracts/schemas/`.
4. Verify schema parity by running `python scripts/development/dev.py all`.

### D. How to Add a New API Endpoint
1. Define request and response schemas in `apps/api/src/dera_api/schemas/`.
2. Implement route handlers in `apps/api/src/dera_api/main.py` (or sub-routers).
3. Ensure all domain exceptions are mapped using `format_error_response`.
4. Add unit tests in `tests/unit/test_api.py`.

### E. How to Add a New Frontend Feature
1. Place visual components in `apps/web/src/components/` and page routes in `apps/web/src/app/`.
2. Consume API endpoints using `apps/web/src/lib/api-client.ts`.
3. Use shared TypeScript types from `@dera/contracts`.
4. Run `npx tsc --noEmit` to verify type safety.
