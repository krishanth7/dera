# Phase 7.1 Next.js & TypeScript Frontend Foundation — Baseline Audit

**Document Reference**: `docs/audit/PHASE_7_1_FRONTEND_BASELINE.md`
**Milestone**: Phase 7.1 — Next.js & TypeScript Frontend Foundation
**Implementation Branch**: `feat/phase-7.1-nextjs-frontend-foundation`
**Base Commit SHA**: `455de3c91edbafd18930c1ded913108d9ad8aade`
**Audit Date**: October 2026
**Auditor**: Principal Frontend Architect & TypeScript Systems Engineer

---

## 1. Executive Summary

This baseline audit assesses the DERA repository at commit `455de3c` before implementing
Phase 7.1. It documents the existing frontend state, verifiable backend contracts,
package manager confirmation, architecture decisions, and the implementation plan.

---

## 2. Repository Baseline

| Property | Value |
|:---|:---|
| **Base Commit SHA** | `455de3c91edbafd18930c1ded913108d9ad8aade` |
| **Branch** | `feat/phase-7.1-nextjs-frontend-foundation` |
| **Package Manager** | `npm` (v11.6.2, `package-lock.json` present) |
| **Node Version (Runtime)** | v25.2.1 |
| **Monorepo Structure** | npm workspaces (`packages/*`, `apps/*`) |
| **TypeScript Version** | ^7.0.2 (root `devDependencies`) |
| **Root tsconfig** | Strict mode enabled, `jsx: preserve`, ES2022 |

---

## 3. Existing Frontend State (`apps/web`)

### 3.1 What Exists

| File | State | Notes |
|:---|:---|:---|
| `apps/web/package.json` | Minimal — `@dera/web`, only `build: tsc`, depends on `@dera/contracts` | No Next.js, no React, no Tailwind installed |
| `apps/web/tsconfig.json` | Extends root, strict, `noEmit: true`, `jsx: preserve` | Ready for Next.js extension |
| `apps/web/src/app/layout.tsx` | Bare root layout, no `<html>` classes, no global CSS | Replaces in Phase 7.1 |
| `apps/web/src/app/page.tsx` | Static status page with inline styles | Replaces in Phase 7.1 |
| `apps/web/src/components/Navbar.tsx` | Inline-style navbar | Replaces with proper shell |
| `apps/web/src/components/StatusCard.tsx` | Inline-style card component | Replaces with design system card |
| `apps/web/src/lib/api-client.ts` | Minimal typed client (health + meta only) | Extended in Phase 7.1 |
| `apps/web/src/types/index.ts` | Re-exports `@dera/contracts`, adds `SystemMeta`, `CanvasState` | Extended |
| `apps/web/src/index.ts` | `DeraSchemaCanvas` class, canvas types | Preserved |

### 3.2 What Is Missing

- No Next.js framework (`next`) installed
- No React (`react`, `react-dom`) installed
- No Tailwind CSS installed
- No design system / design tokens
- No application shell (sidebar, header, breadcrumbs)
- No route groups or protected routing
- No component library (primitives)
- No notification system
- No error/loading/empty states
- No dark theme support
- No accessibility foundations
- No test infrastructure (Vitest, React Testing Library, Playwright)
- No Next.js configuration file (`next.config.ts`)
- No `next-env.d.ts`
- No `public/` directory
- No `.env.local.example` for web app

---

## 4. Reusable Packages

### 4.1 `packages/contracts` — TypeScript Shared Contracts

| Type | Description |
|:---|:---|
| `DatabaseColumn` | Column metadata with nullability, PK flag, default |
| `PrimaryKeyConstraint` | Named primary key with column list |
| `ForeignKeyConstraint` | FK with referential actions |
| `TableIndex` | Index definition with uniqueness and method |
| `DatabaseTable` | Full table metadata with columns, keys, indexes |
| `SchemaSnapshot` | Versioned snapshot of full schema across dialects |
| `DiagnosticFinding` | Rule violation finding with severity |
| `TableDependencyGraph` | Nodes, edges, topological order, cycle flag |

**Status**: READY — All types are stable and consumable by the frontend.

---

