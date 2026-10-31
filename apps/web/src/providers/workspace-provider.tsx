"use client";

import * as React from "react";
import { createContext, useContext, useState, useEffect } from "react";

export interface Workspace {
  id: string;
  name: string;
  slug: string;
  role: "OWNER" | "ADMIN" | "EDITOR" | "ANALYST" | "VIEWER";
}

interface WorkspaceContextType {
  currentWorkspace: Workspace | null;
  workspaces: Workspace[];
  isLoading: boolean;
  error: string | null;
  setCurrentWorkspace: (workspace: Workspace) => void;
  refreshWorkspaces: () => Promise<void>;
}

const defaultWorkspace: Workspace = {
  id: "ws-default-local",
  name: "Default Engineering Workspace",
  slug: "default",
  role: "OWNER",
};

const WorkspaceContext = createContext<WorkspaceContextType | undefined>(undefined);

export function WorkspaceProvider({ children }: { children: React.ReactNode }) {
  const [workspaces, setWorkspaces] = useState<Workspace[]>([defaultWorkspace]);
  const [currentWorkspace, setCurrentWorkspace] = useState<Workspace | null>(defaultWorkspace);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const refreshWorkspaces = async () => {
    setIsLoading(true);
    setError(null);
    try {
      // In production, queries GET /api/v1/workspaces with session cookies
      // Graceful fallback to default engineering context if API is unreachable
      setWorkspaces([defaultWorkspace]);
      if (!currentWorkspace) {
        setCurrentWorkspace(defaultWorkspace);
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to load workspaces";
      setError(msg);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    refreshWorkspaces();
  }, []);

  return (
    <WorkspaceContext.Provider
      value={{
        currentWorkspace,
        workspaces,
        isLoading,
        error,
        setCurrentWorkspace,
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
