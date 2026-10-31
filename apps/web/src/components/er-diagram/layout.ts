/**
 * DERA — Phase 7.4 Deterministic ER Diagram Layout Engine
 * Force-free, cycle-aware, layered topological ranking for database schemas.
 */

import {
  CanvasEdge,
  CanvasNode,
  ColumnPairMapping,
  GraphBounds,
  LayoutOptions,
  RawGraphData,
} from "./types";

export const DEFAULT_NODE_WIDTH = 260;
export const NODE_HEADER_HEIGHT = 44;
export const ROW_HEIGHT = 22;
export const NODE_FOOTER_HEIGHT = 26;
export const MAX_VISIBLE_COLUMNS = 8;
export const DEFAULT_RANK_SEPARATION = 100;
export const DEFAULT_NODE_SEPARATION = 40;
export const CANVAS_PADDING = 60;

/**
 * Calculates standard card dimensions for a node based on column count.
 */
export function calculateNodeDimensions(columnCount: number): { width: number; height: number } {
  const visibleCols = Math.min(columnCount, MAX_VISIBLE_COLUMNS);
  const height =
    NODE_HEADER_HEIGHT +
    visibleCols * ROW_HEIGHT +
    (columnCount > MAX_VISIBLE_COLUMNS ? NODE_FOOTER_HEIGHT : 12);
  return { width: DEFAULT_NODE_WIDTH, height };
}

/**
 * Processes raw graph payload, resolving composite keys, parallel edges, and self-loops.
 */
export function buildGraphModel(raw: RawGraphData): {
  nodes: CanvasNode[];
  edges: CanvasEdge[];
} {
  // 1. Sort nodes canonically by (namespace, name, table_id) to guarantee determinism
  const sortedRawNodes = [...raw.nodes].sort((a, b) => {
    const nsCompare = a.namespace.localeCompare(b.namespace);
    if (nsCompare !== 0) return nsCompare;
    const nameCompare = a.name.localeCompare(b.name);
    if (nameCompare !== 0) return nameCompare;
    return a.table_id.localeCompare(b.table_id);
  });

  // 2. Identify foreign key columns across nodes
  const fkColumnsByTable = new Map<string, Set<string>>();
  raw.edges.forEach((edge) => {
    if (!fkColumnsByTable.has(edge.source_table_id)) {
      fkColumnsByTable.set(edge.source_table_id, new Set());
    }
    edge.source_columns.forEach((col) => {
      fkColumnsByTable.get(edge.source_table_id)!.add(col);
    });
  });

  // 3. Construct CanvasNodes with computed dimensions
  const nodes: CanvasNode[] = sortedRawNodes.map((n) => {
    const fks = fkColumnsByTable.get(n.table_id) || new Set();
    const cols = (n.columns || []).map((c) => ({
      ...c,
      is_foreign_key: fks.has(c.name) || Boolean(c.is_foreign_key),
    }));
    const hasPk = cols.some((c) => c.is_primary_key);
    const dims = calculateNodeDimensions(cols.length);

    return {
      id: n.table_id,
      name: n.name,
      namespace: n.namespace,
      columns: cols,
      has_primary_key: hasPk,
      x: 0,
      y: 0,
      width: dims.width,
      height: dims.height,
    };
  });

  // 4. Group edges by table pair to detect parallel edges and self-loops
  // Pair key: "source_id->target_id"
  const edgeGroups = new Map<string, typeof raw.edges>();
  raw.edges.forEach((edge) => {
    const key = `${edge.source_table_id}->${edge.target_table_id}`;
    if (!edgeGroups.has(key)) {
      edgeGroups.set(key, []);
    }
    edgeGroups.get(key)!.push(edge);
  });

  // 5. Construct CanvasEdges with parallel index and composite mapping
  const edges: CanvasEdge[] = [];
  edgeGroups.forEach((group) => {
    // Sort edges within parallel group deterministically by constraint_name, edge_id
    const sortedGroup = [...group].sort((a, b) => {
      const cComp = a.constraint_name.localeCompare(b.constraint_name);
      if (cComp !== 0) return cComp;
      return a.edge_id.localeCompare(b.edge_id);
    });

    const total = sortedGroup.length;
    sortedGroup.forEach((edge, idx) => {
      const isSelfLoop = edge.source_table_id === edge.target_table_id;
      const isComposite = edge.source_columns.length > 1;

      // Ordered column pairs: (source_col[i] -> target_col[i])
      const column_pairs: ColumnPairMapping[] = [];
      const len = Math.min(edge.source_columns.length, edge.target_columns.length);
      for (let i = 0; i < len; i++) {
        column_pairs.push({
          source_column: edge.source_columns[i],
          target_column: edge.target_columns[i],
        });
      }

      edges.push({
        id: edge.edge_id,
        source_table_id: edge.source_table_id,
        source_table_name: edge.source_table_name,
        target_table_id: edge.target_table_id,
        target_table_name: edge.target_table_name,
        constraint_name: edge.constraint_name,
        source_columns: edge.source_columns,
        target_columns: edge.target_columns,
        column_pairs,
        on_delete: edge.on_delete,
        on_update: edge.on_update,
        is_composite: isComposite,
        is_self_loop: isSelfLoop,
        is_parallel: total > 1,
        parallel_index: idx,
        parallel_total: total,
      });
    });
  });

  // Sort edges deterministically by (source_table_id, target_table_id, constraint_name, id)
  edges.sort((a, b) => {
    const sComp = a.source_table_id.localeCompare(b.source_table_id);
    if (sComp !== 0) return sComp;
    const tComp = a.target_table_id.localeCompare(b.target_table_id);
    if (tComp !== 0) return tComp;
    const cComp = a.constraint_name.localeCompare(b.constraint_name);
    if (cComp !== 0) return cComp;
    return a.id.localeCompare(b.id);
  });

  return { nodes, edges };
}

