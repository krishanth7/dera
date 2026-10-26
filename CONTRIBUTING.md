
# Contributing to DERA

First of all, thank you for your interest in contributing to **DERA — Database Engineering & Reverse Analysis**!

DERA is an open-source project focused on deterministic database reverse engineering, schema visualization, structural diagnostics, and database engineering tools.

We welcome contributions from developers, database engineers, designers, technical writers, testers, security researchers, and open-source enthusiasts worldwide.

Whether you are fixing a typo, reporting a bug, proposing a feature, or implementing a database connector, your contribution is valuable.

**Repository:** https://github.com/krishanth7/dera

---

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Ways to Contribute](#ways-to-contribute)
- [Before You Start](#before-you-start)
- [Development Environment](#development-environment)
- [Project Architecture](#project-architecture)
- [Development Guidelines](#development-guidelines)
- [Coding Standards](#coding-standards)
- [Testing Requirements](#testing-requirements)
- [Commit Message Guidelines](#commit-message-guidelines)
- [Pull Request Process](#pull-request-process)
- [Issue Reporting](#issue-reporting)
- [Security](#security)
- [Documentation and Translations](#documentation-and-translations)
- [Review and Maintainer Policies](#review-and-maintainer-policies)
- [Recognition](#recognition)
- [Getting Help](#getting-help)

---

## Code of Conduct

All contributors must follow our [Code of Conduct](CODE_OF_CONDUCT.md).

We are committed to maintaining a respectful, welcoming, inclusive, and professional open-source community.

Harassment, discrimination, personal attacks, and other unacceptable conduct will not be tolerated.

---

## Ways to Contribute

There are many ways to improve DERA.

### 1. Report Bugs

Found a problem?

Before submitting a bug report:

1. Search existing issues.
2. Check whether the issue has already been reported.
3. Verify that the problem is reproducible.
4. Collect relevant error messages and environment details.
5. Remove credentials and sensitive database information.

[Report a Bug](https://github.com/krishanth7/dera/issues/new)

### 2. Suggest Features

We welcome feature proposals involving:

- Database reverse engineering
- Schema discovery
- Entity-relationship diagrams
- Database connectors
- SQL parsing
- Schema comparison
- Database diagnostics
- Performance engineering
- Migration planning
- Documentation generation
- Security improvements

For major changes, start a discussion before implementation.

[Start a Discussion](https://github.com/krishanth7/dera/discussions)

### 3. Improve Documentation

Documentation contributions may include:

- Correcting errors
- Improving explanations
- Adding examples
- Writing tutorials
- Creating architecture documentation
- Updating installation instructions
- Translating documentation

### 4. Contribute Code

We welcome contributions to:

| Area | Examples |
|---|---|
| Backend | FastAPI routes, services, validation |
| Frontend | Next.js pages, React components |
| Database Connectors | PostgreSQL, MySQL, SQLite |
| Reverse Engineering | Metadata extraction and normalization |
| Graph Engine | Relationship and dependency analysis |
| Diagnostics | Deterministic rule implementations |
| Schema Diff | Snapshot comparison algorithms |
| Testing | Unit, integration, security tests |
| DevOps | Docker, CI/CD, monitoring |
| Documentation | Guides, examples, API references |

---

## Before You Start

Before beginning work:

1. Read the README.
2. Review the Code of Conduct.
3. Search existing issues and pull requests.
4. Discuss major architectural changes.
5. Confirm that your proposal aligns with the project goals.
6. Avoid duplicating work already in progress.

For substantial changes, open an issue describing:

- The problem
- The proposed solution
- Expected benefits
- Technical considerations
- Potential compatibility risks

Maintainer approval is recommended before implementing large architectural changes.

---

## Development Environment

DERA is currently under active development.

The commands below describe the intended development workflow. Some may not be available until the corresponding project components are implemented.

### Prerequisites

The planned development stack includes:

- Git
- Python 3.12+
- Node.js LTS
- PostgreSQL
- Docker
- Docker Compose

### Fork and Clone

Fork the repository and clone your fork:

```bash
git clone https://github.com/YOUR_USERNAME/dera.git
cd dera
```

Configure the upstream repository:

```bash
git remote add upstream https://github.com/krishanth7/dera.git
```

Verify your remotes:

```bash
git remote -v
```

### Create a Feature Branch

Always start from the latest default `main` branch. Detailed guidelines are in [Branching Strategy](docs/development/BRANCHING_STRATEGY.md) and [Contribution Workflow](docs/development/CONTRIBUTION_WORKFLOW.md).

```bash
git checkout main
git pull --ff-only upstream main
git checkout -b feat/your-feature-name
```

Branch naming prefixes:
- `feat/` — New capability or connector
- `fix/` — Bug fix or error resolution
- `docs/` — Documentation additions or translations
- `refactor/` — Code restructuring without functional changes
- `test/` — Unit, integration, or architecture tests
- `ci/` — CI/CD workflows and DevSecOps tooling
- `security/` — Security hardening or vulnerability fixes
- `chore/` — Tooling configuration or cleanup

Examples:
- `feat/postgresql-schema-inspection`
- `fix/composite-foreign-key`
- `docs/branching-strategy`
- `test/sqlite-dialect`

### Environment Configuration

When available, copy the provided environment template:

```bash
cp .env.example .env
```

Never commit `.env` files containing real credentials.

### Planned Local Startup

Once Docker configuration is implemented:

```bash
docker compose up --build
```

The project will document actual service URLs, ports, and startup commands after implementation.

---

## Project Architecture

DERA follows a modular architecture with independently testable components.

```text
dera/
├── apps/
│   ├── web/
│   └── api/
├── packages/
│   ├── core/
│   ├── connectors/
│   └── contracts/
├── workers/
├── tests/
├── infrastructure/
├── docs/
└── .github/
```

### Architectural Principles

Contributions should follow these principles:

1. Keep the reverse-engineering engine deterministic.
2. Avoid external AI services and LLM dependencies.
3. Separate database-specific logic from shared analysis logic.
4. Preserve database metadata accurately.
5. Use read-only database inspection by default.
6. Maintain clear module boundaries.
7. Make behavior reproducible and testable.
8. Prefer simple, maintainable solutions.
9. Document assumptions and limitations.
10. Avoid unnecessary dependencies.

---

## Development Guidelines

### Deterministic Engineering

DERA does not use generative AI models or external AI inference APIs.

Contributors must not introduce dependencies on:

- OpenAI APIs
- Anthropic Claude APIs
- Google Gemini APIs
- Groq inference APIs
- Hosted LLM services
- Local generative AI models

Use deterministic methods such as:

- SQL metadata inspection
- SQL parsing
- Graph algorithms
- Rule-based analysis
- Schema comparison
- Dependency resolution
- Database catalog queries

### Database Safety

All database-related contributions must follow secure engineering practices.

- Prefer read-only inspection.
- Never modify customer databases automatically.
- Never expose connection credentials in logs.
- Avoid collecting customer table-row data.
- Use parameterized SQL where applicable.
- Validate SQL identifiers and engine-specific syntax.
- Respect database permissions.
- Apply connection and query timeouts.
- Document database-specific limitations.

### Connector Development

New database connectors should:

1. Identify supported database versions.
2. Extract metadata using supported catalog interfaces.
3. Convert results into the canonical schema model.
4. Preserve vendor-specific metadata where necessary.
5. Report unsupported object types.
6. Handle permission errors gracefully.
7. Include integration tests.
8. Avoid destructive operations.

---

## Coding Standards

### Python

Follow:

- PEP 8
- Type annotations
- Clear module boundaries
- Meaningful names
- Structured error handling
- Dependency injection where useful
- Automated formatting and linting

Recommended tools:

- Ruff
- Pyright or mypy
- Pytest

Example:

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class DatabaseTable:
    schema: str
    name: str
    columns: tuple[str, ...]


def count_columns(table: DatabaseTable) -> int:
    return len(table.columns)
```

### TypeScript and React

Follow:

- TypeScript strict mode
- Functional React components
- Accessible UI practices
- Reusable components
- Clear separation of data and presentation
- Consistent error handling
- Avoidance of unnecessary client-side state

Recommended tools:

- ESLint
- Prettier
- TypeScript compiler
- Playwright

### SQL

SQL contributions should:

- Be readable and consistently formatted.
- Avoid unnecessary database privileges.
- Use explicit schema qualification when appropriate.
- Account for database-specific syntax.
- Include tests for supported database versions.
- Avoid relying on SQL keyword filters as the sole security control.

---

## Testing Requirements

All functional code contributions should include appropriate tests.

### Unit Tests

Test individual functions and algorithms.

Examples:

- Metadata normalization
- Foreign-key graph construction
- Schema hashing
- Diagnostic rule evaluation
- Schema comparison

### Integration Tests

Test database connectors against supported database versions.

Examples:

- PostgreSQL schema extraction
- Constraint discovery
- Index discovery
- View metadata inspection
- Permission handling

### Security Tests

Include tests for:

- Tenant isolation
- Unauthorized access
- Credential redaction
- Read-only database permissions
- Unsafe connection destinations
- Resource limits

### Regression Tests

Bug fixes should include tests demonstrating that the original problem is resolved.

### Test Quality

Tests should be:

- Repeatable
- Isolated
- Understandable
- Automated where possible
- Independent of production credentials

The repository will publish executable test commands as its tooling is implemented.

---

## Commit Message Guidelines

DERA strictly enforces the [Conventional Commits](docs/development/COMMIT_CONVENTIONS.md) 1.0.0 specification for all commits and pull request titles.

### Format

```text
type(scope): short description
```

Breaking changes are designated by appending `!` before the colon:
```text
feat(api)!: revise schema snapshot response data contract
```

### Supported Types

| Type | Purpose | SemVer Impact |
|---|---|---|
| `feat` | New deterministic capability, model, or connector | Minor (`0.x.0`) |
| `fix` | Bug fix or deterministic calculation repair | Patch (`0.0.x`) |
| `docs` | Documentation additions or translations | None |
| `refactor` | Code restructuring without functional changes | None |
| `perf` | Deterministic performance improvements | Patch (`0.0.x`) |
| `test` | Adding, updating, or expanding test coverage | None |
| `build` | Packaging metadata or build tooling | None |
| `ci` | CI/CD workflows, DevSecOps gates, or scripts | None |
| `chore` | Maintenance, formatting, or tool configuration | None |
| `security` | Security controls, loopback bindings, or permission checks | Patch (`0.0.x`) |
| `revert` | Reverting a previous commit | Patch (`0.0.x`) |
| `deps` | Package dependencies or lockfile updates | None / Patch |

### Local Commit Validation

You can validate any commit message or PR title locally using:

```bash
# Test a title string
python scripts/development/dev.py validate-title "feat(connectors): add SQLite metadata support"

# Install automated local Git commit-msg hook
python scripts/development/dev.py install-hooks
```

For complete scope definitions, examples, and breaking change rules, see [docs/development/COMMIT_CONVENTIONS.md](docs/development/COMMIT_CONVENTIONS.md).

---

## Pull Request Process

Detailed step-by-step instructions for contributors are documented in [Contribution Workflow](docs/development/CONTRIBUTION_WORKFLOW.md) and [Code Review Policy](docs/development/CODE_REVIEW_POLICY.md).

### Step 1 — Create a Feature Branch
Create a branch with an approved prefix from the latest `upstream/main`:
```bash
git checkout main
git pull --ff-only upstream main
git checkout -b feat/your-feature-name
```

### Step 2 — Implement & Verify Locally
Keep changes focused on a single logical concern. Before committing, run the complete baseline validation suite:
```bash
python scripts/development/dev.py all
```

### Step 3 — Commit with Conventional Commits
```bash
git add .
git commit -m "feat(connectors): implement SQLite table introspection"
```

### Step 4 — Open a Pull Request
Push your branch to your fork and open a pull request against `main`. Fill out the [Pull Request Template](.github/PULL_REQUEST_TEMPLATE.md) completely, including:
- Summary & Motivation
- Change Type checkboxes
- Testing Performed
- Security & Deterministic Non-AI confirmations

### Step 5 — Code Review & CI Qualification
All automated CI checks must pass and at least one code owner approval is required before your PR is squash-merged into `main`.

Maintainers may request revisions before merging.

---

## Issue Reporting

### Bug Reports

A useful bug report should contain:

```markdown
## Description

Describe the issue.

## Steps to Reproduce

1.
2.
3.

## Expected Behavior

Explain the expected result.

## Actual Behavior

Explain what happened.

## Environment

- Operating System:
- DERA Version:
- Database Engine:
- Database Version:
- Python Version:
- Browser:

## Logs

Include sanitized logs.

## Additional Context

Provide relevant details.
```

### Feature Requests

Feature requests should explain:

- The problem being solved
- Proposed functionality
- Expected users
- Possible alternatives
- Technical considerations
- Compatibility requirements

---

## Security

Security vulnerabilities must not be disclosed through public issues before responsible coordination.

Please follow the repository's security reporting policy in [SECURITY.md](SECURITY.md) and prefer GitHub Private Vulnerability Reporting when reporting vulnerabilities.

Direct security contact: **krishanth.b.2008@gmail.com**

Do not include passwords, access tokens, database credentials, or sensitive customer data in public reports.

---

## Documentation and Translations

DERA provides documentation support for 10 international languages, maintained in [`docs/i18n/`](docs/i18n/README.en.md).

| Language | Code | File |
|---|---|---|
| English | `en` | [`docs/i18n/README.en.md`](docs/i18n/README.en.md) |
| Spanish | `es` | [`docs/i18n/README.es.md`](docs/i18n/README.es.md) |
| French | `fr` | [`docs/i18n/README.fr.md`](docs/i18n/README.fr.md) |
| German | `de` | [`docs/i18n/README.de.md`](docs/i18n/README.de.md) |
| Portuguese | `pt` | [`docs/i18n/README.pt.md`](docs/i18n/README.pt.md) |
| Japanese | `ja` | [`docs/i18n/README.ja.md`](docs/i18n/README.ja.md) |
| Korean | `ko` | [`docs/i18n/README.ko.md`](docs/i18n/README.ko.md) |
| Simplified Chinese | `zh-CN` | [`docs/i18n/README.zh-CN.md`](docs/i18n/README.zh-CN.md) |
| Arabic | `ar` | [`docs/i18n/README.ar.md`](docs/i18n/README.ar.md) |
| Russian | `ru` | [`docs/i18n/README.ru.md`](docs/i18n/README.ru.md) |

Translation contributors should:

1. Preserve technical meaning and formatting.
2. Keep code examples, SQL commands, and paths untranslated.
3. Maintain consistent international terminology.
4. Preserve relative working links.
5. Avoid translating code identifiers and parameters.
6. For Arabic (`README.ar.md`), keep code blocks and tables in left-to-right format.
7. Update translations when source documentation changes.

English remains the reference language for technical specifications. Detailed guidance is available in [docs/contributing/guide.md](docs/contributing/guide.md).

---

## Review and Maintainer Policies

The DERA maintainers are responsible for maintaining project quality, security, and architectural consistency.

### Review Criteria

Contributions may be evaluated for:

- Correctness
- Security
- Maintainability
- Performance
- Test coverage
- Documentation quality
- Compatibility
- Alignment with project goals

### Merge Policy

Detailed criteria are governed by our [Code Review Policy](docs/development/CODE_REVIEW_POLICY.md) and [Branch Protection Rules](docs/development/BRANCH_PROTECTION.md). A pull request may be squash-merged into `main` when:

- All required CI status checks pass with 100% success.
- Pull request title adheres to Conventional Commits.
- PR readiness checks pass.
- All review feedback and conversations are resolved.
- Security-sensitive aspects are explicitly assessed.
- The contribution is approved by code owner [@krishanth7](https://github.com/krishanth7).

Maintainers may decline contributions that conflict with the project's scope, deterministic mandate, or security requirements.

---

## Recognition

We appreciate everyone who contributes to DERA.

Contributors may be recognized through:

- GitHub contribution history
- Pull request acknowledgments
- Release notes
- Documentation credits
- Community announcements

Contributions are evaluated on quality and usefulness, not quantity.

---

## Getting Help

Need assistance?

- [GitHub Discussions](https://github.com/krishanth7/dera/discussions)
- [GitHub Issues](https://github.com/krishanth7/dera/issues)
- [Repository](https://github.com/krishanth7/dera)

For private conduct concerns, follow the [Code of Conduct](CODE_OF_CONDUCT.md).

---

## Thank You

Thank you for helping build DERA.

Our goal is to make database engineering more transparent, accessible, reliable, and reproducible.

**Understand Every Schema. Engineer Every Change.**

---

<div align="center">

**DERA — Database Engineering & Reverse Analysis**

Maintained by [Bunga Krishanth](https://github.com/krishanth7)

© 2026 DERA Contributors

</div>
