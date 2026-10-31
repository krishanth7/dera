# ER Graph Models & Contracts

**Document Reference**: `docs/frontend/ER_GRAPH_MODELS.md`  
**Milestone**: Phase 7.4 — Interactive ER Diagram Canvas & Relationship Visualization  

---

## 1. Data Contracts

The frontend diagram models consume verified relationship graphs produced by Phase 6.3 backend modules and served via Phase 6.6 REST endpoints (`GET /api/v1/reverse-engineering/schemas/{id}/relationships`).

### 1.1 Backend Contract

```typescript
export interface RelationshipGraphResponse {
  database_name: string;
  engine: string;
  node_count: number;
  edge_count: number;
  nodes: RelationshipNodeItem[];
  edges: RelationshipEdgeItem[];
}
```

### 1.2 Frontend Rendering Model

```typescript
export interface CanvasNode {
  id: string;               // Canonical table_id
  name: string;             // Native table name
  namespace: string;        // Schema / namespace name
  table_type?: string;      // TABLE, VIEW, etc.
  columns: ColumnItem[];    // Name, native_type, is_primary_key, is_foreign_key
  has_primary_key: boolean; // Flag indicating presence of primary key
  x: number;                // Canvas coordinate X
  y: number;                // Canvas coordinate Y
  width: number;            // Computed card width (260px)
  height: number;           // Computed card height based on visible columns
}

export interface CanvasEdge {
  id: string;               // Canonical edge_id
  source_table_id: string;  // Referencing child table ID
  source_table_name: string;
  target_table_id: string;  // Referenced parent table ID
  target_table_name: string;
  constraint_name: string;  // Native constraint name
  source_columns: string[]; // Referencing column names
  target_columns: string[]; // Referenced column names
  column_pairs: ColumnPairMapping[]; // Ordered pair mapping
  on_delete?: string | null;
  on_update?: string | null;
  is_composite: boolean;    // true when source_columns.length > 1
  is_self_loop: boolean;    // true when source_table_id === target_table_id
  is_parallel: boolean;     // true when multiple edges share same table pair
  parallel_index: number;   // 0-indexed position within parallel group
  parallel_total: number;   // total parallel edges in group
}
```

---

## 2. Invariants

- **Canonical Identity**: All nodes and edges use database object identifiers (`table_id`, `edge_id`) rather than array indices.
- **Directional Semantics**: The foreign key edge originates at the referencing child table (`source`) and points to the referenced parent table (`target`).
- **Zero Fabrication**: No edges are synthesized from column naming heuristics; all edges stem from authentic database constraints.
