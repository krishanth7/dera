"use client";

import * as React from "react";
import { X, Key, ArrowRight, CornerDownRight, RefreshCw, Layers } from "lucide-react";
import { Button } from "@/components/ui/button";

interface GraphLegendProps {
  onClose: () => void;
}

export const GraphLegend: React.FC<GraphLegendProps> = ({ onClose }) => {
  return (
    <div className="p-4 bg-slate-900/95 backdrop-blur-md border border-slate-800 rounded-lg shadow-2xl text-xs text-slate-200 max-w-xs space-y-3">
      <div className="flex items-center justify-between border-b border-slate-800 pb-2">
        <span className="font-semibold text-slate-100 flex items-center gap-1.5">
          <Layers className="w-3.5 h-3.5 text-blue-400" />
          Diagram Legend & Semantics
        </span>
        <button
          onClick={onClose}
          className="text-slate-500 hover:text-slate-300 p-0.5 rounded"
          aria-label="Close legend"
        >
          <X className="w-3.5 h-3.5" />
        </button>
      </div>

      <div className="space-y-2.5">
        <div className="flex items-center gap-2">
          <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-amber-600 text-white">
            PK
          </span>
          <span className="text-slate-300">Primary Key column</span>
        </div>

        <div className="flex items-center gap-2">
          <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-blue-600 text-white">
            FK
          </span>
          <span className="text-slate-300">Foreign Key column</span>
        </div>

        <div className="flex items-center gap-2">
          <div className="w-6 h-0.5 bg-slate-400" />
          <ArrowRight className="w-3.5 h-3.5 text-slate-400 -ml-2" />
          <span className="text-slate-300">Foreign Key edge (Child → Parent)</span>
        </div>

        <div className="flex items-center gap-2">
          <div className="w-6 h-0.5 border-t border-dashed border-slate-400" />
          <span className="px-1 py-0.2 rounded text-[9px] font-mono bg-slate-800 text-blue-300 border border-slate-700">
            N cols
          </span>
          <span className="text-slate-300">Composite Foreign Key</span>
        </div>

        <div className="flex items-center gap-2">
          <RefreshCw className="w-3.5 h-3.5 text-slate-400" />
          <span className="text-slate-300">Self-referencing relationship</span>
        </div>

        <div className="flex items-center gap-2">
          <div className="w-4 h-4 rounded border-2 border-blue-500 bg-slate-800" />
          <span className="text-slate-300">Selected table or edge</span>
        </div>

        <div className="flex items-center gap-2">
          <div className="w-4 h-4 rounded border-2 border-cyan-500 bg-slate-800" />
          <span className="text-slate-300">Connected relationship table</span>
        </div>
      </div>
    </div>
  );
};
