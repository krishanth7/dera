import * as React from "react";
import { cn } from "@/lib/utils";

export interface InputProps
  extends React.InputHTMLAttributes<HTMLInputElement> {
  error?: boolean;
}

export const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, type = "text", error, disabled, ...props }, ref) => {
    return (
      <input
        type={type}
        ref={ref}
        disabled={disabled}
        aria-invalid={error ? "true" : props["aria-invalid"]}
        className={cn(
          "flex h-9 w-full rounded-md border bg-white px-3 py-1 text-sm shadow-sm transition-colors file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-slate-400 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 disabled:cursor-not-allowed disabled:opacity-50 dark:bg-slate-900 dark:placeholder:text-slate-500",
          error
            ? "border-red-500 focus-visible:ring-red-500"
            : "border-slate-300 dark:border-slate-700",
          className
        )}
        {...props}
      />
    );
  }
);
Input.displayName = "Input";
