# Phase 7.4 Interactive ER Diagram Canvas & Relationship Visualization — Baseline Audit

**Document Reference**: `docs/audit/PHASE_7_4_ER_CANVAS_BASELINE.md`  
**Milestone**: Phase 7.4 — Interactive ER Diagram Canvas & Relationship Visualization  
**Implementation Branch**: `feat/phase-7.4-er-diagram-canvas`  
**Base Commit SHA**: `fd6e2e6be5ff592cf78b51fc6c6415273bb56205`  
**Audit Date**: October 2026  
**Auditor**: Coordinated Engineering Architecture Team  

---

## 1. Executive Summary

Phase 7.4 delivers DERA's deterministic, interactive Entity-Relationship (ER) diagram canvas and relationship visualization studio. Building upon the Phase 7.1 Next.js foundation, Phase 7.2 authentication & workspace isolation, Phase 7.3 database connection management & schema explorer, Phase 6.3 foreign key relationship graph engine, and Phase 6.6 relationship REST endpoints, this milestone introduces a full visual engineering canvas.

The ER canvas renders verified foreign key relationships between tables, composite foreign key column pairs, self-referential relationships, cross-namespace associations, parallel foreign keys, referential actions (`ON UPDATE`, `ON DELETE`), and database constraint metadata.

Direct browser-to-database connections, client-side credential persistence, heuristic/probabilistic relationship inference, and generative AI models are strictly prohibited. All visual graph structures originate exclusively from verified Phase 6.3 backend reverse-engineering models.

---

## 2. Verified Prerequisites & System Status

| Domain | Milestone | Status | Verified Capabilities |
| :--- | :--- | :--- | :--- |
| **Backend Core** | Phase 4.1–4.6 | Merged & Active | FastAPI application factory, session auth, CSRF double-submit protection, workspace RBAC, transactional outbox jobs. |
| **Connectors** | Phase 5.1–5.6 | Merged & Active | PostgreSQL, Supabase, SQLite, MySQL, MariaDB adapters with read-only transaction isolation and credential boundaries. |
| **Canonical Representation** | Phase 6.1–6.2 | Merged & Active | `SchemaRepresentation`, structural reconstruction, typed table, column, constraint, and index representations. |
| **Relationship Graph Engine** | Phase 6.3 | Merged & Active | `ForeignKeyGraph`, `TableNode`, `ForeignKeyEdge`, composite column mappings, parallel edge retention, self-loop routing, unresolved reference tracking. |
| **Dependency & Cycle Analysis**| Phase 6.4 | Merged & Active | Dependency ordering, strongly connected components (SCC), cycle detection, and topological leveling. |
| **Snapshots & RFC 8785** | Phase 6.5 | Merged & Active | Deterministic JSON canonicalization, cryptographic hashing, and snapshot diffing. |
| **Relationship APIs** | Phase 6.6 | Merged & Active | `GET /schemas/{id}/relationships` returning `RelationshipGraphResponse`, `GET /schemas/{id}/tables/{id}/relationships` returning `TableRelationshipsResponse`. |
| **Frontend Foundation** | Phase 7.1 | Merged & Active | Next.js 15 App Router, Tailwind CSS v4, Lucide icons, dark/light theme, typed `DeraApiClient`, application shell. |
| **Auth & Workspaces** | Phase 7.2 | Merged & Active | Session management, workspace selector, role-based access, and last-owner protection. |
| **Schema Explorer** | Phase 7.3 | Merged & Active | Connection management, guided forms, diagnostic tests, schema summary catalog, split-pane tree explorer, column inspection, constraint cards. |

---

## 3. Technology Evaluation & Canvas Architecture Decision

### 3.1 Evaluation Criteria

1. **Accessibility (WCAG 2.2 AA)**: Seamless keyboard focus, ARIA live regions, semantic elements, and structured table/list alternatives.
2. **Determinism**: Given identical schema graph inputs and layout parameters, the engine must produce identical coordinates with zero random jitter or force-simulation drift.
3. **Rendering Control & Customization**: High-fidelity cubic bezier curves, orthogonal routing, self-loop arcs, composite column pair badges, and interactive hover states.
4. **Bundle Footprint & Stability**: Minimal external dependency overhead, avoiding fragile third-party canvas wrappers or breaking upgrades.
5. **Security & Sanitization**: Pure SVG/DOM nodes preventing XSS or script injection from untrusted table or column names.

### 3.2 Decision: Pure SVG & React State Canvas Architecture

