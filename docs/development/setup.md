# DERA Development Guide & Setup

**Project:** DERA — Database Engineering & Reverse Analysis  
**Repository:** [https://github.com/krishanth7/dera](https://github.com/krishanth7/dera)  
**License:** [MIT License](../../LICENSE)

---

## 1. Prerequisites

- **Python:** 3.12 or newer
- **Node.js:** LTS (v20+)
- **Docker & Docker Compose:** Latest stable version
- **Git:** 2.40+

---

## 2. Environment Configuration

1. Clone the repository:
   ```bash
   git clone https://github.com/krishanth7/dera.git
   cd dera
   ```

2. Copy the example environment configuration:
   ```bash
   cp .env.example .env
   ```
   *Never commit real secrets or production credentials to `.env`.*

3. Planned local startup via Docker Compose:
   ```bash
   docker compose -f infrastructure/docker/docker-compose.dev.yml up --build
   ```

---

## 3. Engineering & Coding Standards

### 3.1 Python (Backend & Analysis Engine)
- Follow **PEP 8** style guidelines.
- Use explicit type annotations for all function parameters and return values.
- Enforce formatting and linting via **Ruff**.
- Type checking via **mypy** or **Pyright**.

### 3.2 TypeScript & React (Frontend)
- Use **TypeScript strict mode** (`"strict": true`).
- Build accessible, functional React components.
- Style with **Tailwind CSS** and **shadcn/ui**.
- Format with **Prettier** and lint with **ESLint**.

### 3.3 Strict Non-AI Constraint
DERA does not utilize generative AI, LLMs, or external inference APIs. All code contributions must employ deterministic algorithms, static rules, mathematical graph processing, or SQL AST analysis.

---

## 4. Testing Strategy

Run the automated test suites:
- **Unit Tests:** `pytest tests/unit`
- **Integration Tests:** `pytest tests/integration`
- **Frontend E2E:** `npx playwright test`
- **Security Scans:** CodeQL automated scanning and dependency audit

---

## 5. Commit Guidelines

Follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:
- `feat(scope): description`
- `fix(scope): description`
- `docs(scope): description`
- `test(scope): description`
- `refactor(scope): description`
- `security(scope): description`
