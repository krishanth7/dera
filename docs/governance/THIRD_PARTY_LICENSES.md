# Third-Party License Inventory & Compliance

**Project:** DERA — Database Engineering & Reverse Analysis  
**Repository:** [https://github.com/krishanth7/dera](https://github.com/krishanth7/dera)  
**Primary License:** [MIT License](../../LICENSE)  
**Maintainer:** [Krishanth](https://github.com/krishanth7)  
**Last Verified:** October 2026

---

## 1. Compliance Overview

DERA is released under the permissive [MIT License](../../LICENSE). To ensure intellectual property integrity, software supply chain security, and unencumbered open-source distribution, all dependencies, tooling, and bundled assets must comply with permissive, open-source licensing models.

### Policy Invariants

1. **Permissive Licensing Requirement:** All runtime and direct dependencies must use permissive licenses compatible with MIT (e.g., MIT, Apache 2.0, BSD-2-Clause, BSD-3-Clause, ISC, PSF).
2. **Copyleft Incompatibility:** No strong copyleft dependencies (e.g., GPL v2/v3, AGPL v3) are permitted in runtime packages (`packages/core`, `packages/connectors`, `packages/contracts`, `apps/api`, `apps/web`) to ensure DERA remains embeddable and cleanly distributable.
3. **No Proprietary or Restrictive Assets:** No commercial, royalty-bearing, or non-commercial-only (NC) assets may be bundled or required for core functionality.
4. **Deterministic Non-AI Mandate:** Zero runtime dependencies on external AI inference SDKs, generative model runtimes, or proprietary cloud inference APIs (OpenAI, Anthropic, Google Gemini, Groq).

---

## 2. Direct Runtime Dependencies

### 2.1 Python Dependencies (`pyproject.toml`)

| Package | Version Constraint | License | SPDX Identifier | Compatibility with MIT | Verified Source |
|---|---|---|---|---|---|
| `pydantic` | `>=2.0.0` | MIT License | `MIT` | Fully Compatible | [pydantic/pydantic](https://github.com/pydantic/pydantic) |
| `networkx` | `>=3.0` | 3-Clause BSD | `BSD-3-Clause` | Fully Compatible | [networkx/networkx](https://github.com/networkx/networkx) |
| `sqlglot` | `>=20.0.0` | MIT License | `MIT` | Fully Compatible | [tobymao/sqlglot](https://github.com/tobymao/sqlglot) |
| `fastapi` | `>=0.110.0` | MIT License | `MIT` | Fully Compatible | [fastapi/fastapi](https://github.com/fastapi/fastapi) |
| `uvicorn` | `>=0.28.0` | 3-Clause BSD | `BSD-3-Clause` | Fully Compatible | [encode/uvicorn](https://github.com/encode/uvicorn) |

### 2.2 TypeScript & Web Dependencies (`apps/web/package.json`, `packages/contracts/package.json`)

| Package | Version Constraint | License | SPDX Identifier | Compatibility with MIT | Verified Source |
|---|---|---|---|---|---|
| `@dera/contracts` | `^0.1.0-dev` | MIT License | `MIT` | Internal Package | `packages/contracts` |
| `typescript` | `^5.4.0` | Apache 2.0 | `Apache-2.0` | Fully Compatible (Dev) | [microsoft/TypeScript](https://github.com/microsoft/TypeScript) |

---

## 3. Development, Build & CI Tooling

The following tools are used strictly in development environments, static analysis, and automated CI/CD pipelines. They are not bundled into distributed runtime packages.

| Tool | Purpose | License | SPDX Identifier | Verification Method |
|---|---|---|---|---|
| `ruff` | Python linting & code formatting | MIT / Apache 2.0 | `MIT OR Apache-2.0` | PyPI Metadata |
| `bandit` | Python static security analysis (SAST) | Apache 2.0 | `Apache-2.0` | PyPI Metadata |
| `prettier` | Markdown & JSON code formatting | MIT License | `MIT` | npm Registry |
| `setuptools` | Python packaging and build backend | MIT License | `MIT` | PyPI Metadata |
| `CodeQL` | GitHub semantic code analysis engine | GitHub Terms / Free for OSS | N/A | GitHub Actions |

---

## 4. Bundled Assets, Fonts & Media

| Asset Category | Current Repository State | Licensing Policy |
|---|---|---|
| **Binary Fonts** | None bundled. | System fonts or standard open-source web fonts (SIL Open Font License) only. |
| **Icons & Graphics** | None bundled. | Permissive SVG icons (Feather, Lucide, or Heroicons under MIT) only. |
| **Sample Datasets / Fixtures** | Synthetic SQL DDL scripts (`fixtures/`). | Authored under project MIT License. No proprietary schemas. |
| **Documentation Media** | GitHub Mermaid diagrams (plain text). | Authored under project MIT License. |

---

## 5. Third-Party Code Attribution

At this stage of development (Phase 1), DERA contains **zero copied third-party source files or vendored code**. All codebase files have been authored natively under the project's MIT License by repository contributors.

If third-party code snippets or algorithms are incorporated in future phases:
1. The original copyright header and license notice must be preserved at the top of the file.
2. The code origin and license type must be registered in this document.
3. The license must be compatible with the MIT License.

---

## 6. Automated Compliance & Vulnerability Scanning

Supply chain hygiene and dependency vulnerabilities are monitored continuously:
- **Dependabot:** Configured via [`.github/dependabot.yml`](../../.github/dependabot.yml) to inspect GitHub Actions and npm dependencies on a weekly cadence.
- **Static Security Analysis:** Enforced on every pull request via [`.github/workflows/security-tests.yml`](../../.github/workflows/security-tests.yml) running Bandit SAST.
- **CodeQL Scanning:** Automated static analysis across all pull requests via [`.github/workflows/codeql.yml`](../../.github/workflows/codeql.yml).
