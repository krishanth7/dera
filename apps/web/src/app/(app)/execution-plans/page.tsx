"use client";

import { ExecutionPlanExplorer } from "@/components/execution-plans/ExecutionPlanExplorer";
import { useWorkspace } from "@/providers/workspace-provider";

export default function ExecutionPlansPage() {
  const { currentWorkspace } = useWorkspace();
  const workspaceId = currentWorkspace?.id ?? null;
  return <ExecutionPlanExplorer key={workspaceId || "none"} workspaceId={workspaceId} />;
}
