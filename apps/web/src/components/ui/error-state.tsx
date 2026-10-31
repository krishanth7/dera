import * as React from "react";
import { AlertCircle, RotateCcw } from "lucide-react";
import { Button } from "./button";
import { cn } from "@/lib/utils";

export interface ErrorStateProps {
  title?: string;
  message: string;
  onRetry?: () => void;
  className?: string;
}

export function ErrorState({
  title = "An error occurred",
  message,
  onRetry,
  className,
}: ErrorStateProps) {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center p-8 text-center rounded-lg border border-red-200 dark:border-red-900/50 bg-red-50/50 dark:bg-red-950/20",
        className
      )}
      role="alert"
    >
      <div className="flex h-12 w-12 items-center justify-center rounded-full bg-red-100 dark:bg-red-900/40 text-red-600 dark:text-red-400 mb-3">
        <AlertCircle className="h-6 w-6" />
      </div>
      <h3 className="text-sm font-semibold text-red-900 dark:text-red-200">{title}</h3>
      <p className="mt-1 text-xs text-red-700 dark:text-red-400 max-w-sm">{message}</p>
      {onRetry && (
        <div className="mt-4">
          <Button size="sm" variant="outline" onClick={onRetry} className="border-red-300 dark:border-red-800 text-red-800 dark:text-red-300">
            <RotateCcw className="w-4 h-4 mr-1.5" />
            Try again
          </Button>
        </div>
      )}
    </div>
  );
}
