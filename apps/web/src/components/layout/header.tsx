"use client";

import * as React from "react";
import { useTheme } from "next-themes";
import { Sun, Moon, Menu, Layers, LogOut, ChevronDown, User } from "lucide-react";
import { useWorkspace } from "@/providers/workspace-provider";
import { useAuth } from "@/providers/auth-provider";
import { Breadcrumbs } from "./breadcrumbs";
import Link from "next/link";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@radix-ui/react-dropdown-menu";

interface HeaderProps {
  onToggleMobileSidebar: () => void;
}

export function Header({ onToggleMobileSidebar }: HeaderProps) {
  const { theme, setTheme } = useTheme();
  const { currentWorkspace, workspaces, setCurrentWorkspace } = useWorkspace();
  const { user, logout, logoutAll } = useAuth();
  const [mounted, setMounted] = React.useState(false);

  React.useEffect(() => {
    setMounted(true);
  }, []);

  return (
    <header className="flex h-14 items-center justify-between border-b border-slate-200 dark:border-slate-800 bg-white/70 dark:bg-slate-900/70 backdrop-blur-xs px-4 z-10 select-none">
      <div className="flex items-center gap-3">
        <button
          type="button"
          onClick={onToggleMobileSidebar}
          className="md:hidden p-1.5 rounded-md text-slate-500 hover:text-slate-900 dark:hover:text-slate-100 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
          aria-label="Toggle navigation menu"
        >
          <Menu className="w-5 h-5" />
        </button>

        {/* Workspace Switcher */}
        <Link
          href="/app/workspaces"
          className="hidden sm:flex items-center gap-2 px-2.5 py-1 rounded bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-xs font-medium text-slate-700 dark:text-slate-300 transition-colors"
          title="Click to view all workspaces"
        >
          <Layers className="w-3.5 h-3.5 text-blue-600 dark:text-blue-400" />
          <span className="truncate max-w-[160px]">
            {currentWorkspace?.name || "Workspace"}
          </span>
          <span className="text-[10px] uppercase font-mono px-1 rounded bg-slate-200 dark:bg-slate-700 text-slate-600 dark:text-slate-400">
            {currentWorkspace?.current_user_role || "OWNER"}
          </span>
        </Link>

        <div className="h-4 w-px bg-slate-200 dark:bg-slate-800 hidden sm:block" />

        {/* Dynamic Breadcrumbs */}
        <Breadcrumbs />
      </div>

      <div className="flex items-center gap-2">
        {/* Theme Switcher */}
        {mounted && (
          <button
            type="button"
            onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
            className="p-2 rounded-md text-slate-500 hover:text-slate-900 dark:hover:text-slate-100 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
            aria-label="Toggle theme"
            title={`Current theme: ${theme}`}
          >
            {theme === "dark" ? (
              <Sun className="w-4 h-4 text-amber-400" />
            ) : (
              <Moon className="w-4 h-4 text-slate-600" />
            )}
          </button>
        )}

        {/* User Account / Identity Dropdown */}
        <div className="flex items-center gap-2 pl-2 border-l border-slate-200 dark:border-slate-800">
          <div className="flex items-center gap-2">
            <div className="h-7 w-7 rounded-full bg-blue-600 text-white flex items-center justify-center text-xs font-semibold font-mono shadow-xs">
              {user?.email ? user.email.slice(0, 2).toUpperCase() : "ENG"}
            </div>
            <span className="hidden md:block text-xs font-medium text-slate-700 dark:text-slate-300 truncate max-w-[140px]">
              {user?.email || "Local Engineer"}
            </span>
            <button
              type="button"
              onClick={() => logout()}
              className="p-1.5 rounded-md text-slate-400 hover:text-red-600 dark:hover:text-red-400 transition-colors"
              title="Sign Out of Session"
              aria-label="Sign out"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </header>
  );
}
