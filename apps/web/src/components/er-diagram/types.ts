/**
 * DERA — Phase 7.4 Entity-Relationship Diagram Canvas Types
 * Strongly-typed graph models, layout options, and interaction state.
 */

export interface ColumnItem {
  name: string;
  native_type: string;
  is_primary_key: boolean;
  is_foreign_key: boolean;
  is_nullable?: boolean;
}

export interface CanvasNode {
  id: string; // table_id
  name: string;
  namespace: string;
  table_type?: string;
  columns: ColumnItem[];
  has_primary_key: boolean;
  x: number;
  y: number;
  width: number;
  height: number;
  is_selected?: boolean;
  is_highlighted?: boolean;
}

export interface ColumnPairMapping {
  source_column: string;
  target_column: string;
}

export interface CanvasEdge {
  id: string; // edge_id
  source_table_id: string;
  source_table_name: string;
  target_table_id: string;
  target_table_name: string;
  constraint_name: string;
  source_columns: string[];
  target_columns: string[];
  column_pairs: ColumnPairMapping[];
  on_delete?: string | null;
  on_update?: string | null;
  is_composite: boolean;
  is_self_loop: boolean;
  is_parallel: boolean;
  parallel_index: number;
  parallel_total: number;
  is_selected?: boolean;
  is_highlighted?: boolean;
}

export interface ViewportState {
  x: number;
  y: number;
  zoom: number;
}

export interface GraphFilterState {
  searchQuery: string;
  selectedNamespace: string | null;
  hideIsolated: boolean;
}

export interface LayoutOptions {
  orientation: "LR" | "TB";
  rankSeparation: number;
  nodeSeparation: number;
}

export interface GraphBounds {
  minX: number;
  minY: number;
  maxX: number;
  maxY: number;
  width: number;
  height: number;
}

export interface RawGraphData {
  database_name: string;
  engine: string;
  nodes: Array<{
    table_id: string;
    namespace: string;
    name: string;
    columns?: ColumnItem[];
  }>;
  edges: Array<{
    edge_id: string;
    source_table_id: string;
    source_table_name: string;
    target_table_id: string;
    target_table_name: string;
    constraint_name: string;
    source_columns: string[];
    target_columns: string[];
    on_delete?: string | null;
    on_update?: string | null;
  }>;
}
