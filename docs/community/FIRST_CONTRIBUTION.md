# First-Time Contributor Guide

**Project:** DERA — Database Engineering & Reverse Analysis  
**Repository:** [https://github.com/krishanth7/dera](https://github.com/krishanth7/dera)  
**Lead Maintainer:** [Krishanth](https://github.com/krishanth7)  
**Parent Guide:** [CONTRIBUTING.md](../../CONTRIBUTING.md)  
**License:** [MIT License](../../LICENSE)  

---

## Welcome to DERA! 👋

Thank you for your interest in contributing to DERA! Whether you are an experienced software engineer, a database administrator, or a first-time open-source contributor, this guide will walk you through your first pull request step by step.

---

## 1. Finding Your First Task

A great place to start is our curated beginner issues:
- Browse issues tagged with [**`good first issue`**](https://github.com/krishanth7/dera/labels/good%20first%20issue). These are self-contained tasks with clear requirements and guidance.
- Browse issues tagged with [**`help wanted`**](https://github.com/krishanth7/dera/labels/help%20wanted) for dialect connectors, benchmark tests, or documentation improvements.
- If you're interested in documentation, check [`docs/i18n/`](../i18n/README.en.md) for international translation opportunities across our 10 supported languages.

Comment on the issue you would like to work on so maintainers can assign it to you and avoid duplicated effort.

---

## 2. Understanding the Codebase Structure

DERA is structured as an enterprise monorepo:

```text
dera/
├── packages/
│   ├── core/         # Deterministic graph algorithms, DAG models, canonical schema objects
│   ├── connectors/   # Database dialect adapters (PostgreSQL, SQLite, MySQL)
│   └── contracts/    # Shared TypeScript contracts and JSON schemas
├── apps/
│   ├── api/          # FastAPI backend services and metadata endpoints
│   └── web/          # Next.js visual engineering studio (React Flow canvas)
├── tests/            # Unit, integration, regression, and architecture test suites
├── scripts/          # Cross-platform developer CLI (`dev.py`) and CI validation scripts
└── docs/             # Architecture, development, security, and governance guides
```

---

## 3. Setting Up Your Development Environment

### Prerequisites
- **Python:** 3.12 or 3.13
- **Node.js:** LTS (v20 or v22)
- **Git:** 2.30+

### Step-by-Step Setup

```bash
# 1. Fork the repository on GitHub, then clone your fork
git clone https://github.com/YOUR_USERNAME/dera.git
cd dera

# 2. Add upstream remote to keep your fork updated
git remote add upstream https://github.com/krishanth7/dera.git

# 3. Copy safe environment template
cp .env.example .env

# 4. Run the full developer verification suite
python scripts/development/dev.py all
```

If `python scripts/development/dev.py all` completes with `[SUCCESS]: All development baseline checks passed successfully`, your environment is 100% ready!

---

## 4. Branching & Making Changes

Always start from an up-to-date `main` branch. Create a feature branch using an approved prefix:

```bash
git checkout main
git pull upstream main
git checkout -b feat/your-feature-name
```

### Allowed Branch Prefixes
- `feat/` — New features, connectors, or models
- `fix/` — Bug fixes or calculation corrections
- `docs/` — Documentation additions or translation improvements
- `test/` — Adding or improving tests
- `refactor/` — Code refactoring without behavioral changes

### Core Rule: Deterministic Engineering
DERA is strictly non-AI at runtime. Never introduce external AI inference APIs (OpenAI, Anthropic, Gemini, Groq) or local LLM execution runtimes. All logic must rely on deterministic catalog queries, AST parsing, and graph algorithms.

---

## 5. Testing & Verification

Before committing, run local validation to ensure your changes pass all checks:

```bash
# Run unit tests
python scripts/development/dev.py test

# Run TypeScript typechecks
python scripts/development/dev.py typecheck

# Validate markdown documentation links
python scripts/development/dev.py validate-docs

# Run full baseline suite
python scripts/development/dev.py all
```

---

## 6. Conventional Commits

DERA strictly enforces the [Conventional Commits](https://www.conventionalcommits.org/) 1.0.0 specification:

```text
type(scope): concise description in lowercase
```

Examples:
- `feat(core): add topological sort cycle detection`
- `fix(connectors): correct composite foreign key mapping in SQLite`
- `docs(community): update first-time contributor instructions`

Validate your commit message locally:
```bash
python scripts/development/dev.py validate-title "feat(core): add topological sort cycle detection"
```

---

## 7. Submitting Your Pull Request

1. Push your branch to your fork:
   ```bash
   git push -u origin feat/your-feature-name
   ```
2. Navigate to [https://github.com/krishanth7/dera/pulls](https://github.com/krishanth7/dera/pulls) and click **New Pull Request**.
3. Fill out the [Pull Request Template](../../.github/PULL_REQUEST_TEMPLATE.md) completely, including testing details and security confirmations.
4. Ensure your PR title matches Conventional Commits format.

---

## 8. Code Review & Next Steps

- Automated GitHub Actions workflows will run tests, security scans, and link validations on your PR.
- Maintainers review submissions within **3 to 5 business days**.
- If revisions are requested, push additional commits to the same branch; the PR will update automatically.
- Once approved, your PR will be squash-merged into `main`, and your name will be permanently celebrated in DERA's Git history!
