# Inspector & Search Security Controls

**Modules**: `apps/web/src/components/table-inspector/`, `schema-search/`, `dependency-explorer/`  
**Phase**: 7.5 — Table Inspector, Advanced Search & Dependency Visualization  

---

## 1. Security Architecture & Threat Model

Database metadata inspection presents unique application security challenges. Database schemas often contain user-controlled naming, arbitrary SQL check expressions, and cross-tenant identifiers. DERA applies defensive-in-depth principles across all Phase 7.5 interfaces.

```text
[ Untrusted DB Engine Metadata ]
             |
             v
[ Phase 6.6 Backend Sanitization & RBAC ]
             |
             v (Verified REST API)
[ Phase 7.5 Typed Client & Context Boundary ]
             |
             +---> React Text Nodes (Auto-Escaping)
             +---> Inert Check Constraint Display (No SQL Execution)
             +---> Strict Workspace Boundary Scoping
             +---> URL Parameter Validation
```

---

## 2. XSS & Injection Mitigation

- **Zero `dangerouslySetInnerHTML`**: All metadata fields—including table names, column names, comments, default expressions, and check constraints—are rendered purely through standard React string children, ensuring automatic DOM escaping.
- **Inert SQL Handling**: Check constraint SQL clauses (e.g., `CHECK (salary > 0 AND tax_code IS NOT NULL)`) are treated strictly as inert, unexecuted strings within styled `<code>` blocks.
- **Identifier Escaping**: Identifiers containing special characters, quotes, or Unicode sequences are safely displayed without browser DOM manipulation vulnerabilities.

---

## 3. Multi-Tenant Authorization & Boundary Scoping

- **Workspace Scoping**: Every table inspector and search request requires a validated `workspaceId`. The backend rejects queries attempting to access schemas outside the authenticated workspace boundary.
- **No Direct Database Connections**: Frontend code never receives or stores database connection strings, passwords, SSH keys, or cloud credentials. All data is fetched via authorized backend REST APIs.
- **Cross-Schema Isolation**: Schema search queries filter results exclusively within schemas assigned to the active workspace session.

---

## 4. Query Protection & Rate Limiting

- **Search Debouncing**: Schema search inputs are debounced to 300ms on the client. Stale in-flight requests are automatically aborted via `AbortController`.
- **Bounded Result Sets**: Pagination is enforced across all search results (default 25, max 100 per page) to prevent client memory exhaustion and backend denial-of-service.
- **Graph Traversal Limits**: Transitive dependency algorithms enforce hard depth caps (maximum 20 hops) to prevent resource depletion on dense cyclic graphs.
