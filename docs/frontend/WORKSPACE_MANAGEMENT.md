# Workspace & Member Management UI — Phase 7.2

## Multi-Tenancy Architecture
- Isolated tenant workspaces backed by `GET /api/v1/workspaces` and `POST /api/v1/workspaces`.
- Context switching seamlessly updates `currentWorkspace`, re-scoping navigation and data retrieval.

## Member Management (`/app/workspaces/[slug]/members`)
- Directory table listing member email, active role (`owner`, `admin`, `editor`, `viewer`), and membership status.
- Direct member invitation/addition via `POST /api/v1/workspaces/{slug}/members`.
- Role updates via `PATCH /api/v1/workspaces/{slug}/members/{user_id}` enforcing administrative hierarchy.
- Member deletion via `DELETE /api/v1/workspaces/{slug}/members/{user_id}` with last-owner safeguards.
