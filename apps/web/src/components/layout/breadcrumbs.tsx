"use client";

import * as React from "react";
import { usePathname } from "next/navigation";
import Link from "next/link";
import { ChevronRight, Home } from "lucide-react";

export function Breadcrumbs() {
  const pathname = usePathname();

  const segments = pathname
    .split("/")
    .filter(Boolean)
    .filter((s) => s !== "app");

  return (
    <nav aria-label="Breadcrumbs" className="flex items-center text-xs text-slate-500 dark:text-slate-400">
      <Link
        href="/app/overview"
        className="flex items-center hover:text-slate-900 dark:hover:text-slate-100 transition-colors"
      >
        <Home className="w-3.5 h-3.5 mr-1" />
        <span>Studio</span>
      </Link>

      {segments.map((segment, index) => {
        const href = `/app/${segments.slice(0, index + 1).join("/")}`;
        const isLast = index === segments.length - 1;
        const title = segment.charAt(0).toUpperCase() + segment.slice(1);

        return (
          <React.Fragment key={href}>
            <ChevronRight className="w-3.5 h-3.5 mx-1.5 text-slate-400 shrink-0" />
            {isLast ? (
              <span className="font-semibold text-slate-900 dark:text-slate-100" aria-current="page">
                {title}
              </span>
            ) : (
              <Link
                href={href}
                className="hover:text-slate-900 dark:hover:text-slate-100 transition-colors"
              >
                {title}
              </Link>
            )}
          </React.Fragment>
        );
      })}
    </nav>
  );
}
