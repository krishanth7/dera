# Explorer Testing Specification

**Document Reference**: `docs/frontend/EXPLORER_TESTING.md`  
**Milestone**: Phase 7.3 — Database Connection & Schema Explorer UI  

---

## 1. Test Architecture & Coverage

Phase 7.3 establishes a comprehensive test suite covering the full spectrum of connection management and schema exploration functionality.

### Test Categories

```text
+--------------------------------------------------------------------------+
|                     DERA Phase 7.3 Test Matrix                          |
+-------------------+------------------------------------------------------+
| Category          | Focus Areas                                          |
+-------------------+------------------------------------------------------+
| Unit Tests        | API client methods, payload formation, error mapping |
| Component Tests   | Connection forms, engine selection, table inspector  |
| Security Tests    | XSS prevention in SQL/names, credential masking      |
| Cross-Engine Tests| Postgres, Supabase, MySQL, MariaDB, SQLite contracts |
| Integration Tests | Route loading, split-pane navigation, refresh flows  |
+-------------------+------------------------------------------------------+
```

---

## 2. Test Execution Commands

```bash
# Execute frontend unit & component test suite
npm run test --prefix apps/web

# Execute TypeScript typechecking across workspaces
npm run typecheck

# Execute Next.js production build verification
npm run build --prefix apps/web
```
