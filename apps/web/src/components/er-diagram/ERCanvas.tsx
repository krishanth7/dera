"use client";

import * as React from "react";
import { CanvasEdge, CanvasNode, ViewportState } from "./types";
import { TableNode } from "./TableNode";
import { RelationshipEdge } from "./RelationshipEdge";

interface ERCanvasProps {
  nodes: CanvasNode[];
  edges: CanvasEdge[];
  selectedNodeId: string | null;
  selectedEdgeId: string | null;
  viewport: ViewportState;
  onViewportChange: (viewport: ViewportState) => void;
  onSelectNode: (nodeId: string | null) => void;
  onSelectEdge: (edgeId: string | null) => void;
  onUpdateNodePosition: (nodeId: string, x: number, y: number) => void;
}

export const ERCanvas: React.FC<ERCanvasProps> = ({
  nodes,
  edges,
  selectedNodeId,
  selectedEdgeId,
  viewport,
  onViewportChange,
  onSelectNode,
  onSelectEdge,
  onUpdateNodePosition,
}) => {
  const containerRef = React.useRef<HTMLDivElement>(null);

  // Dragging state (panning canvas or dragging node)
  const [isPanning, setIsPanning] = React.useState<boolean>(false);
  const [panStart, setPanStart] = React.useState<{ x: number; y: number }>({ x: 0, y: 0 });

  const [draggingNodeId, setDraggingNodeId] = React.useState<string | null>(null);
  const [nodeDragOffset, setNodeDragOffset] = React.useState<{ x: number; y: number }>({ x: 0, y: 0 });

  // Compute node map for quick lookup
  const nodeMap = React.useMemo(() => {
    const map = new Map<string, CanvasNode>();
    nodes.forEach((n) => map.set(n.id, n));
    return map;
  }, [nodes]);

  // Compute highlighted nodes and edges based on selection
  const { highlightedNodeIds, highlightedEdgeIds } = React.useMemo(() => {
    const nodeIds = new Set<string>();
    const edgeIds = new Set<string>();

    if (selectedNodeId) {
      edges.forEach((e) => {
        if (e.source_table_id === selectedNodeId) {
          edgeIds.add(e.id);
          nodeIds.add(e.target_table_id);
        }
        if (e.target_table_id === selectedNodeId) {
          edgeIds.add(e.id);
          nodeIds.add(e.source_table_id);
        }
      });
    } else if (selectedEdgeId) {
      const edge = edges.find((e) => e.id === selectedEdgeId);
      if (edge) {
        nodeIds.add(edge.source_table_id);
        nodeIds.add(edge.target_table_id);
      }
    }

    return { highlightedNodeIds: nodeIds, highlightedEdgeIds: edgeIds };
  }, [selectedNodeId, selectedEdgeId, edges]);

  // Handle Canvas Panning
  const handleMouseDown = (e: React.MouseEvent) => {
    if (e.button !== 0) return; // Only primary mouse button
    setIsPanning(true);
    setPanStart({ x: e.clientX - viewport.x, y: e.clientY - viewport.y });
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (draggingNodeId) {
      // Repositioning a specific table node
      const currentZoom = viewport.zoom;
      const newX = (e.clientX - viewport.x) / currentZoom - nodeDragOffset.x;
      const newY = (e.clientY - viewport.y) / currentZoom - nodeDragOffset.y;
      onUpdateNodePosition(draggingNodeId, Math.round(newX), Math.round(newY));
    } else if (isPanning) {
      // Panning the entire canvas
      onViewportChange({
        ...viewport,
        x: e.clientX - panStart.x,
        y: e.clientY - panStart.y,
      });
    }
  };

  const handleMouseUp = () => {
    setIsPanning(false);
    setDraggingNodeId(null);
  };

  // Handle Zoom via Mouse Wheel centered at cursor
  const handleWheel = (e: React.WheelEvent) => {
    e.preventDefault();
    if (!containerRef.current) return;

    const rect = containerRef.current.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    const mouseY = e.clientY - rect.top;

    const zoomFactor = e.deltaY < 0 ? 1.1 : 0.9;
    const newZoom = Math.min(Math.max(viewport.zoom * zoomFactor, 0.2), 2.5);

    // Zoom towards cursor
    const newX = mouseX - (mouseX - viewport.x) * (newZoom / viewport.zoom);
    const newY = mouseY - (mouseY - viewport.y) * (newZoom / viewport.zoom);

    onViewportChange({
      x: newX,
      y: newY,
      zoom: newZoom,
    });
  };

  // Node Drag Start handler
  const handleNodeDragStart = (nodeId: string, e: React.MouseEvent) => {
    const node = nodeMap.get(nodeId);
    if (!node) return;

    const currentZoom = viewport.zoom;
    const clickCanvasX = (e.clientX - viewport.x) / currentZoom;
    const clickCanvasY = (e.clientY - viewport.y) / currentZoom;

    setDraggingNodeId(nodeId);
    setNodeDragOffset({
      x: clickCanvasX - node.x,
      y: clickCanvasY - node.y,
    });
    onSelectNode(nodeId);
  };

  // Background Canvas Click (Deselect)
  const handleBackgroundClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget || (e.target as HTMLElement).tagName === "svg") {
      onSelectNode(null);
      onSelectEdge(null);
    }
  };

  return (
    <div
      ref={containerRef}
      className="relative w-full h-full overflow-hidden bg-slate-950 select-none cursor-grab active:cursor-grabbing"
      onMouseDown={handleMouseDown}
      onMouseMove={handleMouseMove}
      onMouseUp={handleMouseUp}
      onMouseLeave={handleMouseUp}
      onWheel={handleWheel}
      onClick={handleBackgroundClick}
      role="region"
      aria-label="Interactive Entity-Relationship diagram canvas"
      tabIndex={0}
    >
      <svg
        className="w-full h-full block"
        style={{ touchAction: "none" }}
      >
        <defs>
          {/* Subtle Grid Pattern */}
          <pattern id="er-grid" width={40} height={40} patternUnits="userSpaceOnUse">
            <circle cx={20} cy={20} r={1} fill="#1e293b" />
          </pattern>

          {/* Directed Relationship Arrow Markers */}
          <marker
            id="arrow-default"
            viewBox="0 0 10 10"
            refX={8}
            refY={5}
            markerWidth={6}
            markerHeight={6}
            orient="auto-start-reverse"
          >
            <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#64748b" />
          </marker>

          <marker
            id="arrow-selected"
            viewBox="0 0 10 10"
            refX={8}
            refY={5}
            markerWidth={7}
            markerHeight={7}
            orient="auto-start-reverse"
          >
            <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#3b82f6" />
          </marker>

          <marker
            id="arrow-highlighted"
            viewBox="0 0 10 10"
            refX={8}
            refY={5}
            markerWidth={6.5}
            markerHeight={6.5}
            orient="auto-start-reverse"
          >
            <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#06b6d4" />
          </marker>
        </defs>

        {/* Canvas Background Grid */}
        <rect width="100%" height="100%" fill="url(#er-grid)" />

        {/* Viewport Transform Group */}
        <g transform={`translate(${viewport.x}, ${viewport.y}) scale(${viewport.zoom})`}>
          {/* 1. Edge Layer (rendered underneath nodes) */}
          <g id="er-edges-layer">
            {edges.map((edge) => (
              <RelationshipEdge
                key={edge.id}
                edge={edge}
                sourceNode={nodeMap.get(edge.source_table_id)}
                targetNode={nodeMap.get(edge.target_table_id)}
                isSelected={edge.id === selectedEdgeId}
                isHighlighted={highlightedEdgeIds.has(edge.id)}
                onSelect={(id) => {
                  onSelectEdge(id);
                  onSelectNode(null);
                }}
              />
            ))}
          </g>

          {/* 2. Node Layer */}
          <g id="er-nodes-layer">
            {nodes.map((node) => (
              <TableNode
                key={node.id}
                node={node}
                isSelected={node.id === selectedNodeId}
                isHighlighted={highlightedNodeIds.has(node.id)}
                onSelect={(id) => {
                  onSelectNode(id);
                  onSelectEdge(null);
                }}
                onDragStart={handleNodeDragStart}
              />
            ))}
          </g>
        </g>
      </svg>
    </div>
  );
};