/**
 * Computes deterministic layered topological coordinates for all nodes in the graph.
 */
export function computeDeterministicLayout(
  nodes: CanvasNode[],
  edges: CanvasEdge[],
  options: LayoutOptions = {
    orientation: "LR",
    rankSeparation: DEFAULT_RANK_SEPARATION,
    nodeSeparation: DEFAULT_NODE_SEPARATION,
  }
): {
  positionedNodes: CanvasNode[];
  bounds: GraphBounds;
} {
  if (nodes.length === 0) {
    return {
      positionedNodes: [],
      bounds: { minX: 0, minY: 0, maxX: 0, maxY: 0, width: 0, height: 0 },
    };
  }

  const nodeMap = new Map<string, CanvasNode>();
  nodes.forEach((n) => nodeMap.set(n.id, { ...n }));

  // Adjacency graph for topological ranking (source -> targets)
  // FK direction: source (referencing child) -> target (referenced parent)
  const adj = new Map<string, Set<string>>();
  const inDegree = new Map<string, number>();

  nodes.forEach((n) => {
    adj.set(n.id, new Set());
    inDegree.set(n.id, 0);
  });

  // Filter out self-loops and remove backward cycle edges for ranking
  edges.forEach((e) => {
    if (e.source_table_id !== e.target_table_id) {
      if (nodeMap.has(e.source_table_id) && nodeMap.has(e.target_table_id)) {
        adj.get(e.source_table_id)!.add(e.target_table_id);
      }
    }
  });

  // Calculate in-degrees
  adj.forEach((targets) => {
    targets.forEach((tgt) => {
      inDegree.set(tgt, (inDegree.get(tgt) || 0) + 1);
    });
  });

  // Compute ranks using longest path / BFS
  const ranks = new Map<string, number>();
  const queue: string[] = [];

  // Nodes with in-degree 0 start at rank 0
  nodes.forEach((n) => {
    if ((inDegree.get(n.id) || 0) === 0) {
      ranks.set(n.id, 0);
      queue.push(n.id);
    }
  });

  // If graph is entirely cyclic or remaining nodes have no in-degree 0, seed with first node
  if (queue.length === 0 && nodes.length > 0) {
    const firstNode = nodes[0].id;
    ranks.set(firstNode, 0);
    queue.push(firstNode);
  }

  // Assign ranks
  const visited = new Set<string>();
  while (queue.length > 0) {
    const u = queue.shift()!;
    visited.add(u);
    const currentRank = ranks.get(u) || 0;

    const neighbors = Array.from(adj.get(u) || []).sort();
    for (const v of neighbors) {
      const existingRank = ranks.get(v);
      const nextRank = currentRank + 1;
      if (existingRank === undefined || nextRank > existingRank) {
        ranks.set(v, nextRank);
      }
      if (!visited.has(v) && !queue.includes(v)) {
        queue.push(v);
      }
    }
  }

  // Any unreached disconnected nodes get rank 0
  nodes.forEach((n) => {
    if (!ranks.has(n.id)) {
      ranks.set(n.id, 0);
    }
  });

  // Group nodes by rank
  const rankBuckets = new Map<number, CanvasNode[]>();
  nodes.forEach((n) => {
    const r = ranks.get(n.id) || 0;
    if (!rankBuckets.has(r)) {
      rankBuckets.set(r, []);
    }
    rankBuckets.get(r)!.push(nodeMap.get(n.id)!);
  });

  // Sort each rank bucket deterministically by (namespace, name, id)
  const sortedRanks = Array.from(rankBuckets.keys()).sort((a, b) => a - b);
  sortedRanks.forEach((r) => {
    rankBuckets.get(r)!.sort((a, b) => {
      const nsComp = a.namespace.localeCompare(b.namespace);
      if (nsComp !== 0) return nsComp;
      const nameComp = a.name.localeCompare(b.name);
      if (nameComp !== 0) return nameComp;
      return a.id.localeCompare(b.id);
    });
  });

  // Position nodes
  const positionedNodes: CanvasNode[] = [];
  let minX = Infinity;
  let minY = Infinity;
  let maxX = -Infinity;
  let maxY = -Infinity;

  if (options.orientation === "LR") {
    // Left-to-Right: ranks along X axis, nodes in rank along Y axis
    sortedRanks.forEach((r) => {
      const bucket = rankBuckets.get(r)!;
      const x = CANVAS_PADDING + r * (DEFAULT_NODE_WIDTH + options.rankSeparation);

      let currentY = CANVAS_PADDING;
      bucket.forEach((node) => {
        node.x = x;
        node.y = currentY;

        minX = Math.min(minX, node.x);
        minY = Math.min(minY, node.y);
        maxX = Math.max(maxX, node.x + node.width);
        maxY = Math.max(maxY, node.y + node.height);

        currentY += node.height + options.nodeSeparation;
        positionedNodes.push(node);
      });
    });
  } else {
    // Top-to-Bottom: ranks along Y axis, nodes in rank along X axis
    sortedRanks.forEach((r) => {
      const bucket = rankBuckets.get(r)!;
      let currentX = CANVAS_PADDING;

      // Find max height in this rank for consistent Y spacing
      const maxHeight = Math.max(...bucket.map((n) => n.height));

      bucket.forEach((node) => {
        const y = CANVAS_PADDING + r * (maxHeight + options.rankSeparation);
        node.x = currentX;
        node.y = y;

        minX = Math.min(minX, node.x);
        minY = Math.min(minY, node.y);
        maxX = Math.max(maxX, node.x + node.width);
        maxY = Math.max(maxY, node.y + node.height);

        currentX += node.width + options.nodeSeparation;
        positionedNodes.push(node);
      });
    });
  }

  // Bounds safety check
  if (!isFinite(minX)) minX = 0;
  if (!isFinite(minY)) minY = 0;
  if (!isFinite(maxX)) maxX = 0;
  if (!isFinite(maxY)) maxY = 0;

  const bounds: GraphBounds = {
    minX,
    minY,
    maxX,
    maxY,
    width: Math.max(0, maxX - minX + CANVAS_PADDING * 2),
    height: Math.max(0, maxY - minY + CANVAS_PADDING * 2),
  };

  return { positionedNodes, bounds };
}
