# DERA Repository Filesystem Inventory

> **Phase:** 1.1 Technical Audit  
> **Audited Commit:** [`52dcc8df395f464172ea019b3df716e36b62134f`](https://github.com/krishanth7/dera/commit/52dcc8df395f464172ea019b3df716e36b62134f)  
> **Total Tracked Files:** 46  

---

## 1. Directory Tree Representation

Below is the verified directory structure of the repository on `main` at commit `52dcc8d`:

```
dera/
├── .github/
│   ├── ISSUE_TEMPLATE/
│   │   ├── bug_report.yml          # Structured bug report form
│   │   ├── config.yml              # Issue template configuration
│   │   ├── documentation.yml       # Documentation issue form
│   │   └── feature_request.yml     # Deterministic feature request form
│   ├── workflows/
│   │   └── codeql.yml              # CodeQL security analysis workflow
│   ├── FUNDING.yml                 # Community sponsorship configuration
│   ├── PULL_REQUEST_TEMPLATE.md    # PR submission checklist and guidance
│   └── dependabot.yml              # Weekly GitHub Actions & pip dependency scanning
├── apps/
│   ├── api/
│   │   └── src/
│   │       └── dera_api/
│   │           ├── __init__.py     # API package initialization
│   │           └── main.py         # FastAPI deterministic gateway entrypoint
│   └── web/
│       ├── package.json            # Web application package manifest
│       └── src/
│           └── index.ts            # Web studio TypeScript entrypoint stub
├── docs/
│   ├── architecture/
│   │   └── overview.md             # System architecture & non-AI deterministic design
│   ├── contributing/
│   │   └── guide.md                # Contributor setup and pull request lifecycle
│   ├── development/
│   │   └── setup.md                # Local development environment setup guide
│   ├── i18n/                       # Multilingual localized documentation (10 languages)
│   │   ├── README.ar.md            # Arabic translation (RTL formatted)
│   │   ├── README.de.md            # German translation
│   │   ├── README.en.md            # English baseline documentation
│   │   ├── README.es.md            # Spanish translation
│   │   ├── README.fr.md            # French translation
│   │   ├── README.ja.md            # Japanese translation
│   │   ├── README.ko.md            # Korean translation
│   │   ├── README.pt.md            # Portuguese translation
│   │   ├── README.ru.md            # Russian translation
│   │   └── README.zh-CN.md         # Simplified Chinese translation
│   ├── security/
│   │   └── model.md                # Security policy, credential handling, and threat model
│   └── README.md                   # Documentation navigation hub
├── packages/
│   ├── contracts/
│   │   ├── package.json            # Contract definitions package manifest
│   │   └── src/
│   │       └── index.ts            # Type definitions for schemas, tables, and relationships
│   └── core/
│       └── src/
│           └── dera/
│               ├── __init__.py     # Core library package initialization
│               ├── diagnostics.py  # Deterministic schema rule engine (missing PK, unindexed FK)
│               ├── graph.py        # Topological dependency sorting & Tarjan's cycle detection
│               └── models.py       # Dataclass models: Column, Table, ForeignKey, Schema
├── tests/
│   ├── __init__.py                 # Test root package marker
│   └── unit/
│       ├── __init__.py             # Unit test package marker
│       ├── test_api.py             # API health check test case
│       └── test_models.py          # Core models, graph sorting, and diagnostics test cases
├── .gitignore                      # Git ignore patterns for Python, Node, and IDE artifacts
├── CODE_OF_CONDUCT.md              # Contributor Covenant v2.0
├── CONTRIBUTING.md                  # Community contribution workflow and guidelines
├── LICENSE                         # MIT License text
├── package.json                    # Monorepo root npm workspace configuration
├── pyproject.toml                  # Python build metadata, packaging, and dependency definitions
├── README.md                       # Master repository README
├── SECURITY.md                     # Vulnerability disclosure policy and secure reporting channels
└── tsconfig.json                   # Root TypeScript compiler options (ES2022, strict, nodenext)
```

---

## 2. File Categories & Language Distribution

| Category | Extensions | File Count | Verified Files |
|---|---|---|---|
| **Python Source** | `.py` | 7 | `packages/core/src/dera/models.py`, `graph.py`, `diagnostics.py`, `__init__.py`, `apps/api/src/dera_api/main.py`, `__init__.py`, `tests/` |
| **TypeScript Source** | `.ts` | 2 | `packages/contracts/src/index.ts`, `apps/web/src/index.ts` |
| **Documentation** | `.md` | 21 | Root `README.md`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md`, `docs/**/*.md` |
| **CI/CD & Workflows** | `.yml` | 7 | `.github/workflows/codeql.yml`, `.github/dependabot.yml`, `.github/ISSUE_TEMPLATE/*.yml`, `.github/FUNDING.yml` |
| **Configuration & Manifests** | `.json`, `.toml` | 5 | `pyproject.toml`, `package.json`, `tsconfig.json`, `apps/web/package.json`, `packages/contracts/package.json` |
| **Project Identity** | None, `.gitignore` | 2 | `LICENSE` (MIT), `.gitignore` |
| **Total Tracked** | | **46** | |

---

## 3. Existing Source Modules vs. Proposed Future Directories

### Actual Implemented Modules (Phase 1.1 Baseline)
1. **`packages/core/src/dera/`**
   - `models.py`: Immutable schema entities (`DataType`, `Column`, `ForeignKey`, `Table`, `SchemaSnapshot`).
   - `graph.py`: Schema dependency graph DAG model, cycle detection (Tarjan's strongly connected components), topological sorting for safe migration order.
   - `diagnostics.py`: Rule-based deterministic linting (`MissingPrimaryKeyRule`, `UnindexedForeignKeyRule`).
2. **`apps/api/src/dera_api/`**
   - `main.py`: FastAPI server stub with `/health` and `/api/v1/meta` endpoints.
3. **`packages/contracts/src/`**
   - `index.ts`: TypeScript interfaces mirroring core Python entities for JSON schema exchange.
4. **`apps/web/src/`**
   - `index.ts`: UI workspace bootstrap file.

### Proposed Future Directories (To Be Established in Phase 1.2 Monorepo Architecture)
- `packages/connectors/`: Dedicated database connector abstractions and drivers (`postgres`, `sqlite`, `mysql`, `snowflake`). Note: SQLite implementation prototype exists in PR #3.
- `packages/sql-parser/`: Deterministic SQL parsing and dialect transpilation (SQLGlot integration).
- `packages/diff/`: Schema difference engine and migration script generator.
- `apps/cli/`: Standalone command-line interface tool (`dera inspect`, `dera diff`).
- `apps/web/components/`: React Flow / ELK.js schema visualization canvas and Monaco SQL editor.
- `infrastructure/`: Docker Compose, Helm charts, and Terraform definitions for production deployment.
- `scripts/`: Operational automation, linting, and build verification utilities.