## 5. Verified Backend API Readiness

### 5.1 API Routes Available (Phase 4.x + 6.6)

| Route | Method | Description |
|:---|:---|:---|
| `GET /health` | Health check | Service status, version |
| `GET /api/v1/meta` | System metadata | Zero-AI policy, dialects |
| `POST /api/v1/auth/register` | Register user | Email + password |
| `POST /api/v1/auth/login` | Login | Sets Secure/HttpOnly session cookie |
| `POST /api/v1/auth/logout` | Logout | Clears session cookie |
| `GET /api/v1/auth/me` | Current user | Authenticated user info |
| `GET /api/v1/workspaces` | List workspaces | Paginated |
| `POST /api/v1/workspaces` | Create workspace | CSRF-protected |
| `GET /api/v1/workspaces/{id}` | Workspace detail | Auth + membership |
| `GET /api/v1/workspaces/{id}/members` | List members | Role-based |
| `GET /api/v1/reverse-engineering/...` | RE endpoints | Schema, tables, columns |

### 5.2 Authentication Architecture

- **Session type**: Secure, HttpOnly cookie-based sessions
- **CSRF**: Double-submit CSRF token pattern
- **Authorization**: Server-side RBAC (Owner, Admin, Analyst, Viewer)
- **Frontend implication**: No token storage in localStorage/sessionStorage;
  credentials travel via cookies; CSRF token must be fetched and included on mutations

### 5.3 API URL Configuration

- `NEXT_PUBLIC_DERA_API_URL` already defined in root `.env.example`
- Pattern: `http://localhost:8000` for development

---

## 6. Phase 6.6 Status

Phase 6.6 has a **baseline audit document** (`PHASE_6_6_API_BASELINE.md`) that describes
the plan. The reverse engineering API endpoints exist at:
`apps/api/src/dera_api/api/v1/endpoints/reverse_engineering/`.
The commit history shows Phase 6.5 (snapshots) was merged; Phase 6.6 API is scaffolded.

**Frontend API Contract Status**: PARTIALLY READY — Health, auth, and workspace endpoints
are confirmed ready. Reverse engineering endpoints are implemented in code and usable
in typed API client but full integration depends on running backend.

---

## 7. Architecture Decisions

### 7.1 Next.js App Router (Confirmed)

The existing `apps/web/src/app/` directory structure confirms App Router is already
targeted. Phase 7.1 will complete this foundation.

### 7.2 Tailwind CSS v4

Tailwind CSS v4 (via `@tailwindcss/postcss`) will be introduced. It provides CSS-first
configuration, design tokens as CSS custom properties, and eliminates the need for a
separate `tailwind.config.js` for basic token definitions.

### 7.3 Radix UI Primitives

`@radix-ui/react-*` primitives will be used for accessible component foundations
(Dialog, DropdownMenu, Tabs, Select, Checkbox, Switch, Tooltip). These are unstyled,
fully accessible, and keyboard navigable — aligned with WCAG 2.2 AA requirements.

### 7.4 Lucide Icons

`lucide-react` for consistent, tree-shakable SVG icons.

### 7.5 Zod for Environment Validation

`zod` for runtime environment variable validation at startup.

### 7.6 Vitest + React Testing Library + Playwright

- **Unit/Component tests**: Vitest + `@testing-library/react`
- **E2E smoke tests**: Playwright (configured for Chromium)
- Consistent with existing Python test patterns (deterministic, no external services)

### 7.7 next-themes for Theme Management

`next-themes` for SSR-safe theme switching without hydration flash.

---

## 8. Planned Route Structure

```text
/                          → Redirect to /app/overview or /login
/login                     → Public authentication page
/workspaces                → Workspace selection (post-login)
/app                       → Protected application shell (route group)
  /app/overview            → Dashboard / system status
  /app/connections         → Database connections (Phase 7.2+)
  /app/schemas             → Schema explorer (Phase 7.2+)
  /app/relationships       → Relationship graph (future)
  /app/dependencies        → Dependency analysis (future)
  /app/snapshots           → Snapshot management (future)
  /app/exports             → Export management (future)
  /app/settings            → Application settings
```

---

