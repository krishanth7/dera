"use client";

import * as React from "react";
import { useState } from "react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { useWorkspace } from "@/providers/workspace-provider";
import { useAuth } from "@/providers/auth-provider";
import { useToast } from "@/providers/toast-provider";
import { Layers, Plus, ArrowRight, ShieldCheck } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";

export default function WorkspacesPage() {
  const router = useRouter();
  const { workspaces, currentWorkspace, setCurrentWorkspace, createWorkspace, isLoading } = useWorkspace();
  const { user } = useAuth();
  const { addToast } = useToast();

  const [isCreating, setIsCreating] = useState(false);
  const [newWsName, setNewWsName] = useState("");
  const [newWsSlug, setNewWsSlug] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const handleSelectWorkspace = (ws: typeof workspaces[0]) => {
    setCurrentWorkspace(ws);
    addToast({
      type: "info",
      title: "Workspace Switched",
      description: `Active context changed to ${ws.name}`,
    });
    router.push("/app/overview");
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newWsName.trim() || !newWsSlug.trim()) return;

    setSubmitting(true);
    try {
      const created = await createWorkspace(newWsName.trim(), newWsSlug.trim().toLowerCase());
      addToast({
        type: "success",
        title: "Workspace Created",
        description: `Successfully provisioned ${created.name}`,
      });
      setIsCreating(false);
      setNewWsName("");
      setNewWsSlug("");
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to create workspace";
      addToast({
        type: "error",
        title: "Creation Error",
        description: msg,
      });
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-6 max-w-5xl">
      <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between border-b border-slate-200 dark:border-slate-800 pb-5">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-slate-900 dark:text-slate-100">
            Workspaces & Multi-Tenancy
          </h1>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
            Isolated tenant workspaces with explicit role-based access control (RBAC).
          </p>
        </div>
        <Button size="sm" onClick={() => setIsCreating(!isCreating)}>
          <Plus className="w-4 h-4 mr-1.5" />
          {isCreating ? "Cancel" : "Create Workspace"}
        </Button>
      </div>

      {/* Workspace Creation Form */}
      {isCreating && (
        <Card className="border-blue-200 dark:border-blue-900/60 bg-blue-50/20 dark:bg-blue-950/10">
          <CardHeader>
            <CardTitle className="text-sm">Provision New Engineering Workspace</CardTitle>
            <CardDescription>
              Assigns caller the Owner role. Tenant slug must be globally unique.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleCreate} className="space-y-4">
              <div className="grid gap-4 sm:grid-cols-2">
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                    Workspace Name
                  </label>
                  <Input
                    required
                    placeholder="e.g. Core Infrastructure"
                    value={newWsName}
                    onChange={(e) => {
                      setNewWsName(e.target.value);
                      if (!newWsSlug) {
                        setNewWsSlug(e.target.value.toLowerCase().replace(/[^a-z0-9]+/g, "-"));
                      }
                    }}
                  />
                </div>
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                    Tenant Slug
                  </label>
                  <Input
                    required
                    pattern="^[a-z0-9-]+$"
                    placeholder="e.g. core-infra"
                    value={newWsSlug}
                    onChange={(e) => setNewWsSlug(e.target.value.toLowerCase())}
                  />
                </div>
              </div>
              <div className="flex justify-end gap-2">
                <Button type="button" variant="outline" size="sm" onClick={() => setIsCreating(false)}>
                  Cancel
                </Button>
                <Button type="submit" size="sm" isLoading={submitting}>
                  Provision Workspace
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      {/* Workspace Directory Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {workspaces.map((ws) => {
          const isCurrent = currentWorkspace?.id === ws.id || currentWorkspace?.slug === ws.slug;

          return (
            <Card
              key={ws.id}
              className={`relative flex flex-col justify-between transition-all ${
                isCurrent
                  ? "border-blue-500/80 shadow-xs dark:border-blue-500/60"
                  : "hover:border-slate-300 dark:hover:border-slate-700"
              }`}
            >
              <CardHeader className="space-y-1">
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-mono uppercase px-1.5 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300">
                    {ws.slug}
                  </span>
                  <Badge variant={ws.current_user_role === "owner" ? "success" : "secondary"}>
                    {ws.current_user_role?.toUpperCase() || "MEMBER"}
                  </Badge>
                </div>
                <CardTitle className="text-base truncate pt-1">{ws.name}</CardTitle>
                <CardDescription className="text-xs">Status: {ws.status}</CardDescription>
              </CardHeader>
              <CardContent className="pt-2 border-t border-slate-100 dark:border-slate-800/60 flex items-center justify-between mt-auto">
                <Link
                  href={`/app/workspaces/${ws.slug}/members`}
                  className="text-xs text-slate-500 hover:text-slate-900 dark:hover:text-slate-200"
                >
                  Manage Members
                </Link>
                {isCurrent ? (
                  <Badge variant="outline" className="border-blue-500 text-blue-600 dark:text-blue-400">
                    Active
                  </Badge>
                ) : (
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => handleSelectWorkspace(ws)}
                  >
                    Switch Context <ArrowRight className="w-3.5 h-3.5 ml-1" />
                  </Button>
                )}
              </CardContent>
            </Card>
          );
        })}
      </div>
    </div>
  );
}
