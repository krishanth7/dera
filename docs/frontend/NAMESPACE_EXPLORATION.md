# Namespace Exploration Specification

**Document Reference**: `docs/frontend/NAMESPACE_EXPLORATION.md`  
**Milestone**: Phase 7.3 — Database Connection & Schema Explorer UI  

---

## 1. Multi-Namespace Support

Modern enterprise databases (such as PostgreSQL and Supabase) partition tables across distinct schemas or namespaces. DERA preserves and exposes this organization natively.

### Namespace Attributes

- **Namespace Identifier**: Canonical name of the schema partition (e.g. `public`, `pg_catalog`, `information_schema`).
- **Object Count**: Total count of active tables and views belonging to the namespace.
- **Filtering Dropdown**: Quick-filter select menu at the top of the tree allows isolating tables to a single namespace.
- **Collapsible Section Header**: Each namespace group can be independently toggled to manage screen real estate for large schemas.

---

## 2. Cross-Namespace Foreign Keys

When tables in one namespace reference tables in another (for example, `public.orders` referencing `auth.users`), the Explorer renders fully qualified identifiers:

```text
[ public.orders ]
  └─ constraint: fk_orders_user
     └─ user_id  ──>  auth.users (id)
```
