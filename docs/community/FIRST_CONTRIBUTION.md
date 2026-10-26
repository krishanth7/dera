# First-Time Contributor Guide

> **Project:** DERA — Database Engineering & Reverse Analysis  
> **Repository:** [https://github.com/krishanth7/dera](https://github.com/krishanth7/dera)  
> **Lead Maintainer:** [Krishanth](https://github.com/krishanth7)  
> **Parent Guide:** [`CONTRIBUTING.md`](../../CONTRIBUTING.md)  
> **License:** [MIT License](../../LICENSE)  

---

## Welcome to DERA! 👋

Thank you for your interest in contributing to DERA! Whether you are an experienced software engineer, a database administrator, or a first-time open-source contributor, this guide will walk you through your first pull request step by step.

If you have questions at any point, check our [Contributor FAQ](CONTRIBUTOR_FAQ.md) or start a thread in [GitHub Discussions](https://github.com/krishanth7/dera/discussions).

---

## 1. Finding Your First Task

A great place to start is our curated beginner issues:
- Browse issues tagged with [**`good first issue`**](https://github.com/krishanth7/dera/labels/good%20first%20issue). These are self-contained tasks with clear requirements and guidance.
- Browse issues tagged with [**`help wanted`**](https://github.com/krishanth7/dera/labels/help%20wanted) for dialect connectors, benchmark tests, or documentation improvements.
- Check our [Contribution Areas Map](CONTRIBUTION_AREAS.md) to explore opportunities across documentation, translations, database connectors, core algorithms, and frontend interfaces.
- If you're interested in documentation, check [`docs/i18n/`](../i18n/README.en.md) for international translation opportunities across our 10 supported languages.

Comment on the issue you would like to work on so maintainers can assign it to you and avoid duplicated effort.

---

## 2. Choosing Your Contribution Workflow

DERA supports two contribution workflows depending on the type of change you are making:

1. **GitHub Web Interface (Fastest for Documentation):** Recommended for minor typos, grammar clarifications, or small translation edits. You do not need a terminal, Python, or Node.js installed.
2. **Local Terminal / IDE Setup:** Recommended for code changes, new documentation guides, architectural specifications, and complex test additions.

---

## 3. Workflow A: Web-Based Contributions (Docs Only)

For quick documentation improvements, you can contribute directly through GitHub:

1. Navigate to the file you want to edit on [GitHub](https://github.com/krishanth7/dera).
2. Click the **Pencil icon** (✏️) in the upper right corner to edit the file.
3. GitHub will automatically create a fork and a new branch in your account.
4. Make your edits. Preview your changes with the **Preview** tab.
5. In the **Propose changes** box at the bottom:
   - Provide a Conventional Commit title (e.g., `docs(readme): fix typo in quickstart section`).
   - Describe what was changed and why.
6. Click **Propose changes**, then click **Create pull request**.
7. Complete the [Pull Request Template](../../.github/PULL_REQUEST_TEMPLATE.md) and submit!

---

## 4. Workflow B: Local Terminal Development Setup

For code and multi-file contributions, set up a local workspace:

### Prerequisites
- **Python:** 3.12 or 3.13
- **Node.js:** LTS (v20 or v22)
- **Git:** 2.30+

### Step-by-Step Setup

```bash
# 1. Fork the repository on GitHub, then clone your personal fork
git clone https://github.com/YOUR_USERNAME/dera.git
cd dera

# 2. Add the authoritative upstream remote
git remote add upstream https://github.com/krishanth7/dera.git

# 3. Create your feature branch off main
git checkout main
git pull upstream main
git checkout -b feat/your-feature-name

# 4. Install local dependencies
npm install

# 5. Run the full developer verification suite
python scripts/development/dev.py all
```

If `python scripts/development/dev.py all` completes with `[SUCCESS]: All development baseline checks passed successfully`, your environment is fully operational!

---

## 5. Development Guidelines & Safety Rules

### Core Invariant: Deterministic Non-AI Execution
DERA is strictly non-AI at runtime. Never introduce external AI inference APIs (OpenAI, Anthropic, Gemini, Groq) or local LLM execution runtimes. All logic must rely on deterministic catalog queries, AST parsing, and graph algorithms.

### Database Introspection Safety
All database connector code must strictly enforce read-only execution (`SET TRANSACTION READ ONLY`), static query mutation blocking (`DROP`, `ALTER`, etc.), and zero customer row-data extraction.

---

## 6. Testing & Validation

Before committing, run local validation to ensure your changes pass all checks:

```bash
# Run unit & integration tests
python scripts/development/dev.py test

# Run TypeScript compiler static typechecks
python scripts/development/dev.py typecheck

# Run documentation linting, links, mermaid, and navigation checks
npm run docs:check

# Run the complete baseline verification suite
python scripts/development/dev.py all
```

For detailed documentation rules and troubleshooting, see our [Documentation Validation Guide](../development/DOCUMENTATION_VALIDATION.md).

---

## 7. Conventional Commits

DERA strictly enforces the [Conventional Commits](https://www.conventionalcommits.org/) 1.0.0 specification:

```text
type(scope): concise description in lowercase
```

Examples:
- `feat(connectors): add SQLite composite foreign key inspection`
- `fix(core): correct topological sort cycle detection for self-referential keys`
- `docs(community): add first contribution walkthrough guide`

Validate your commit message locally:
```bash
python scripts/development/dev.py validate-title "docs(community): add first contribution walkthrough guide"
```

---

## 8. Submitting & Updating Your Pull Request

1. **Push your branch:**
   ```bash
   git push -u origin feat/your-feature-name
   ```
2. **Open the Pull Request:** Navigate to [https://github.com/krishanth7/dera/pulls](https://github.com/krishanth7/dera/pulls) and click **New Pull Request**.
3. **Fill the Template:** Fill out the checklist in [`.github/PULL_REQUEST_TEMPLATE.md`](../../.github/PULL_REQUEST_TEMPLATE.md).
4. **Monitor CI Gates:** GitHub Actions will automatically validate linting, tests, security, and documentation links.
5. **Responding to Reviews:** Maintainers review submissions within **3 to 5 business days**. If changes are requested:
   - Make the required updates on your local branch.
   - Commit and push to your fork:
     ```bash
     git push origin feat/your-feature-name
     ```
   - The PR updates automatically.
6. **Merging:** Once approved and all checks pass, maintainers squash-merge your PR into `main`. Congratulations on becoming a DERA contributor! 🎉
