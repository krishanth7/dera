
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

```bash
git checkout -b feat/your-feature-name
```

Examples:

```text
feat/postgresql-connector
feat/schema-visualization
fix/foreign-key-parser
docs/installation-guide
test/schema-diff
```

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

DERA recommends Conventional Commits.

### Format

```text
type(scope): short description
```

### Supported Types

| Type | Purpose |
|---|---|
| feat | New feature |
| fix | Bug fix |
| docs | Documentation |
| refactor | Code restructuring |
| test | Tests |
| perf | Performance improvement |
| build | Build system |
| ci | CI/CD changes |
| chore | Maintenance |
| security | Security improvement |

### Examples

```text
feat(connector): add PostgreSQL schema inspection
fix(graph): correct composite foreign-key mapping
docs(readme): improve installation documentation
test(schema): add schema normalization tests
perf(erd): optimize large graph rendering
security(api): enforce organization access checks
```

Use concise, meaningful commit messages.

---

## Pull Request Process

### Step 1 — Create a Branch

Create a feature or fix branch from the latest main branch.

### Step 2 — Implement the Change

Keep changes focused and avoid unrelated modifications.

### Step 3 — Add Tests

Include tests covering the changed behavior.

### Step 4 — Update Documentation

Update relevant documentation when functionality or configuration changes.

### Step 5 — Verify Your Changes

Run applicable tests, formatting checks, and linting tools.

### Step 6 — Open a Pull Request

Open a pull request against the main branch.

[Create a Pull Request](https://github.com/krishanth7/dera/compare)

### Pull Request Template

Use the following structure:

```markdown
## Summary

Describe the changes.

## Related Issue

Closes #

## Changes Made

- 
- 
- 

## Testing

Explain how the changes were tested.

## Screenshots

Add screenshots for UI changes, if applicable.

## Checklist

- [ ] Code follows project standards
- [ ] Tests added or updated
- [ ] Documentation updated
- [ ] No secrets or sensitive data included
- [ ] Security implications reviewed
- [ ] Breaking changes documented
```

### Pull Request Expectations

- Keep PRs focused.
- Explain the motivation.
- Include relevant tests.
- Respond respectfully to review feedback.
- Avoid unrelated formatting changes.
- Document breaking changes.
- Do not include secrets or private customer data.

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

A pull request may be merged when:

- Required checks pass.
- Review feedback is resolved.
- Changes meet project standards.
- Security concerns are addressed.
- The contribution is approved by an authorized maintainer.

Maintainers may decline contributions that conflict with the project's scope or security requirements.

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
