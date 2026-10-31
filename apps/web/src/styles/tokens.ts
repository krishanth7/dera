/**
 * DERA Design System Tokens
 * Constants reflecting CSS variables and system spacing/typography.
 */

export const tokens = {
  colors: {
    brand: {
      primary: "hsl(var(--primary))",
      primaryForeground: "hsl(var(--primary-foreground))",
      secondary: "hsl(var(--secondary))",
      secondaryForeground: "hsl(var(--secondary-foreground))",
    },
    status: {
      success: "hsl(var(--success))",
      warning: "hsl(var(--warning))",
      destructive: "hsl(var(--destructive))",
      muted: "hsl(var(--muted-foreground))",
    },
    surfaces: {
      background: "hsl(var(--background))",
      foreground: "hsl(var(--foreground))",
      card: "hsl(var(--card))",
      border: "hsl(var(--border))",
    },
  },
  typography: {
    fontSans: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
    fontMono: 'ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace',
  },
  spacing: {
    xs: "0.25rem", // 4px
    sm: "0.5rem",  // 8px
    md: "1rem",    // 16px
    lg: "1.5rem",  // 24px
    xl: "2rem",    // 32px
  },
  radius: {
    sm: "0.25rem",
    md: "0.375rem",
    lg: "0.5rem",
  },
} as const;
