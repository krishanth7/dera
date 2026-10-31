# Authentication UI Architecture — Phase 7.2

## Overview
Phase 7.2 implements user-facing authentication, tenant workspace management, and member role administration using verified Phase 4.4 backend endpoints.

## Authentication Routes
- `/login`: Public sign-in page validating credentials against `POST /api/v1/auth/login`. Automatically establishes HttpOnly session cookies and CSRF tokens.
- `/register`: Interactive user registration directly connected to `POST /api/v1/auth/register`.
- `/forgot-password`: Informative account recovery guidance explaining enterprise self-hosted administration and owner-governed credential recovery.

## Session Lifecycle & Transport
- **Storage**: Zero credentials or JWTs stored in `localStorage` or `sessionStorage`.
- **Session Cookie**: `dera_session` (HttpOnly, Secure, SameSite) managed by backend.
- **CSRF Cookie**: `dera_csrf` read and sent via `X-CSRF-Token` header on all mutation requests.
- **Session Restoration**: Initial client load queries `GET /api/v1/auth/me`.
- **Logout Workflows**: Dedicated `/logout` and `/logout-all` calls ensuring total revocation on backend workers.