Rather than pulling in heavy canvas libraries with arbitrary physics engines, DERA employs a **custom SVG-based interactive canvas** coupled with a **deterministic layered topological layout algorithm**.

Key architectural pillars:
- **Viewport Engine**: Pure SVG `<svg>` viewport with `<g transform="translate(x, y) scale(k)">` matrix handling pan and zoom with sub-pixel precision.
- **Node Cards**: Rich SVG foreignObject / interactive SVG groups rendering table headers, namespaces, column ordinals, types, PK keys, and FK badges.
- **Edge Routing Layer**: Cubic bezier curves with directional arrow markers, offset offsets for parallel edges, and custom geometric arc loops for self-referencing foreign keys.
- **Deterministic Sugiyama-inspired Layered Layout**: Breadth-first / longest-path topological ranking, deterministic tie-breaking by `(namespace, name, table_id)`, and force-free coordinate assignment.
- **Accessible Dual View**: Instant toggle to an accessible, semantic HTML table/list representation allowing non-visual screen reader users and keyboard-only engineers to inspect every relationship and mapping.

---

## 4. Graph Contracts & Data Model Integration

### 4.1 Backend REST Contract (Phase 6.6)

```typescript
// GET /api/v1/reverse-engineering/schemas/{schema_id}/relationships
interface RelationshipGraphResponse {
  database_name: string;
  engine: string;
  node_count: number;
  edge_count: number;
  nodes: TableNodeResponse[];
  edges: RelationshipEdgeResponse[];
}

interface TableNodeResponse {
  table_id: string;
  namespace: string;
  name: string;
}

interface RelationshipEdgeResponse {
  edge_id: string;
  source_table_id: string;
  source_table_name: string;
  target_table_id: string;
  target_table_name: string;
  constraint_name: string;
  source_columns: string[];
  target_columns: string[];
  on_delete: string | null;
  on_update: string | null;
}
```

### 4.2 Frontend Graph Model Adaptation

1. **Node Identity**: Canonical `table_id` preserved across selection, filtering, and layout updates. Augmented with column details from `listTables` / `getTableDetail` for rich card rendering.
2. **Edge Identity**: Stable `edge_id` uniquely identifying the relationship. Parallel edges between identical tables remain distinct objects with offset visual paths.
3. **Composite Foreign Keys**: Ordered column arrays (`source_columns` and `target_columns` of equal length) are mapped pair-by-pair: `(src_col[i] -> tgt_col[i])`.
4. **Self-References**: Edges where `source_table_id === target_table_id` are routed as right-side loop arcs.
5. **Cross-Namespace Relationships**: Namespaces are visually badged and preserved without artificial single-namespace isolation.

---

## 5. Security & Zero-AI Invariants

1. **Zero-AI Compliance**: Zero machine learning models, zero LLMs, zero probabilistic relationship guessers. Every edge reflects an authentic database constraint.
2. **Read-Only / No Browser Credentials**: The client interacts exclusively with verified DERA reverse-engineering APIs using workspace-authenticated sessions.
3. **Untrusted Metadata Handling**: All database table names, column names, comments, and constraint identifiers are treated as untrusted text and rendered via React text nodes to prevent XSS.
4. **Workspace Boundary Enforcement**: All schema and relationship queries validate workspace membership via `X-Workspace-Id` headers.

---

## 6. Implementation Roadmap

1. **API Client & Typed Graph Models**: Extend `apps/web/src/lib/api-client.ts` with `getSchemaRelationships` and `getTableRelationships`.
2. **Deterministic Layout Engine**: Implement layered DAG / topological rank layout with cycle safety and stable coordinate assignment in `apps/web/src/components/er-diagram/layout.ts`.
3. **Interactive Canvas & Components**: Build `ERCanvas`, `TableNode`, `RelationshipEdge`, `RelationshipDetails`, `ERToolbar`, `GraphSearch`, `GraphFilters`, `GraphLegend`, and `AccessibleGraphTable`.
4. **ER Diagram Route**: Update `apps/web/src/app/(app)/relationships/page.tsx` with schema selector, canvas viewport, details drawer, search/filter bar, and accessibility toggle.
5. **Verification**: Comprehensive unit, component, determinism, accessibility, and security tests.
6. **Documentation & Acceptance**: Deliver 14 comprehensive markdown documents in `docs/frontend/` and formal acceptance audit in `docs/audit/PHASE_7_4_ER_CANVAS_ACCEPTANCE.md`.
