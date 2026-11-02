import React from "react";
import { cleanup, render, screen, waitFor } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import { WorkspaceProvider, useWorkspace } from "@/providers/workspace-provider";
import { apiClient } from "@/lib/api-client";

afterEach(()=>{cleanup();vi.restoreAllMocks();});

it("settles on the authorized workspace without a fetch loop before plan analysis",async()=>{
  const fetch=vi.spyOn(apiClient,"listWorkspaces").mockResolvedValue([{id:"authorized",name:"Authorized",slug:"authorized",status:"active",created_at:"2026-11-02"}]);
  function Current(){const {currentWorkspace,isLoading}=useWorkspace();return <p>{isLoading?"loading":currentWorkspace?.id}</p>;}
  render(<WorkspaceProvider><Current /></WorkspaceProvider>);
  await waitFor(()=>expect(screen.getByText("authorized")).toBeInTheDocument());
  expect(fetch).toHaveBeenCalledTimes(1);
});
