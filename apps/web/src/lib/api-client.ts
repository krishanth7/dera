/**
 * DERA Typed API Client & Error Normalization
 * Standardized across backend contracts (RFC 7807 Problem Details).
 */

import { env } from "@/lib/env";

export interface ApiProblemDetail {
  type: string;
  title: string;
  status: number;
  detail: string;
  instance?: string;
  code?: string;
  invalid_params?: Array<{ name: string; reason: string }>;
}

export class DeraApiError extends Error {
  public readonly status: number;
  public readonly problem: ApiProblemDetail;

  constructor(problem: ApiProblemDetail) {
    super(problem.detail || problem.title || "An unexpected API error occurred");
    this.name = "DeraApiError";
    this.status = problem.status;
    this.problem = problem;
  }
}

export interface SystemMeta {
  service: string;
  version: string;
  zero_ai_policy: boolean;
  supported_dialects: string[];
}

export interface WorkspaceSummary {
  id: string;
  name: string;
  slug: string;
  role: string;
  created_at: string;
}

export class DeraApiClient {
  private readonly baseUrl: string;

  constructor(baseUrl?: string) {
    this.baseUrl = (baseUrl || env.NEXT_PUBLIC_DERA_API_URL).replace(/\/$/, "");
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint.startsWith("/") ? "" : "/"}${endpoint}`;

    const headers: Record<string, string> = {
      Accept: "application/json",
      "Content-Type": "application/json",
      ...((options.headers as Record<string, string>) || {}),
    };

    const res = await fetch(url, {
      ...options,
      headers,
      credentials: "include", // Forward HttpOnly auth session cookies
    });

    if (!res.ok) {
      let problem: ApiProblemDetail;
      try {
        problem = await res.json();
      } catch {
        problem = {
          type: "about:blank",
          title: res.statusText || "Error",
          status: res.status,
          detail: `HTTP error ${res.status}`,
        };
      }
      throw new DeraApiError(problem);
    }

    if (res.status === 204) {
      return {} as T;
    }

    return (await res.json()) as T;
  }

  // System & Health
  async getHealth(): Promise<{ status: string; version: string }> {
    return this.request<{ status: string; version: string }>("/health");
  }

  async getMeta(): Promise<SystemMeta> {
    return this.request<SystemMeta>("/api/v1/meta");
  }

  // Workspaces
  async listWorkspaces(): Promise<{ items: WorkspaceSummary[]; total: number }> {
    return this.request<{ items: WorkspaceSummary[]; total: number }>("/api/v1/workspaces");
  }

  async getWorkspace(id: string): Promise<WorkspaceSummary> {
    return this.request<WorkspaceSummary>(`/api/v1/workspaces/${id}`);
  }

  // Auth Status
  async getCurrentUser(): Promise<{ id: string; email: string; is_active: boolean }> {
    return this.request<{ id: string; email: string; is_active: boolean }>("/api/v1/auth/me");
  }
}

export const apiClient = new DeraApiClient();
