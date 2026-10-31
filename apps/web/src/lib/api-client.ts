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

export interface UserResponse {
  id: string;
  email: string;
  status: "active" | "suspended" | "pending";
  created_at: string;
  updated_at?: string;
}

export interface AuthResponse {
  user: UserResponse;
  session_id: string;
  csrf_token: string;
  expires_at: string;
}

export interface WorkspaceSummary {
  id: string;
  name: string;
  slug: string;
  status: string;
  created_at: string;
  updated_at?: string;
  current_user_role?: "owner" | "admin" | "editor" | "viewer";
}

export interface MembershipResponse {
  id: string;
  workspace_id: string;
  user_id: string;
  user_email?: string | null;
  role: "owner" | "admin" | "editor" | "viewer";
  status: "active" | "invited" | "suspended";
  created_at: string;
  updated_at?: string;
}

export interface CreateWorkspacePayload {
  name: string;
  slug: string;
}

export interface AddMemberPayload {
  email: string;
  role: "owner" | "admin" | "editor" | "viewer";
}

export interface UpdateMemberRolePayload {
  role: "owner" | "admin" | "editor" | "viewer";
}

function getCsrfTokenFromCookie(): string | null {
  if (typeof document === "undefined") return null;
  const match = document.cookie.match(/(?:^|;\s*)dera_csrf=([^;]+)/);
  return match ? decodeURIComponent(match[1]) : null;
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

    // Attach CSRF token for state-changing requests if present
    const method = (options.method || "GET").toUpperCase();
    if (["POST", "PUT", "PATCH", "DELETE"].includes(method)) {
      const csrf = getCsrfTokenFromCookie();
      if (csrf && !headers["X-CSRF-Token"]) {
        headers["X-CSRF-Token"] = csrf;
      }
    }

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

  // Authentication
  async register(email: string, password: string): Promise<AuthResponse> {
    return this.request<AuthResponse>("/api/v1/auth/register", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
  }

  async login(email: string, password: string): Promise<AuthResponse> {
    return this.request<AuthResponse>("/api/v1/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
  }

  async logout(): Promise<void> {
    return this.request<void>("/api/v1/auth/logout", {
      method: "POST",
    });
  }

  async logoutAll(): Promise<void> {
    return this.request<void>("/api/v1/auth/logout-all", {
      method: "POST",
    });
  }

  async getCurrentUser(): Promise<UserResponse> {
    return this.request<UserResponse>("/api/v1/auth/me");
  }

  // Workspaces
  async listWorkspaces(): Promise<WorkspaceSummary[]> {
    return this.request<WorkspaceSummary[]>("/api/v1/workspaces");
  }

  async createWorkspace(payload: CreateWorkspacePayload): Promise<WorkspaceSummary> {
    return this.request<WorkspaceSummary>("/api/v1/workspaces", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  }

  async getWorkspace(slug: string): Promise<WorkspaceSummary> {
    return this.request<WorkspaceSummary>(`/api/v1/workspaces/${slug}`);
  }

  // Memberships
  async listMembers(workspaceSlug: string): Promise<MembershipResponse[]> {
    return this.request<MembershipResponse[]>(`/api/v1/workspaces/${workspaceSlug}/members`);
  }

  async addMember(workspaceSlug: string, payload: AddMemberPayload): Promise<MembershipResponse> {
    return this.request<MembershipResponse>(`/api/v1/workspaces/${workspaceSlug}/members`, {
      method: "POST",
      body: JSON.stringify(payload),
    });
  }

  async updateMemberRole(
    workspaceSlug: string,
    userId: string,
    payload: UpdateMemberRolePayload
  ): Promise<MembershipResponse> {
    return this.request<MembershipResponse>(`/api/v1/workspaces/${workspaceSlug}/members/${userId}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    });
  }

  async removeMember(workspaceSlug: string, userId: string): Promise<void> {
    return this.request<void>(`/api/v1/workspaces/${workspaceSlug}/members/${userId}`, {
      method: "DELETE",
    });
  }
}

export const apiClient = new DeraApiClient();
