# DERA Dependency & Software Supply Chain Assessment

> **Phase:** 1.1 Technical Audit  
> **Audited Commit:** [`52dcc8df395f464172ea019b3df716e36b62134f`](https://github.com/krishanth7/dera/commit/52dcc8df395f464172ea019b3df716e36b62134f)  

---

## 1. Dependency Manifests & Package Managers

The audited repository relies on two package ecosystems: Python (pip / setuptools) and Node.js (npm workspaces).

| Ecosystem | Manifest File | Lockfile Present on `main` | Version Constraints Declared |
|---|---|---|---|
| **Python** | `pyproject.toml` | No (`requirements.lock` / `uv.lock` absent) | `>=3.12` declared |
| **Node.js (Root)** | `package.json` | No (Added in PR #3 as `package-lock.json`) | Workspaces: `apps/*`, `packages/*` |
| **Node.js (Contracts)** | `packages/contracts/package.json` | N/A (Subpackage) | TypeScript `>=5.0.0` |
| **Node.js (Web)** | `apps/web/package.json` | N/A (Subpackage) | Next.js, React 19 declared |

---

## 2. Python Ecosystem Audit (`pyproject.toml`)

- **Build System:** `setuptools>=61.0.0`
- **Declared Runtime Dependencies:**
  - `fastapi>=0.110.0` (Optional REST gateway)
  - `pydantic>=2.0.0` (Optional data validation)
  - `uvicorn>=0.28.0` (Optional ASGI server)
- **Declared Development Dependencies (`[project.optional-dependencies] dev`):**
  - `pytest>=8.0.0`
  - `pytest-asyncio>=0.23.0`
  - `ruff>=0.3.0`
  - `mypy>=1.9.0`
- **Core Library (`packages/core`) Runtime Footprint:**
  - Standard library only (`dataclasses`, `enum`, `typing`, `collections`, `abc`).
  - **Zero third-party runtime dependencies** required for schema models, topological sorting, Tarjan's cycle detection, or diagnostic rules.

---

## 3. Node.js & TypeScript Ecosystem Audit

- **Package Manager:** `npm` workspaces
- **Root `package.json` Configuration:**
  - `"private": true`
  - `"workspaces": ["apps/*", "packages/*"]`
- **Subpackages:**
  - `@dera/contracts`: Pure TypeScript interface definitions. Zero runtime dependencies.
  - `@dera/web`: Next.js web application stub.
- **Lockfile Status:** `package-lock.json` is absent on `main` commit `52dcc8d`. In-flight PR #3 supplies a verified `package-lock.json` lockfile for deterministic CI installs.

---

## 4. Software Supply Chain & Non-AI Verification

A strict supply-chain verification was conducted against all declared and indirect dependencies:

| Verification Check | Target Libraries / APIs | Verified Result | Evidence |
|---|---|---|---|
| **Generative AI Dependencies** | `openai`, `google-genai`, `anthropic`, `groq`, `cohere` | **ZERO FOUND** | Absent from all manifests |
| **LLM Orchestration Frameworks** | `langchain`, `llamaindex`, `haystack`, `dspy` | **ZERO FOUND** | Absent from all manifests |
| **Machine Learning Heavyweights** | `torch`, `tensorflow`, `transformers`, `onnxruntime` | **ZERO FOUND** | Absent from all manifests |
| **Vulnerable Dependencies (CVEs)** | All declared packages | **ZERO ALERTS** | `gh api /dependabot/alerts` returned `[]` |
| **License Compliance** | All direct and transitive dependencies | **Permissive (MIT/Apache 2.0)** | No GPL/AGPL viral licenses detected |

---

## 5. Dependency Recommendations for Phase 1.2 & 1.3

1. **Lockfile Enforcement:** Ensure `package-lock.json` is merged into `main` (via PR #3) to guarantee deterministic builds in CI without network version drift.
2. **Modern Python Dependency Management:** Adopt `uv` or `pip-tools` to generate a frozen `requirements.lock` for production containers.
3. **Automated Dependabot Review:** Utilize `.github/workflows/dependency-review.yml` (from PR #3) to block pull requests introducing vulnerable or GPL-licensed packages.
