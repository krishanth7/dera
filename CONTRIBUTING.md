# Contributing to DERA

> **Project:** DERA — Database Engineering & Reverse Analysis  
> **Tagline:** Understand Every Schema. Engineer Every Change.  
> **Repository:** [https://github.com/krishanth7/dera](https://github.com/krishanth7/dera)  
> **Maintainer:** Krishanth (`krishanth7`)  
> **License:** [MIT License](LICENSE)  

Welcome! Thank you for taking the time to contribute to **DERA**.

DERA is an open-source platform dedicated to deterministic database reverse engineering, schema visualization, and architectural diagnostics. We welcome contributions from database engineers, software developers, technical writers, security researchers, and open-source enthusiasts worldwide.

---

## Quick Navigation

| What do you want to do? | Recommended Starting Point |
|---|---|
| **Make your first contribution** | [First Contribution Guide](docs/community/FIRST_CONTRIBUTION.md) |
| **Find open tasks & skill areas** | [Contribution Areas Map](docs/community/CONTRIBUTION_AREAS.md) |
| **Ask questions or propose ideas** | [GitHub Discussions Guide](docs/community/DISCUSSIONS_GUIDE.md) |
| **Read common questions** | [Contributor FAQ](docs/community/CONTRIBUTOR_FAQ.md) |
| **Learn git branching & PR rules** | [Contribution Workflow](docs/development/CONTRIBUTION_WORKFLOW.md) |
| **Author or edit documentation** | [Documentation Style Guide](docs/development/DOCUMENTATION_STYLE_GUIDE.md) |
| **Translate documentation** | [Translating Documentation Guide](docs/i18n/CONTRIBUTING_TRANSLATIONS.md) |
| **Validate documentation locally** | [Documentation Validation Guide](docs/development/DOCUMENTATION_VALIDATION.md) |
| **Report a security vulnerability** | [Root Security Policy](SECURITY.md) |

---

## 1. Code of Conduct

All contributors and participants must adhere to our [Code of Conduct](CODE_OF_CONDUCT.md). We are committed to providing a welcoming, inclusive, and harassment-free community for everyone.

---

## 2. Core Engineering Principles

Before contributing code or architecture specifications, please review DERA's foundational engineering invariants:

1. **Strict Non-AI Policy:** DERA is completely deterministic at runtime. We never introduce LLMs, generative AI APIs, vector embeddings, or probabilistic recommendations into core algorithms or database inspection routines.
2. **Read-Only Database Safety:** Database connectors must enforce strict session-level read-only directives (`SET TRANSACTION READ ONLY`) backed by static query mutation blocking (`DROP`, `ALTER`, etc.). Never extract customer table row-data.
3. **Hermetic Testing:** Tests must execute fully offline without requiring external network connectivity or cloud accounts.
4. **Authoritative English Source:** English is the authoritative source for all technical documentation. Localizations across our **ten official languages** (`en`, `es`, `fr`, `de`, `pt`, `it`, `ja`, `ko`, `zh-CN`, `ru`) synchronize with English.

---

## 3. Ways to Contribute

- **Report Bugs:** Open a structured report via [GitHub Issues](https://github.com/krishanth7/dera/issues/new?template=bug_report.yml).
- **Propose Features:** For significant additions, open a discussion in [GitHub Discussions](https://github.com/krishanth7/dera/discussions) before writing code.
- **Improve Documentation:** Fix typos directly via the GitHub web editor or submit comprehensive tutorials and architecture specifications.
- **Translate Documentation:** Help maintain our 10 official README translations in [`docs/i18n/`](docs/i18n/).
- **Implement Dialect Connectors:** Expand read-only system catalog extractors for supported relational databases.
- **Strengthen Test Coverage:** Add edge-case schemas, cycle benchmarks, and cross-platform verification fixtures.

---

## 4. Development Setup & Verification

DERA uses a cross-platform Python development CLI (`scripts/development/dev.py`) to keep local commands reproducible across Windows, Linux, and macOS.

```bash
# 1. Clone your fork
git clone https://github.com/YOUR_USERNAME/dera.git
cd dera

# 2. Add upstream remote
git remote add upstream https://github.com/krishanth7/dera.git

# 3. Install dependencies
npm install

# 4. Run the full validation suite
python scripts/development/dev.py all
```

### Essential Local Commands

| Command | Action |
|---|---|
| `python scripts/development/dev.py test` | Runs unit, integration, and regression test suites. |
| `python scripts/development/dev.py typecheck` | Executes TypeScript static typecheck (`tsc --noEmit`). |
| `npm run docs:check` | Runs Markdown linting, internal links, mermaid, and i18n checks. |
| `python scripts/development/dev.py all` | Runs complete baseline (compile, tests, typecheck, docs). |

---

## 5. Branching & Commit Conventions

DERA requires clean, bisectable Git history using [Conventional Commits](https://www.conventionalcommits.org/):

```text
type(scope): concise description in lowercase
```

### Allowed Branch Prefixes
- `feat/` — New features, models, or connectors
- `fix/` — Bug fixes or calculation corrections
- `docs/` — Documentation additions or translation improvements
- `test/` — Adding or updating test suites
- `ci/` — CI/CD workflows and automated quality gates
- `refactor/` — Code refactoring without behavioral changes

For full specifications and examples, see [Commit Conventions](docs/development/COMMIT_CONVENTIONS.md).

---

## 6. Pull Request Process

1. **Keep PRs Focused:** Small, single-purpose pull requests are reviewed and integrated much faster than massive multi-feature changes.
2. **Complete the PR Template:** Fill out all sections in [`.github/PULL_REQUEST_TEMPLATE.md`](.github/PULL_REQUEST_TEMPLATE.md), confirming non-AI adherence, test execution, and security safety.
3. **Verify Passing Checks:** Ensure all automated GitHub Actions checks pass.
4. **Review & Integration:** Maintainers review submissions within **3 to 5 business days**. Once approved, changes are squash-merged into `main`.

---

## 7. Security Disclosures

Do **not** report security vulnerabilities or sensitive credentials via public GitHub issues.

Privately disclose security concerns via:
- [GitHub Private Vulnerability Reporting](https://github.com/krishanth7/dera/security/advisories/new)
- Direct security contact: `krishanth.b.2008@gmail.com`

Review our [Root Security Policy](SECURITY.md) and [Vulnerability Response Plan](docs/security/VULNERABILITY_RESPONSE.md).

---

## 8. License & Attribution

By submitting a contribution to DERA, you agree that your contribution is provided under the terms of the [MIT License](LICENSE). Contributor copyright remains with the author, and all contributors are credited in the repository's Git history and release notes.

Thank you for helping make DERA the premier deterministic database engineering platform!
