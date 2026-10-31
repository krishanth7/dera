"use client";

import * as React from "react";
import { useState } from "react";
import { Sidebar } from "./sidebar";
import { Header } from "./header";
import { cn } from "@/lib/utils";

export interface AppShellProps {
  children: React.ReactNode;
}

export function AppShell({ children }: AppShellProps) {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  // Close mobile drawer on Escape key press
  React.useEffect(() => {
    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape" && mobileOpen) {
        setMobileOpen(false);
      }
    }
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [mobileOpen]);

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-white dark:bg-slate-950 font-sans">
      {/* Skip to Content Navigation Link for Screen Readers & Keyboard Users */}
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:fixed focus:top-3 focus:left-3 focus:z-50 focus:px-4 focus:py-2 focus:bg-blue-600 focus:text-white focus:font-semibold focus:rounded-md focus:shadow-lg focus:outline-none focus:ring-2 focus:ring-white focus:ring-offset-2 focus:ring-offset-blue-600"
      >
        Skip to main content
      </a>

      {/* Desktop Sidebar */}
      <Sidebar
        isCollapsed={isCollapsed}
        onToggleCollapse={() => setIsCollapsed(!isCollapsed)}
        className="hidden md:flex shrink-0"
      />

      {/* Mobile Sidebar Overlay */}
      {mobileOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/50 md:hidden backdrop-blur-xs"
          onClick={() => setMobileOpen(false)}
          aria-hidden="true"
        />
      )}

      {/* Mobile Drawer */}
      <div
        role="dialog"
        aria-modal="true"
        aria-label="Mobile navigation drawer"
        className={cn(
          "fixed inset-y-0 left-0 z-50 w-64 md:hidden transition-transform duration-300 ease-in-out bg-white dark:bg-slate-950",
          mobileOpen ? "translate-x-0" : "-translate-x-full"
        )}
      >
        <Sidebar
          isCollapsed={false}
          onToggleCollapse={() => setMobileOpen(false)}
          className="h-full border-r border-slate-200 dark:border-slate-800"
        />
      </div>

      {/* Main Content Area */}
      <div className="flex flex-1 flex-col overflow-hidden">
        <Header onToggleMobileSidebar={() => setMobileOpen(!mobileOpen)} />
        <main
          className="flex-1 overflow-y-auto bg-slate-50/40 dark:bg-slate-950/40 p-4 md:p-6"
          id="main-content"
          tabIndex={-1}
        >
          <div className="mx-auto max-w-7xl space-y-6">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}
