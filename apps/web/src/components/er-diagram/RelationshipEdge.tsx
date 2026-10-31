"use client";

import * as React from "react";
import { CanvasEdge, CanvasNode } from "./types";

interface RelationshipEdgeProps {
  edge: CanvasEdge;
  sourceNode?: CanvasNode;
  targetNode?: CanvasNode;
  isSelected?: boolean;
  isHighlighted?: boolean;
  onSelect: (edgeId: string) => void;
}

export const RelationshipEdge: React.FC<RelationshipEdgeProps> = ({
  edge,
  sourceNode,
  targetNode,
  isSelected = false,
  isHighlighted = false,
  onSelect,
}) => {
  if (!sourceNode || !targetNode) return null;

  const handleClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    onSelect(edge.id);
  };

  // Edge styling
  let strokeColor = "#64748b"; // slate-500
  let strokeWidth = 1.5;
  let strokeDasharray: string | undefined = undefined;

  if (isSelected) {
    strokeColor = "#3b82f6"; // blue-500
    strokeWidth = 3;
  } else if (isHighlighted) {
    strokeColor = "#06b6d4"; // cyan-500
    strokeWidth = 2.5;
  }

  if (edge.is_composite) {
    strokeDasharray = "5,3";
  }

  // Self-referencing relationship
  if (edge.is_self_loop) {
    const startX = sourceNode.x + sourceNode.width;
    const startY = sourceNode.y + 24;
    const endX = sourceNode.x + sourceNode.width;
    const endY = sourceNode.y + 50;

    const offset = 40 + (edge.parallel_index || 0) * 20;
    const pathD = `M ${startX} ${startY} C ${startX + offset} ${startY - 15}, ${startX + offset} ${endY + 15}, ${endX} ${endY}`;
    const midX = startX + offset;
    const midY = (startY + endY) / 2;

    return (
      <g
        id={`edge-${edge.id}`}
        className="cursor-pointer"
        onClick={handleClick}
        role="button"
        tabIndex={0}
        aria-label={`Self-referencing relationship ${edge.constraint_name} on ${edge.source_table_name}`}
        onKeyDown={(e) => {
          if (e.key === "Enter" || e.key === " ") {
            e.preventDefault();
            onSelect(edge.id);
          }
        }}
      >
        <title>{`${edge.constraint_name}: ${edge.source_columns.join(", ")} -> ${edge.target_columns.join(", ")}`}</title>

        {/* Wide invisible hit area */}
        <path d={pathD} fill="none" stroke="transparent" strokeWidth={16} />

        {/* Visible relationship edge */}
        <path
          d={pathD}
          fill="none"
          stroke={strokeColor}
          strokeWidth={strokeWidth}
          strokeDasharray={strokeDasharray}
          markerEnd={isSelected ? "url(#arrow-selected)" : isHighlighted ? "url(#arrow-highlighted)" : "url(#arrow-default)"}
        />

        {/* Composite badge or constraint label */}
        {edge.is_composite && (
          <g transform={`translate(${midX}, ${midY})`}>
            <rect x={-20} y={-9} width={40} height={18} rx={4} fill="#1e293b" stroke={strokeColor} strokeWidth={1} />
            <text x={0} y={3} fill="#93c5fd" fontSize={9} fontWeight={600} textAnchor="middle" fontFamily="ui-monospace, monospace">
              {edge.source_columns.length} cols
            </text>
          </g>
        )}
      </g>
    );
  }

  // Cross-table directed edge
  // Compute best attachment points
  const sourceCenterX = sourceNode.x + sourceNode.width / 2;
  const targetCenterX = targetNode.x + targetNode.width / 2;

  let x1: number, y1: number, x2: number, y2: number;

  if (sourceCenterX < targetCenterX - 40) {
    // Source is to the left of Target: exit right of source, enter left of target
    x1 = sourceNode.x + sourceNode.width;
    y1 = sourceNode.y + sourceNode.height / 2;
    x2 = targetNode.x;
    y2 = targetNode.y + targetNode.height / 2;
  } else if (sourceCenterX > targetCenterX + 40) {
    // Source is to the right of Target: exit left of source, enter right of target
    x1 = sourceNode.x;
    y1 = sourceNode.y + sourceNode.height / 2;
    x2 = targetNode.x + targetNode.width;
    y2 = targetNode.y + targetNode.height / 2;
  } else {
    // Vertically stacked
    if (sourceNode.y < targetNode.y) {
      x1 = sourceCenterX;
      y1 = sourceNode.y + sourceNode.height;
      x2 = targetCenterX;
      y2 = targetNode.y;
    } else {
      x1 = sourceCenterX;
      y1 = sourceNode.y;
      x2 = targetCenterX;
      y2 = targetNode.y + targetNode.height;
    }
  }

  // Offset parallel edges perpendicularly
  let cx1 = (x1 + x2) / 2;
  let cy1 = y1;
  let cx2 = (x1 + x2) / 2;
  let cy2 = y2;

  if (edge.is_parallel && edge.parallel_total > 1) {
    const shift = (edge.parallel_index - (edge.parallel_total - 1) / 2) * 28;
    cy1 += shift;
    cy2 += shift;
  }

  const pathD = `M ${x1} ${y1} C ${cx1} ${cy1}, ${cx2} ${cy2}, ${x2} ${y2}`;
  const midX = (x1 + x2) / 2;
  const midY = (cy1 + cy2) / 2;

  return (
    <g
      id={`edge-${edge.id}`}
      className="cursor-pointer"
      onClick={handleClick}
      role="button"
      tabIndex={0}
      aria-label={`Foreign key ${edge.constraint_name} from ${edge.source_table_name} to ${edge.target_table_name}`}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          onSelect(edge.id);
        }
      }}
    >
      <title>{`${edge.constraint_name}: ${edge.source_table_name}(${edge.source_columns.join(", ")}) -> ${edge.target_table_name}(${edge.target_columns.join(", ")})`}</title>

      {/* Invisible wider hit path */}
      <path d={pathD} fill="none" stroke="transparent" strokeWidth={18} />

      {/* Visible directed edge */}
      <path
        d={pathD}
        fill="none"
        stroke={strokeColor}
        strokeWidth={strokeWidth}
        strokeDasharray={strokeDasharray}
        markerEnd={isSelected ? "url(#arrow-selected)" : isHighlighted ? "url(#arrow-highlighted)" : "url(#arrow-default)"}
      />

      {/* Composite or Parallel Badge Pill */}
      {(edge.is_composite || edge.is_parallel) && (
        <g transform={`translate(${midX}, ${midY})`}>
          <rect
            x={-24}
            y={-9}
            width={48}
            height={18}
            rx={4}
            fill="#0f172a"
            stroke={strokeColor}
            strokeWidth={1}
          />
          <text
            x={0}
            y={3}
            fill={edge.is_composite ? "#93c5fd" : "#cbd5e1"}
            fontSize={9}
            fontWeight={600}
            textAnchor="middle"
            fontFamily="ui-monospace, monospace"
          >
            {edge.is_composite ? `${edge.source_columns.length} cols` : `FK #${edge.parallel_index + 1}`}
          </text>
        </g>
      )}
    </g>
  );
};
