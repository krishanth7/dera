import * as React from "react";
import { cn } from "@/lib/utils";

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: "default" | "secondary" | "outline" | "success" | "warning" | "destructive";
}

export function Badge({ className, variant = "default", ...props }: BadgeProps) {
  const variantStyles = {
    default: "bg-blue-100 text-blue-800 dark:bg-blue-900/40 dark:text-blue-300 border-transparent",
    secondary: "bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300 border-transparent",
    outline: "border border-slate-300 text-slate-700 dark:border-slate-700 dark:text-slate-300",
    success: "bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-300 border-transparent",
    warning: "bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-300 border-transparent",
    destructive: "bg-red-100 text-red-800 dark:bg-red-900/40 dark:text-red-300 border-transparent",
  };

  return (
    <span
      className={cn(
        "inline-flex items-center px-2 py-0.5 rounded text-xs font-medium tracking-wide",
        variantStyles[variant],
        className
      )}
      {...props}
    />
  );
}
