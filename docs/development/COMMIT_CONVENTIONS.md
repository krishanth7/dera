# DERA Conventional Commits Specification

> **Project:** DERA — Database Engineering & Reverse Analysis  
> **Maintainer:** Krishanth ([@krishanth7](https://github.com/krishanth7))  
> **Repository:** [https://github.com/krishanth7/dera](https://github.com/krishanth7/dera)  
> **Standard:** [Conventional Commits 1.0.0](https://www.conventionalcommits.org/en/v1.0.0/)  

---

## 1. Architectural Motivation

DERA enforces the Conventional Commits specification for all commit messages and pull request titles. This guarantees:
1. **Automated Changelogs:** Semantic commit messages allow automated tooling to generate structured release notes and changelogs.
2. **Deterministic Versioning:** Commit types directly govern Semantic Versioning (SemVer) increments (`fix` triggers a patch release, `feat` triggers a minor release, breaking changes trigger a major release).
3. **High-Signal Git History:** Contributors and maintainers can instantly understand the scope and intent of any change in git logs.
4. **Clean Squash Merging:** When pull requests are squash-merged into `main`, the validated PR title becomes the canonical commit message on `main`.

---

## 2. Standard Commit Format

Every commit message and pull request title must match the structure:

```text
<type>(<optional-scope>): <description>

[optional body]

[optional footer(s)]
```

### Breaking Changes Syntax
To declare a breaking change (such as an API contract change, schema model change, or CLI argument deprecation):
- Append an exclamation mark `!` immediately before the colon:
  ```text
  feat(api)!: revise schema snapshot response data contract
  ```
- Or include a `BREAKING CHANGE:` footer block in the commit body:
  ```text
  feat(api): revise schema snapshot response data contract

  BREAKING CHANGE: The `database_id` field has been renamed to `connection_id`.
  ```

---

## 3. Allowed Commit Types

| Type | SemVer Impact | Description & Purpose |
|---|---|---|
| `feat` | **Minor** (`0.x.0`) | New deterministic capability, public API route, core model, or database connector |
| `fix` | **Patch** (`0.0.x`) | Bug fix, error resolution, calculation fix, or boundary validation repair |
| `docs` | None / Metadata | Documentation additions, fixes, guides, or internationalization translations |
| `refactor` | None | Internal code restructuring with zero functional, behavior, or API changes |
| `perf` | **Patch** (`0.0.x`) | Measurable performance optimization, memory footprint reduction, or DAG speedup |
| `test` | None | Adding missing tests, correcting regressions, or expanding coverage |
| `build` | None | Changes to packaging metadata (`pyproject.toml`, `package.json`), compilers, or bundlers |
| `ci` | None | GitHub Actions workflows, DevSecOps gates, security linters, or CI scripts |
| `chore` | None | Housekeeping, formatting, temporary file cleanup, or tool configuration |
| `revert` | **Patch** (`0.0.x`) | Reverting a previous commit that introduced an issue |
| `security` | **Patch** (`0.0.x`) | Security hardening, loopback enforcement, or permission checks |
| `deps` | None / **Patch** | Dependency updates, lockfile updates, or version bumps |

---

## 4. Standard Scopes

Scopes provide contextual precision regarding which monorepo package or application is affected:

| Scope | Area of Monorepo | Concrete Example |
|---|---|---|
| `core` | `packages/core` | `feat(core): introduce schema snapshot hash fingerprinting` |
| `connectors` | `packages/connectors` | `feat(connectors): add PostgreSQL foreign key discovery` |
| `contracts` | `packages/contracts` | `feat(contracts): publish schema snapshot JSON schema v1` |
| `api` | `apps/api` | `fix(api): handle missing database credentials with 401 response` |
| `web` | `apps/web` | `feat(web): render accessible ER diagram navigation toolbar` |
| `repo` | Monorepo root | `chore(repo): configure unified editorconfig and gitattributes` |
| `i18n` | `docs/i18n` | `docs(i18n): update French and Spanish README translations` |
| `deps` | Package dependencies | `deps(npm): bump typescript compiler to latest stable` |
| `actions` | `.github/workflows` | `ci(actions): pin GitHub Actions to immutable SHAs` |
| `security` | DevSecOps & Security | `security(api): enforce strict loopback 127.0.0.1 default host` |

---

## 5. Comprehensive Examples

### Standard Feature
```text
feat(connectors): implement SQLite table and index introspection

Extracts table names, column types, nullability, default expressions,
and foreign key constraints directly from sqlite_master without table locks.
```

### Bug Fix
```text
fix(graph): resolve recursion depth issue in cyclic foreign keys

Implements Tarjan's strongly connected components algorithm to
detect circular references deterministically and prevent infinite loops.
```

### Breaking Change
```text
feat(core)!: redesign canonical column type hierarchy

BREAKING CHANGE: Deprecates `DataType.TEXT` in favor of typed `SqlType.VARCHAR`
and `SqlType.TEXT` to support vendor-specific precision and length attributes.
```

### Security Enhancement
```text
security(connectors): block mutation statements during read-only inspection

Adds static AST validation to reject queries containing DROP, TRUNCATE,
ALTER, INSERT, UPDATE, DELETE, or GRANT statements before execution.
```

---

## 6. Local Validation

Contributors can validate any commit message or PR title string locally using the DERA development CLI:

```bash
# Validating a PR or commit title
python scripts/development/dev.py validate-title "feat(core): introduce canonical models"

# Automated hook installation (optional)
python scripts/development/dev.py install-hooks
```
