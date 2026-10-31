# DERA — Phase 7.5 Baseline Audit: Table Inspector, Advanced Search & Dependency Visualization

**Document**: `docs/audit/PHASE_7_5_INSPECTOR_BASELINE.md`  
**Milestone**: Phase 7.5 — Table Inspector, Advanced Search & Dependency Visualization  
**Repository**: [https://github.com/krishanth7/dera](https://github.com/krishanth7/dera)  
**Branch**: `feat/phase-7.5-table-inspector-dependencies`  
**Base Commit SHA**: `49f242e4db562ec898fec12e69f0be62d88792e0`  
**Audit Date**: October 31, 2026  
**Auditor**: DERA Verification & Assurance Core  

---

## 1. Executive Summary

This baseline audit evaluates the operational readiness of the DERA repository for **Phase 7.5: Table Inspector, Advanced Search & Dependency Visualization**. It verifies the underlying Phase 6 canonical backend engines (structural metadata, foreign key graph, cycle detection, topological ordering, and schema snapshots) and Phase 7.1–7.4 frontend foundations to ensure complete contract compatibility before implementation.

### Verified Prerequisites
- **Phase 6.1**: Canonical schema model and object identity abstraction.
- **Phase 6.2**: Structural reconstruction (tables, columns, constraints, unique keys, check constraints, indexes).
- **Phase 6.3**: Foreign key relationship graph, composite mappings, self-referencing relationships, and cross-namespace relationships.
- **Phase 6.4**: Dependency analysis, cycle detection (Tarjan SCC & Johnson elementary cycle algorithms), topological creation/drop orders, and parallel migration levels.
- **Phase 6.5**: Cryptographic schema snapshots and integrity verification.
- **Phase 6.6**: Reverse engineering REST APIs (`/reverse-engineering/tables`, `/columns`, `/constraints`, `/dependencies`, `/cycles`, `/snapshots`).
- **Phase 7.1**: Next.js & TypeScript frontend foundation, design tokens, app shell, navigation.
- **Phase 7.2**: Session authentication, workspace context, and RBAC permissions.
- **Phase 7.3**: Database connection management and Schema Explorer UI.
- **Phase 7.4**: Interactive ER Diagram canvas and relationship visualization studio.

---

## 2. API Contract & Data Model Verification

The following backend endpoints in `apps/api/src/dera_api/api/v1/endpoints/reverse_engineering/` were audited and verified for Phase 7.5 consumption:

| Endpoint Path | Method | Backend Handler | Response Contract | Verified Status |
| :--- | :---: | :--- | :--- | :---: |
| `/schemas/{schema_id}/tables` | `GET` | `list_schema_tables` | `TableListResponse` | **VERIFIED** |
| `/schemas/{schema_id}/tables/{table_id}` | `GET` | `get_table_detail` | `TableDetailResponse` | **VERIFIED** |
| `/schemas/{schema_id}/columns/{column_id}` | `GET` | `get_column_detail` | `ColumnDetailResponse` | **VERIFIED** |
| `/schemas/{schema_id}/constraints` | `GET` | `list_schema_constraints` | `ConstraintListResponse` | **VERIFIED** |
| `/schemas/{schema_id}/relationships` | `GET` | `get_schema_relationships` | `RelationshipGraphResponse` | **VERIFIED** |
| `/schemas/{schema_id}/tables/{table_id}/relationships` | `GET` | `get_table_relationships` | `TableRelationshipsResponse` | **VERIFIED** |
| `/schemas/{schema_id}/dependencies` | `GET` | `get_schema_dependencies` | `DependencyAnalysisResponse` | **VERIFIED** |
| `/schemas/{schema_id}/tables/{table_id}/dependencies` | `GET` | `get_table_dependencies` | `TableDependencyResponse` | **VERIFIED** |
| `/schemas/{schema_id}/cycles` | `GET` | `get_schema_cycles` | `CycleReportResponse` | **VERIFIED** |
| `/snapshots` | `GET` | `list_schema_snapshots` | `SnapshotListResponse` | **VERIFIED** |
| `/snapshots/{snapshot_id}` | `GET` | `get_schema_snapshot` | `SnapshotSummaryResponse` | **VERIFIED** |

---

## 3. Dependency & Graph Semantics Verification

Phase 6.4 core contracts establish deterministic rules that Phase 7.5 must visually preserve:
1. **Edge Direction**: A foreign key edge originates at the referencing child table and points to the referenced parent table (`child -> parent`).
2. **Dependency Definition**:
   - **Outgoing Dependencies**: Tables that the selected table references (parents that must exist before the child can be created).
   - **Incoming Dependencies (Dependents)**: Tables that reference the selected table (children that depend on this parent).
3. **Cycle Definition**: Cycles occur when there is circular reachability (`A -> B -> ... -> A`). Tarjan's algorithm partitions the graph into Strongly Connected Components (SCCs). Components with `|V| > 1` or self-loops (`|V| = 1` with self-reference) are cyclic.
4. **Execution Order**:
   - `creation_order`: Topological sort ensuring parents precede children.
   - `drop_order`: Reverse topological sort ensuring children are dropped before parents.
   - `levels`: Parallel migration levels (`TopologicalLevelResponse`).

---

## 4. Architectural Decisions & Scope

### 4.1 Frontend Routing
- Table Inspector: `/tables/[tableId]` (with rewrite from `/app/tables/[tableId]`), accepting `?schemaId=...` for schema contextualization.
- Advanced Search: `/search` (with rewrite from `/app/search`), accepting `?schemaId=...`, `?q=...`, `?type=...`.
- Dependency Explorer: `/dependencies` and `/dependencies/[objectId]` (with rewrites from `/app/dependencies`), integrating schema-wide and table-level analysis.

### 4.2 Universal Object Inspector Interface (NoSQL Extensibility)
To accommodate future database services (Firebase Firestore, Realtime Database, MongoDB, DynamoDB) without misrepresenting current SQL relational implementations, an extensible abstraction is defined:
```typescript
export type InspectorObjectKind =
  | "table"
  | "view"
  | "collection"
  | "document_type"
  | "database_resource";

export interface InspectorObject {
  id: string;
  kind: InspectorObjectKind;
  displayName: string;
  namespace?: string;
  completeness: string;
}
```

### 4.3 Security & XSS Prevention
- All identifiers (tables, columns, constraints, indexes, expressions) are treated as untrusted text.
- Check constraint expressions and SQL defaults are rendered inertly without HTML execution.
- URLs and query parameters are strictly sanitized and encoded with `encodeURIComponent`.

---

## 5. Implementation Roadmap

1. **API Client Extensions**: Add `getSchemaDependencies`, `getTableDependencies`, `getSchemaCycles`, `listSchemaConstraints`, `listSnapshots`, `getSnapshot` to `apps/web/src/lib/api-client.ts`.
2. **Domain Models & Utilities**: Create `apps/web/src/components/table-inspector/types.ts` and `apps/web/src/components/dependency-explorer/types.ts`.
3. **Table Inspector UI**: Build header, summary cards, tabs for Columns, Constraints, Indexes, Dependencies, and Raw Metadata.
4. **Advanced Schema Search UI**: Build cross-schema search with multi-field matching, filters, debouncing, and pagination.
5. **Dependency Explorer UI**: Build reachability explorer, transitive depth controls, cycle & SCC visualization, and execution order sequences.
6. **Integration & Navigation**: Update sidebar, link Schema Explorer, ER Canvas, Table Inspector, and Dependency Explorer.
7. **Verification**: Comprehensive unit, component, determinism, accessibility, security, and build checks.
8. **Documentation & Audit**: 16 markdown documents in `docs/frontend/` and acceptance audit.
