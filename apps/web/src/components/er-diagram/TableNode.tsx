"use client";

import * as React from "react";
import { CanvasNode } from "./types";
import { NODE_HEADER_HEIGHT, ROW_HEIGHT, MAX_VISIBLE_COLUMNS } from "./layout";

interface TableNodeProps {
  node: CanvasNode;
  isSelected?: boolean;
  isHighlighted?: boolean;
  onSelect: (nodeId: string) => void;
  onDragStart?: (nodeId: string, event: React.MouseEvent) => void;
}

export const TableNode: React.FC<TableNodeProps> = ({
  node,
  isSelected = false,
  isHighlighted = false,
  onSelect,
  onDragStart,
}) => {
  const visibleColumns = (node.columns || []).slice(0, MAX_VISIBLE_COLUMNS);
  const remainingCount = (node.columns || []).length - visibleColumns.length;

  const handleMouseDown = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (onDragStart) {
      onDragStart(node.id, e);
    }
  };

  const handleClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    onSelect(node.id);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      onSelect(node.id);
    }
  };

  // Card border styling based on state
  let strokeColor = "#334155"; // slate-700
  let strokeWidth = 1.5;
  if (isSelected) {
    strokeColor = "#3b82f6"; // blue-500
    strokeWidth = 2.5;
  } else if (isHighlighted) {
    strokeColor = "#06b6d4"; // cyan-500
    strokeWidth = 2;
  }

  return (
    <g
      id={`table-node-${node.id}`}
      transform={`translate(${node.x}, ${node.y})`}
      className="cursor-pointer select-none transition-transform"
      role="button"
      tabIndex={0}
      aria-label={`Table ${node.namespace}.${node.name}, ${node.columns.length} columns`}
      onClick={handleClick}
      onMouseDown={handleMouseDown}
      onKeyDown={handleKeyDown}
    >
      {/* Outer Card Background */}
      <rect
        width={node.width}
        height={node.height}
        rx={8}
        ry={8}
        fill="#0f172a" // slate-900
        stroke={strokeColor}
        strokeWidth={strokeWidth}
        filter={isSelected ? "drop-shadow(0 0 8px rgba(59, 130, 246, 0.4))" : undefined}
      />

      {/* Header Background */}
      <path
        d={`M 0 8 Q 0 0 8 0 L ${node.width - 8} 0 Q ${node.width} 0 ${node.width} 8 L ${node.width} ${NODE_HEADER_HEIGHT} L 0 ${NODE_HEADER_HEIGHT} Z`}
        fill={isSelected ? "#1e293b" : "#1e293b"}
        stroke="#334155"
        strokeWidth={1}
      />

      {/* Namespace Tag */}
      <text
        x={12}
        y={16}
        fill="#94a3b8" // slate-400
        fontSize={10}
        fontFamily="ui-monospace, monospace"
        fontWeight={500}
      >
        {node.namespace}
      </text>

      {/* Table Name */}
      <text
        x={12}
        y={34}
        fill="#f8fafc" // slate-50
        fontSize={13}
        fontWeight={600}
        fontFamily="system-ui, sans-serif"
      >
        {node.name.length > 22 ? `${node.name.substring(0, 20)}...` : node.name}
      </text>

      {/* Table Type or Column Count Badge in Header */}
      <rect
        x={node.width - 56}
        y={12}
        width={44}
        height={18}
        rx={4}
        ry={4}
        fill="#334155"
      />
      <text
        x={node.width - 34}
        y={24}
        fill="#cbd5e1"
        fontSize={9}
        fontWeight={500}
        textAnchor="middle"
        fontFamily="ui-monospace, monospace"
      >
        {node.columns.length} cols
      </text>

      {/* Column Rows */}
      {visibleColumns.map((col, index) => {
        const rowY = NODE_HEADER_HEIGHT + index * ROW_HEIGHT;
        const isAlternate = index % 2 === 1;

        return (
          <g key={col.name} transform={`translate(0, ${rowY})`}>
            {/* Optional subtle row background */}
            {isAlternate && (
              <rect
                x={1}
                y={0}
                width={node.width - 2}
                height={ROW_HEIGHT}
                fill="#1e293b"
                fillOpacity={0.4}
              />
            )}

            {/* PK Indicator */}
            {col.is_primary_key && (
              <g transform="translate(10, 4)">
                <rect width={20} height={13} rx={2} fill="#d97706" />
                <text
                  x={10}
                  y={10}
                  fill="#ffffff"
                  fontSize={8}
                  fontWeight={700}
                  textAnchor="middle"
                  fontFamily="system-ui, sans-serif"
                >
                  PK
                </text>
              </g>
            )}

            {/* FK Indicator */}
            {col.is_foreign_key && (
              <g transform={`translate(${col.is_primary_key ? 34 : 10}, 4)`}>
                <rect width={20} height={13} rx={2} fill="#2563eb" />
                <text
                  x={10}
                  y={10}
                  fill="#ffffff"
                  fontSize={8}
                  fontWeight={700}
                  textAnchor="middle"
                  fontFamily="system-ui, sans-serif"
                >
                  FK
                </text>
              </g>
            )}

            {/* Column Name */}
            <text
              x={col.is_primary_key && col.is_foreign_key ? 60 : col.is_primary_key || col.is_foreign_key ? 36 : 12}
              y={14}
              fill={col.is_primary_key ? "#fef08a" : "#f1f5f9"}
              fontSize={11}
              fontFamily="ui-monospace, monospace"
            >
              {col.name.length > 16 ? `${col.name.substring(0, 14)}..` : col.name}
            </text>

            {/* Native Type */}
            <text
              x={node.width - 12}
              y={14}
              fill="#64748b"
              fontSize={10}
              textAnchor="end"
              fontFamily="ui-monospace, monospace"
            >
              {col.native_type.length > 12
                ? `${col.native_type.substring(0, 10)}..`
                : col.native_type}
            </text>
          </g>
        );
      })}

      {/* Overflow Footer if columns > MAX_VISIBLE_COLUMNS */}
      {remainingCount > 0 && (
        <g transform={`translate(0, ${NODE_HEADER_HEIGHT + visibleColumns.length * ROW_HEIGHT})`}>
          <line x1={0} y1={0} x2={node.width} y2={0} stroke="#334155" strokeWidth={1} />
          <text
            x={node.width / 2}
            y={17}
            fill="#94a3b8"
            fontSize={10}
            fontStyle="italic"
            textAnchor="middle"
            fontFamily="system-ui, sans-serif"
          >
            +{remainingCount} more columns...
          </text>
        </g>
      )}
    </g>
  );
};
