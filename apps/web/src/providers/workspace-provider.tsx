"use client";

import * as React from "react";
import { createContext, useContext, useState, useEffect, useCallback } from "react";
import { apiClient, WorkspaceSummary, DeraApiError } from "@/lib/api-client";

interface WorkspaceContextType {
  currentWorkspace: WorkspaceSummary | null;
  workspaces: WorkspaceSummary[];
  isLoading: boolean;
  loading: boolean;
  error: string | null;
  setCurrentWorkspace: (workspace: WorkspaceSummary) => void;
  createWorkspace: (name: string, slug: string) => Promise<WorkspaceSummary>;
  refreshWorkspaces: () => Promise<void>;
}


const defaultLocalWorkspace: WorkspaceSummary = {
  id: "ws-default-local",
  name: "Engineering Core Workspace",
  slug: "default",
  status: "active",
  created_at: new Date().toISOString(),
  current_user_role: "owner",
};

const WorkspaceContext = createContext<WorkspaceContextType | undefined>(undefined);

export function WorkspaceProvider({ children }: { children: React.ReactNode }) {
  const [workspaces, setWorkspaces] = useState<WorkspaceSummary[]>([defaultLocalWorkspace]);
  const [currentWorkspace, setCurrentWorkspace] = useState<WorkspaceSummary | null>(defaultLocalWorkspace);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const refreshWorkspaces = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const items = await apiClient.listWorkspaces();
      if (items && items.length > 0) {
        setWorkspaces(items);
        // Persist current workspace selection or pick the first
        setCurrentWorkspace((prev) => {
          if (!prev) return items[0];
          const matched = items.find((w) => w.slug === prev.slug || w.id === prev.id);
          return matched || items[0];
        });
      } else {
        setWorkspaces([defaultLocalWorkspace]);
        setCurrentWorkspace(defaultLocalWorkspace);
      }
    } catch (err: unknown) {
      // In offline/dev environment, fallback smoothly to local context
      setWorkspaces([defaultLocalWorkspace]);
      if (!currentWorkspace) {
        setCurrentWorkspace(defaultLocalWorkspace);
      }
    } finally {
      setIsLoading(false);
    }
  }, [currentWorkspace]);

  useEffect(() => {
    refreshWorkspaces();
  }, []);

  const createWorkspace = async (name: string, slug: string): Promise<WorkspaceSummary> => {
    setIsLoading(true);
    setError(null);
    try {
      const newWs = await apiClient.createWorkspace({ name, slug });
      setWorkspaces((prev) => [...prev, newWs]);
      setCurrentWorkspace(newWs);
      return newWs;
    } catch (err: unknown) {
      const msg = err instanceof DeraApiError ? err.problem.detail : "Workspace creation failed";
      setError(msg);
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <WorkspaceContext.Provider
      value={{
        currentWorkspace,
        workspaces,
        isLoading,
        loading: isLoading,
        error,
        setCurrentWorkspace,
        createWorkspace,
        refreshWorkspaces,
      }}
    >
      {children}
    </WorkspaceContext.Provider>
  );
}

export function useWorkspace() {
  const context = useContext(WorkspaceContext);
  if (!context) {
    throw new Error("useWorkspace must be used within a WorkspaceProvider");
  }
  return context;
}
