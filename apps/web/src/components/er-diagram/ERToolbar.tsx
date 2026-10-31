"use client";

import * as React from "react";
import {
  Maximize2,
  Minimize2,
  RotateCcw,
  ZoomIn,
  ZoomOut,
  LayoutGrid,
  Columns,
  Table as TableIcon,
  HelpCircle,
  Network,
  SlidersHorizontal,
} from "lucide-react";
import { Button } from "@/components/ui/button";

interface ERToolbarProps {
  zoom: number;
  orientation: "LR" | "TB";
  viewMode: "canvas" | "table";
  showLegend: boolean;
  showFilters: boolean;
  onZoomIn: () => void;
  onZoomOut: () => void;
  onFitToView: () => void;
  onResetView: () => void;
  onAutoLayout: () => void;
  onToggleOrientation: () => void;
  onToggleViewMode: () => void;
  onToggleLegend: () => void;
  onToggleFilters: () => void;
}

export const ERToolbar: React.FC<ERToolbarProps> = ({
  zoom,
  orientation,
  viewMode,
  showLegend,
  showFilters,
  onZoomIn,
  onZoomOut,
  onFitToView,
  onResetView,
  onAutoLayout,
  onToggleOrientation,
  onToggleViewMode,
  onToggleLegend,
  onToggleFilters,
}) => {
  return (
    <div className="flex flex-wrap items-center justify-between gap-2 p-2 bg-slate-900/90 backdrop-blur-md border border-slate-800 rounded-lg shadow-xl text-slate-200">
      {/* Left Section: View Mode & Filters */}
      <div className="flex items-center gap-1">
        <Button
          variant={viewMode === "canvas" ? "secondary" : "ghost"}
          size="sm"
          onClick={onToggleViewMode}
          className="text-xs font-medium gap-1.5 h-8 px-2.5"
          aria-label="Switch between Visual Canvas and Accessible Table view"
          title="Switch between Visual Canvas and Accessible Table view"
        >
          {viewMode === "canvas" ? (
            <>
              <Network className="w-3.5 h-3.5 text-blue-400" />
              <span>Visual Canvas</span>
            </>
          ) : (
            <>
              <TableIcon className="w-3.5 h-3.5 text-emerald-400" />
              <span>Accessible Table</span>
            </>
          )}
        </Button>

        <div className="h-4 w-px bg-slate-800 mx-1" />

        <Button
          variant={showFilters ? "secondary" : "ghost"}
          size="sm"
          onClick={onToggleFilters}
          className="h-8 px-2 gap-1 text-xs"
          aria-label="Toggle search and filters bar"
          title="Toggle search and filters bar"
        >
          <SlidersHorizontal className="w-3.5 h-3.5" />
          <span className="hidden sm:inline">Filters</span>
        </Button>

        <Button
          variant={showLegend ? "secondary" : "ghost"}
          size="sm"
          onClick={onToggleLegend}
          className="h-8 px-2 gap-1 text-xs"
          aria-label="Toggle diagram legend"
          title="Diagram Legend & Key"
        >
          <HelpCircle className="w-3.5 h-3.5" />
          <span className="hidden sm:inline">Legend</span>
        </Button>
      </div>

      {/* Right Section: Canvas Viewport & Layout Controls (Visible in Canvas mode) */}
      {viewMode === "canvas" && (
        <div className="flex items-center gap-1">
          <Button
            variant="ghost"
            size="sm"
            onClick={onZoomOut}
            className="h-8 w-8 p-0"
            aria-label="Zoom out"
            title="Zoom Out (-)"
          >
            <ZoomOut className="w-3.5 h-3.5" />
          </Button>

          <span className="text-xs font-mono text-slate-400 px-1 w-12 text-center select-none">
            {Math.round(zoom * 100)}%
          </span>

          <Button
            variant="ghost"
            size="sm"
            onClick={onZoomIn}
            className="h-8 w-8 p-0"
            aria-label="Zoom in"
            title="Zoom In (+)"
          >
            <ZoomIn className="w-3.5 h-3.5" />
          </Button>

          <div className="h-4 w-px bg-slate-800 mx-1" />

          <Button
            variant="ghost"
            size="sm"
            onClick={onFitToView}
            className="h-8 w-8 p-0"
            aria-label="Fit graph to view"
            title="Fit to View (F)"
          >
            <Maximize2 className="w-3.5 h-3.5" />
          </Button>

          <Button
            variant="ghost"
            size="sm"
            onClick={onResetView}
            className="h-8 w-8 p-0"
            aria-label="Reset viewport to 100%"
            title="Reset View (R)"
          >
            <RotateCcw className="w-3.5 h-3.5" />
          </Button>

          <div className="h-4 w-px bg-slate-800 mx-1" />

          <Button
            variant="ghost"
            size="sm"
            onClick={onToggleOrientation}
            className="h-8 px-2 gap-1 text-xs"
            aria-label={`Switch layout orientation (currently ${orientation === "LR" ? "Horizontal" : "Vertical"})`}
            title="Toggle Layout Orientation"
          >
            {orientation === "LR" ? (
              <>
                <Columns className="w-3.5 h-3.5 text-indigo-400" />
                <span className="hidden md:inline">Horizontal</span>
              </>
            ) : (
              <>
                <LayoutGrid className="w-3.5 h-3.5 text-indigo-400" />
                <span className="hidden md:inline">Vertical</span>
              </>
            )}
          </Button>

          <Button
            variant="outline"
            size="sm"
            onClick={onAutoLayout}
            className="h-8 px-2.5 text-xs bg-slate-800 border-slate-700 hover:bg-slate-700 text-slate-100"
            aria-label="Recompute deterministic auto-layout"
            title="Deterministic Re-layout"
          >
            <span>Auto-Layout</span>
          </Button>
        </div>
      )}
    </div>
  );
};
