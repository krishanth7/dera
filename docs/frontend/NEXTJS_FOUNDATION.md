# Next.js Foundation — Phase 7.1

## Core Setup
- **App Router**: Uses `src/app/` structure with Route Groups `(auth)` and `(app)`.
- **Layouts**: RootLayout provides `ThemeProvider`, `WorkspaceProvider`, and `ToastProvider`.
- **Security Headers**: Injected via `next.config.ts`:
  - Content-Security-Policy (CSP)
  - X-Frame-Options: SAMEORIGIN
  - X-Content-Type-Options: nosniff
  - Referrer-Policy: strict-origin-when-cross-origin
  - Permissions-Policy
- **Bundle Optimization**: Tree-shaking on icons and UI components, Turbopack support.
