import type { Metadata } from "next";
import { ThemeProvider } from "@/providers/theme-provider";
import { ToastProvider } from "@/providers/toast-provider";
import { WorkspaceProvider } from "@/providers/workspace-provider";
import "./globals.css";

export const metadata: Metadata = {
  title: "DERA — Database Engineering & Reverse Analysis",
  description: "Understand Every Schema. Engineer Every Change. Deterministic engineering platform for enterprise database reverse engineering.",
  icons: {
    icon: "/favicon.ico",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head />
      <body className="min-h-screen bg-background text-foreground antialiased selection:bg-blue-600 selection:text-white">
        <ThemeProvider>
          <WorkspaceProvider>
            <ToastProvider>
              {children}
            </ToastProvider>
          </WorkspaceProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