## 9. File Creation Plan

### New Files in `apps/web/`

- `next.config.ts` — Next.js configuration with security headers
- `postcss.config.mjs` — PostCSS for Tailwind
- `vitest.config.ts` — Vitest configuration
- `playwright.config.ts` — Playwright E2E configuration
- `.env.local.example` — Frontend environment variables template
- `public/` — Static assets (favicon, icons)
- `src/app/globals.css` — Global styles and Tailwind tokens
- `src/app/(auth)/login/page.tsx` — Login page
- `src/app/(app)/layout.tsx` — App shell layout
- `src/app/(app)/overview/page.tsx` — Overview page
- `src/app/(app)/settings/page.tsx` — Settings page
- `src/components/ui/` — Component library primitives
- `src/components/layout/` — Shell components
- `src/lib/` — Utilities, env validation, API client
- `src/providers/` — Context providers (theme, workspace, toast)
- `src/hooks/` — Custom React hooks
- `src/styles/` — Design token definitions
- `tests/` — Unit, component, and E2E tests

### Modified Files

- `apps/web/package.json` — Add Next.js, React, Tailwind, all dependencies
- `apps/web/tsconfig.json` — Update for Next.js compatibility

---

## 10. Missing Dependencies (To Be Installed)

| Package | Purpose | Category |
|:---|:---|:---|
| `next` | Application framework | Core |
| `react`, `react-dom` | UI library | Core |
| `@types/react`, `@types/react-dom` | TypeScript types | Dev |
| `tailwindcss`, `@tailwindcss/postcss` | Styling | Core |
| `@radix-ui/react-dialog` | Accessible dialogs | UI |
| `@radix-ui/react-dropdown-menu` | Dropdown menus | UI |
| `@radix-ui/react-tabs` | Tabs | UI |
| `@radix-ui/react-select` | Select controls | UI |
| `@radix-ui/react-checkbox` | Checkboxes | UI |
| `@radix-ui/react-switch` | Toggle switches | UI |
| `@radix-ui/react-tooltip` | Tooltips | UI |
| `@radix-ui/react-label` | Form labels | UI |
| `@radix-ui/react-separator` | Separators | UI |
| `@radix-ui/react-slot` | Slot composition | UI |
| `lucide-react` | Icons | UI |
| `next-themes` | Theme management | Core |
| `clsx` | Conditional classnames | Utility |
| `zod` | Validation | Utility |
| `vitest` | Unit testing | Dev |
| `@testing-library/react` | Component testing | Dev |
| `@testing-library/user-event` | User interaction testing | Dev |
| `@vitejs/plugin-react` | React plugin for Vitest | Dev |
| `jsdom` | DOM environment for tests | Dev |
| `@playwright/test` | E2E testing | Dev |
| `postcss` | CSS processing | Dev |

---

## 11. Security Considerations

- Next.js security headers configured in `next.config.ts` (CSP, X-Content-Type-Options, etc.)
- No `NEXT_PUBLIC_` variables will contain secrets
- Session cookies managed by backend (HttpOnly, Secure, SameSite)
- All database metadata treated as untrusted text (no `dangerouslySetInnerHTML`)
- CSRF tokens fetched via dedicated API call before mutations

---

## 12. Implementation Sequence

1. Install dependencies (Next.js, React, Tailwind, Radix, testing tools)
2. Update `apps/web/package.json` and `tsconfig.json`
3. Create `next.config.ts` with security headers
4. Create `postcss.config.mjs` for Tailwind
5. Create `globals.css` with design tokens (light/dark themes)
6. Implement root `app/layout.tsx` with providers
7. Create route structure (`(auth)`, `(app)` route groups)
8. Build design system (tokens, typography, spacing)
9. Implement component library primitives
10. Build application shell (sidebar, header, breadcrumbs)
11. Implement workspace context
12. Implement loading/error/empty states
13. Implement notification system
14. Implement typed API client
15. Implement authentication foundation
16. Implement protected route middleware
17. Apply accessibility requirements
18. Configure test infrastructure
19. Write unit, component, and E2E tests
20. Run typecheck, lint, build
21. Create documentation
22. Create acceptance audit
