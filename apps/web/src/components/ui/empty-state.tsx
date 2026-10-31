import * as React from "react";
import { FolderX, Plus } from "lucide-react";
import { Button } from "./button";
import { cn } from "@/lib/utils";

export interface EmptyStateProps {
  title: string;
  description: string;
  icon?: React.ReactNode;
  actionLabel?: string;
  onAction?: () => void;
  action?: React.ReactNode;
  className?: string;
}

export function EmptyState({
  title,
  description,
  icon,
  actionLabel,
  onAction,
  action,
  className,
}: EmptyStateProps) {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center p-8 text-center rounded-lg border border-dashed border-slate-300 dark:border-slate-800 bg-white/50 dark:bg-slate-900/50",
        className
      )}
    >
      <div className="flex h-12 w-12 items-center justify-center rounded-full bg-slate-100 dark:bg-slate-800 text-slate-500 dark:text-slate-400 mb-3">
        {icon || <FolderX className="h-6 w-6" />}
      </div>
      <h3 className="text-sm font-semibold text-slate-900 dark:text-slate-100">{title}</h3>
      <p className="mt-1 text-xs text-slate-500 dark:text-slate-400 max-w-sm">{description}</p>
      {action && <div className="mt-4">{action}</div>}
      {!action && actionLabel && onAction && (
        <div className="mt-4">
          <Button size="sm" onClick={onAction}>
            <Plus className="w-4 h-4 mr-1.5" />
            {actionLabel}
          </Button>
        </div>
      )}
    </div>
  );
}

