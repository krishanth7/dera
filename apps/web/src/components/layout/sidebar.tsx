"use client";

import * as React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Database,
  TableProperties,
  Network,
  GitFork,
  Search,
  Camera,
  FileDown,
  Settings,
  ChevronLeft,
  ChevronRight,
  ShieldCheck,
  Layers,
} from "lucide-react";
import { cn } from "@/lib/utils";

interface NavItem {
  title: string;
  href: string;
  icon: React.ReactNode;
  badge?: string;
  planned?: boolean;
}

const navItems: NavItem[] = [
  {
    title: "Overview",
    href: "/app/overview",
    icon: <LayoutDashboard className="w-4 h-4" />,
  },
  {
    title: "Workspaces",
    href: "/app/workspaces",
    icon: <Layers className="w-4 h-4" />,
  },
  {
    title: "Connections",
    href: "/app/connections",
    icon: <Database className="w-4 h-4" />,
    badge: "Phase 7.3",
  },
  {
    title: "Schema Explorer",
    href: "/app/schemas",
    icon: <TableProperties className="w-4 h-4" />,
    badge: "Phase 7.3",
  },
  {
    title: "Search",
    href: "/app/search",
    icon: <Search className="w-4 h-4" />,
    badge: "Phase 7.5",
  },
  {
    title: "Relationships",
    href: "/app/relationships",
    icon: <Network className="w-4 h-4" />,
    badge: "Phase 7.4",
  },
  {
    title: "Dependencies",
    href: "/app/dependencies",
    icon: <GitFork className="w-4 h-4" />,
    badge: "Phase 7.5",
  },
  {
    title: "Diagnostics",
    href: "/app/diagnostics",
    icon: <ShieldCheck className="w-4 h-4" />,
    badge: "Phase 8",
  },
  {
    title: "Snapshots",
    href: "/app/snapshots",
    icon: <Camera className="w-4 h-4" />,
    badge: "Future",
    planned: true,
  },
  {
    title: "Exports",
    href: "/app/exports",
    icon: <FileDown className="w-4 h-4" />,
    badge: "Future",
    planned: true,
  },
  {
    title: "Settings",
    href: "/app/settings",
    icon: <Settings className="w-4 h-4" />,
  },
];

interface SidebarProps {
  isCollapsed: boolean;
  onToggleCollapse: () => void;
  className?: string;
}

export function Sidebar({ isCollapsed, onToggleCollapse, className }: SidebarProps) {
  const pathname = usePathname();

  return (
    <aside
      className={cn(
        "relative flex flex-col border-r border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-950/70 transition-all duration-300 select-none",
        isCollapsed ? "w-16" : "w-64",
        className
      )}
      aria-label="Application Sidebar Navigation"
    >
      {/* Brand Header */}
      <div className="flex h-14 items-center justify-between px-4 border-b border-slate-200 dark:border-slate-800">
        {!isCollapsed && (
          <div className="flex items-center gap-2 overflow-hidden">
            <div className="flex h-7 w-7 items-center justify-center rounded bg-blue-600 text-white font-bold text-xs tracking-wider shrink-0 shadow-xs">
              D
            </div>
            <div className="flex flex-col truncate">
              <span className="font-bold text-sm tracking-tight text-slate-900 dark:text-slate-100 truncate">
                DERA Studio
              </span>
              <span className="text-[10px] text-slate-500 dark:text-slate-400 font-mono tracking-tight -mt-0.5">
                v0.1.0-dev
              </span>
            </div>
          </div>
        )}
        {isCollapsed && (
          <div className="mx-auto flex h-7 w-7 items-center justify-center rounded bg-blue-600 text-white font-bold text-xs shadow-xs">
            D
          </div>
        )}
        <button
          type="button"
          onClick={onToggleCollapse}
          className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 p-1 rounded-md hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors hidden md:flex"
          aria-label={isCollapsed ? "Expand sidebar" : "Collapse sidebar"}
        >
          {isCollapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
        </button>
      </div>

      {/* Navigation Links */}
      <nav className="flex-1 overflow-y-auto px-2 py-4 space-y-1">
        {navItems.map((item) => {
          const isActive = pathname === item.href || pathname?.startsWith(item.href + "/");

          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 px-3 py-2 rounded-md text-xs font-medium transition-colors relative group",
                isActive
                  ? "bg-blue-600 text-white dark:bg-blue-600 dark:text-white shadow-xs"
                  : "text-slate-600 hover:text-slate-900 hover:bg-slate-100 dark:text-slate-400 dark:hover:text-slate-100 dark:hover:bg-slate-800/60"
              )}
              title={isCollapsed ? item.title : undefined}
            >
              <span className="shrink-0">{item.icon}</span>
              {!isCollapsed && (
                <span className="flex-1 truncate">{item.title}</span>
              )}
              {!isCollapsed && item.badge && (
                <span
                  className={cn(
                    "text-[10px] px-1.5 py-0.5 rounded font-mono uppercase tracking-wider",
                    isActive
                      ? "bg-blue-700 text-blue-100"
                      : "bg-slate-200 text-slate-600 dark:bg-slate-800 dark:text-slate-400"
                  )}
                >
                  {item.badge}
                </span>
              )}
            </Link>
          );
        })}
      </nav>

      {/* Technical Integrity Indicator */}
      <div className="p-3 border-t border-slate-200 dark:border-slate-800">
        {!isCollapsed ? (
          <div className="flex items-center gap-2 p-2 rounded bg-emerald-50 dark:bg-emerald-950/30 border border-emerald-200 dark:border-emerald-900/50 text-[11px] text-emerald-800 dark:text-emerald-300">
            <ShieldCheck className="w-4 h-4 shrink-0 text-emerald-600 dark:text-emerald-400" />
            <div className="truncate">
              <span className="font-semibold block">Deterministic Core</span>
              <span className="text-[10px] text-emerald-600 dark:text-emerald-400">Zero-AI Verified</span>
            </div>
          </div>
        ) : (
          <div className="flex justify-center" title="Deterministic Core — Zero-AI Verified">
            <ShieldCheck className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
          </div>
        )}
      </div>
    </aside>
  );
}
