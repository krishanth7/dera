# ER Diagram Security Controls

**Document Reference**: `docs/frontend/ER_SECURITY.md`  
**Milestone**: Phase 7.4 — Interactive ER Diagram Canvas & Relationship Visualization  

---

## 1. Zero-AI & Heuristic Elimination

DERA strictly prohibits probabilistic foreign key guessing, ML models, or generative AI. Every visual node and edge directly corresponds to an inspected database object extracted by Phase 5 connectors and structured by Phase 6.3 engines.

---

## 2. Cross-Site Scripting (XSS) Prevention

All database metadata—including table names, namespace names, column names, column data types, and constraint identifiers—is treated as untrusted external text:

- Table and column names are rendered via React SVG `<text>` elements.
- No `dangerouslySetInnerHTML` is used in graph rendering.
- Test suites explicitly verify that malicious injection payloads (e.g., `<script>alert(1)</script>`, `<img src=x onerror=...>`) render strictly as inert text.

---

## 3. Workspace Boundary Enforcement

All API requests issued by `apiClient.getSchemaRelationships` and `getTableRelationships` mandate valid session authentication and inject the active workspace header `X-Workspace-Id`. Backend services verify that the schema belongs to the authorized workspace before returning graph payloads.
