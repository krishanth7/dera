# Documentation Change Policy

**Project:** DERA — Database Engineering & Reverse Analysis  
**Repository:** [https://github.com/krishanth7/dera](https://github.com/krishanth7/dera)  
**Lead Maintainer:** [Krishanth](https://github.com/krishanth7)  
**License:** [MIT License](../../LICENSE)  

---

## 1. Purpose & Scope

In DERA, documentation is treated as a first-class engineering artifact. When software behavior changes without corresponding documentation updates, technical drift occurs, eroding developer trust and increasing support overhead.

This policy defines the documentation obligations triggered by engineering changes to the DERA monorepo, including:
- Core algorithms (`packages/core`)
- Database connectors (`packages/connectors`)
- HTTP and RPC APIs (`apps/api`)
- Web visualization frontend (`apps/web`)
- Shared schemas and contracts (`packages/contracts`)
- CLI scripts and workflows (`scripts/development/dev.py`)

---

## 2. Change Categories & Documentation Obligations

When submitting a pull request that introduces or alters software behavior, contributors must update the corresponding documentation files detailed below:

| Change Category | Triggering Events | Required Documentation Updates | Authoritative Target Paths |
|---|---|---|---|
| **New API Endpoints** | Adding FastAPI routes or RPC operations | Document route path, HTTP method, request/response schema, query parameters, error responses, and deterministic guarantees. | `docs/architecture/API_SPECIFICATION.md`<br>`packages/contracts/` |
| **Modified API Contracts** | Renaming parameters, changing types, altering pagination | Update JSON Schema / Pydantic models, document backwards compatibility or breaking changes. | `packages/contracts/README.md`<br>`docs/architecture/` |
| **New Database Connectors** | Adding support for PostgreSQL, MySQL, SQLite, etc. | Document catalog queries used, supported dialect versions, driver requirements, and update the Compatibility Matrix. | `docs/connectors/<DIALECT>.md`<br>`README.md` (Compatibility Matrix)<br>`docs/i18n/README.*.md` |
| **Schema Model Changes** | Altering relational model abstractions (tables, columns, indexes, foreign keys) | Update model documentation, Mermaid ER diagrams, and core data contract specs. | `docs/architecture/DATA_MODELS.md`<br>`packages/core/README.md` |
| **CLI Changes** | Adding/modifying subcommands, flags, or default parameters in `dev.py` | Update usage examples, help flags, and developer command references. | `docs/development/COMMANDS.md`<br>`docs/development/CONTRIBUTION_WORKFLOW.md` |
| **Configuration Changes** | New environment variables, config files, or default port/host changes | Document variable name, allowed values, secure default (e.g., `127.0.0.1`), and update `.env.example`. | `docs/development/CONFIGURATION.md`<br>`.env.example` |
| **Security Changes** | Modifying authentication, permission models, or security policies | Document security implications, defensive invariants, and update vulnerability process if applicable. | `docs/security/DATABASE_SECURITY.md`<br>`SECURITY.md` |
| **Dependency Upgrades** | Adding new runtime dependencies or updating major versions | Verify license compatibility (MIT-compatible), document rationale, update lockfiles and dependency guides. | `pyproject.toml`<br>`package.json`<br>`docs/development/SETUP.md` |
| **Breaking Changes** | Incompatible API changes, dropped DB version support, altered CLI behavior | Provide a dedicated migration section, before/after examples, and deprecation notices. | `docs/roadmap/BREAKING_CHANGES.md`<br>`CHANGELOG.md` |
| **Deprecations** | Flagging a feature or parameter for future removal | Add clear deprecation warnings with planned sunset version and recommended alternatives. | Affected doc files + `CHANGELOG.md` |
| **Releases** | Tagging minor, major, or patch release versions | Compile changelog entries, verify installation instructions, and assess translation impact. | `CHANGELOG.md`<br>`docs/governance/RELEASE_DOCUMENTATION.md` |

---

## 3. Pull Request Synchronization Expectations

### 3.1 Atomic Updates (Feature + Docs)
Feature implementations and their corresponding technical documentation should ideally be delivered in the same pull request. This ensures that:
- Code review and documentation review occur concurrently.
- Git history maintains 1:1 synchronization between software capability and documented reality.
- New features are immediately usable upon being merged into `main`.

### 3.2 Proportionality Principle
Documentation requirements must remain proportional to the scale of the change:
- **Typo fix or comment clarification:** No additional documentation updates needed.
- **Internal refactor with no public API change:** Update internal docstrings or inline comments if applicable; no user-facing documentation changes required.
- **New public function or CLI flag:** Update relevant markdown guides and help strings.
- **Architectural overhaul or new connector:** Comprehensive documentation, diagram update, and compatibility matrix adjustment required.

### 3.3 Translation Synchronization
- Contributors submitting code or English documentation changes are **not required** to translate prose into the other nine supported languages (`es`, `fr`, `de`, `pt`, `it`, `ja`, `ko`, `zh-CN`, `ru`).
- If an English update modifies the **Feature Status Matrix**, **Database Compatibility Matrix**, or **Security Invariants**, the maintainers will track translation updates via a follow-up translation tracking issue as described in [Translation Maintenance](../i18n/TRANSLATION_MAINTENANCE.md).

---

## 4. Policy on Pre-Existing Documentation Debt

To maintain an inviting and fair contributor experience:
- **Never block a PR for unrelated pre-existing debt:** A contributor improving SQLite index extraction should not be required to fix unrelated formatting issues in the PostgreSQL connector guide or write missing architecture guides for other modules.
- **Scope discipline:** Reviewers should only request documentation updates directly related to the code changes introduced in the pull request.
- **Debt logging:** If pre-existing documentation debt is identified during review, maintainers should file a new issue labeled `type/docs` with `good first issue` or `help wanted` rather than holding the current PR hostage.

---

## 5. Verification Checklist for Contributors

Before requesting review on a pull request that alters repository behavior, verify:

- [ ] Technical documentation in `docs/` reflects newly introduced or modified behavior.
- [ ] Code examples and CLI commands are tested and executable.
- [ ] All internal Markdown links are valid (`npm run docs:links` or `python scripts/ci/validate_docs.py`).
- [ ] Markdown style standards are satisfied (`npm run lint:docs`).
- [ ] No unverified claims of performance, certifications, or production readiness are made.
