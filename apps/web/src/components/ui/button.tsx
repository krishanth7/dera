import * as React from "react";
import { Slot } from "@radix-ui/react-slot";
import { cn } from "@/lib/utils";

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  asChild?: boolean;
  variant?: "primary" | "secondary" | "outline" | "ghost" | "destructive";
  size?: "sm" | "md" | "lg" | "icon";
  isLoading?: boolean;
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      className,
      variant = "primary",
      size = "md",
      isLoading = false,
      asChild = false,
      disabled,
      children,
      ...props
    },
    ref
  ) => {
    const Comp = asChild ? Slot : "button";

    const variantStyles = {
      primary:
        "bg-blue-600 text-white hover:bg-blue-700 dark:bg-blue-600 dark:hover:bg-blue-500 shadow-sm",
      secondary:
        "bg-slate-100 text-slate-900 hover:bg-slate-200 dark:bg-slate-800 dark:text-slate-100 dark:hover:bg-slate-700",
      outline:
        "border border-slate-300 bg-transparent hover:bg-slate-100 text-slate-800 dark:border-slate-700 dark:text-slate-200 dark:hover:bg-slate-800",
      ghost:
        "hover:bg-slate-100 text-slate-700 dark:hover:bg-slate-800 dark:text-slate-300",
      destructive:
        "bg-red-600 text-white hover:bg-red-700 dark:bg-red-700 dark:hover:bg-red-600 shadow-sm",
    };

    const sizeStyles = {
      sm: "h-8 px-3 text-xs rounded",
      md: "h-9 px-4 text-sm rounded-md",
      lg: "h-10 px-6 text-base rounded-md",
      icon: "h-9 w-9 p-0 rounded-md flex items-center justify-center",
    };

    return (
      <Comp
        ref={ref}
        disabled={disabled || isLoading}
        aria-busy={isLoading ? "true" : undefined}
        className={cn(
          "inline-flex items-center justify-center font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 disabled:pointer-events-none disabled:opacity-50 select-none",
          variantStyles[variant],
          sizeStyles[size],
          className
        )}
        {...props}
      >
        {isLoading ? (
          <span className="flex items-center gap-2">
            <svg
              className="animate-spin h-4 w-4 text-current"
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
            >
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
              ></circle>
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
              ></path>
            </svg>
            <span>Loading...</span>
          </span>
        ) : (
          children
        )}
      </Comp>
    );
  }
);
Button.displayName = "Button";
