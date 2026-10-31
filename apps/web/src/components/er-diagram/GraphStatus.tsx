"use client";

import * as React from "react";
import { Database, Network, Key, Layers, ShieldCheck, Clock } from "lucide-react";
import { Badge } from "@/components/ui/badge";

interface GraphStatusProps {
  databaseName: string;
  engine: string;
  nodeCount: number;
  edgeCount: number;
  compositeCount: number;
  selfLoopCount: number;
  completeness?: string;
  collectionTimestamp?: string;
}

export const GraphStatus: React.FC<GraphStatusProps> = ({
  databaseName,
  engine,
  nodeCount,
  edgeCount,
  compositeCount,
  selfLoopCount,
  completeness = "complete",
  collectionTimestamp,
}) => {
  return (
    <div className="flex flex-wrap items-center justify-between gap-3 px-4 py-2 bg-slate-900 border-b border-slate-800 text-xs text-slate-300">
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-1.5 font-medium text-slate-100">
          <Database className="w-3.5 h-3.5 text-blue-400" />
          <span className="font-mono">{databaseName}</span>
        </div>

        <Badge variant="outline" className="text-[10px] uppercase font-mono bg-slate-800 border-slate-700 text-slate-300">
          {engine}
        </Badge>

        <Badge
          variant="outline"
          className={`text-[10px] uppercase font-mono ${
            completeness === "complete"
              ? "bg-emerald-950/40 border-emerald-800 text-emerald-300"
              : "bg-amber-950/40 border-amber-800 text-amber-300"
          }`}
        >
          {completeness}
        </Badge>
      </div>

      <div className="flex items-center gap-4 text-slate-400 font-mono text-[11px]">
        <span>
          <strong className="text-slate-200">{nodeCount}</strong> tables
        </span>
        <span>•</span>
        <span>
          <strong className="text-slate-200">{edgeCount}</strong> relationships
        </span>
        {compositeCount > 0 && (
          <>
            <span>•</span>
            <span className="text-blue-300">
              <strong>{compositeCount}</strong> composite
            </span>
          </>
        )}
        {selfLoopCount > 0 && (
          <>
            <span>•</span>
            <span className="text-purple-300">
              <strong>{selfLoopCount}</strong> self-loops
            </span>
          </>
        )}
        {collectionTimestamp && (
          <>
            <span className="hidden sm:inline">•</span>
            <span className="hidden sm:flex items-center gap-1 text-slate-500">
              <Clock className="w-3 h-3" />
              {new Date(collectionTimestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
            </span>
          </>
        )}
      </div>
    </div>
  );
};
