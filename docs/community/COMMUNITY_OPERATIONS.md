# Community Operations & Label Taxonomy

**Project:** DERA — Database Engineering & Reverse Analysis  
**Repository:** [https://github.com/krishanth7/dera](https://github.com/krishanth7/dera)  
**Lead Maintainer:** [Krishanth](https://github.com/krishanth7)  
**License:** [MIT License](../../LICENSE)  

---

## 1. Overview

This document outlines the operational standards used by DERA maintainers to manage issues, pull requests, releases, and repository labeling across the project.

---

## 2. Standard Label Taxonomy

DERA employs a structured, color-coded label taxonomy categorized by functional prefixes:

### 2.1 Issue & PR Type (`type/*`)

| Label | Description | Hex Color |
|---|---|---|
| `type/bug` | Software defects, extraction failures, or incorrect calculations | `#d73a4a` (Red) |
| `type/feature` | New deterministic capabilities, models, or algorithms | `#a2eeef` (Cyan) |
| `type/connector` | Database connector implementations or dialect adaptations | `#0e8a16` (Green) |
| `type/docs` | Documentation additions, corrections, and translations | `#0075ca` (Blue) |
| `type/performance` | Latency optimizations, memory scaling, and benchmarks | `#e99695` (Salmon) |
| `type/maintenance` | Refactoring, tooling updates, DevSecOps, and technical debt | `#6f42c1` (Purple) |
| `type/security` | Security hardening, permission checks, and loopback bindings | `#b60205` (Dark Red) |

### 2.2 Priority Levels (`priority/*`)

| Label | Description | Hex Color |
|---|---|---|
| `priority/critical` | Blocking releases, data safety violations, or crash on valid input | `#b60205` (Dark Red) |
| `priority/high` | Major functionality impaired, severe memory overhead | `#d93f0b` (Orange) |
| `priority/medium` | Standard bug or planned roadmap feature | `#fbca04` (Yellow) |
| `priority/low` | Minor cosmetic issue, non-urgent refactor | `#0e8a16` (Green) |

### 2.3 Status Lifecycle (`status/*`)

| Label | Meaning in Triage Workflow | Hex Color |
|---|---|---|
| `status/triage` | Newly opened; pending maintainer initial classification | `#ededed` (Light Gray) |
| `status/in-progress` | Actively being implemented by an assigned contributor | `#1d76db` (Blue) |
| `status/needs-reproduction` | Blocked waiting for minimal reproduction schema or logs | `#e4e669` (Yellow) |
| `status/blocked` | Blocked by external dependency, upstream bug, or decision | `#000000` (Black) |
| `status/resolved` | Completed, verified, and pending release | `#0e8a16` (Green) |

### 2.4 Architectural Component (`component/*`)

| Label | Component Path | Hex Color |
|---|---|---|
| `component/core` | `packages/core/` (Graph theory, models, topological engine) | `#5319e7` |
| `component/connectors` | `packages/connectors/` (PostgreSQL, SQLite, MySQL adapters) | `#0052cc` |
| `component/contracts` | `packages/contracts/` (JSON schemas, TypeScript contracts) | `#1f883d` |
| `component/api` | `apps/api/` (FastAPI backend, routes, middleware) | `#006b75` |
| `component/web` | `apps/web/` (Next.js visual studio, React Flow canvas) | `#6f42c1` |
| `component/ci` | `.github/workflows/` (GitHub Actions, DevSecOps pipelines) | `#d4c5f9` |
| `component/docs` | `docs/` and international documentation | `#bfd4f2` |

### 2.5 Community & Onboarding

| Label | Purpose |
|---|---|
| `good first issue` | Curated, self-contained tasks suitable for newcomers to open source |
| `help wanted` | Tasks where community contributions and dialect expertise are actively sought |

---

## 3. Milestone & Release Management

1. **Phase Milestones:** Issues and PRs are grouped into GitHub Milestones corresponding to DERA's [12-Phase Roadmap](../roadmap/README.md).
2. **Semantic Versioning:** Releases strictly follow SemVer 2.0.0 (`vMAJOR.MINOR.PATCH`):
   - `MAJOR` — Breaking data contract changes or CLI backwards incompatibility.
   - `MINOR` — New connectors or deterministic analysis capabilities.
   - `PATCH` — Bug fixes, performance improvements, and documentation enhancements.
3. **Automated Changelogs:** Because Conventional Commits are enforced via CI on every pull request, changelogs are generated automatically upon release tagging.
