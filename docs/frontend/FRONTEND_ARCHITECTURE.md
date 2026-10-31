# Frontend Architecture — Phase 7.1

## Overview

DERA's visual database engineering studio frontend is built with **Next.js (App Router)** and **TypeScript** in a strictly typed, deterministic architecture.

### Technology Stack
- **Framework**: Next.js (App Router)
- **UI Library**: React
- **Language**: TypeScript (Strict Mode)
- **Styling**: Tailwind CSS v4 (PostCSS)
- **Primitives**: Radix UI
- **Icons**: Lucide React
- **Theme**: `next-themes`
- **Validation**: Zod
- **Testing**: Vitest, React Testing Library, Playwright

## Monorepo Integration
- Location: `apps/web/`
- Consumes shared contracts from `@dera/contracts` (`packages/contracts/src/index.ts`)
- Strict separation of browser environment vs backend services
- Zero client-side database credentials; all operations routed through backend workers
