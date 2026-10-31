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

export interface ConnectorEngine {
  engine: "postgresql" | "sqlite" | "mysql" | "mariadb";
  display_name: string;
  default_port: number | null;
  is_experimental: boolean;
  supported_providers: string[];
}

export interface ConnectionTestPayload {
  engine: "postgresql" | "sqlite" | "mysql" | "mariadb";
  database: string;
  host?: string | null;
  port?: number | null;
  username?: string | null;
  password?: string | null;
  ssl_mode?: string;
}

export interface ConnectionTestResult {
  success: boolean;
  latency_ms: number;
  engine: string;
  server_version?: string | null;
  error_code?: string | null;
  error_message?: string | null;
}

export interface ConnectionItem {
  id: string;
  workspace_id: string;
  name: string;
  engine: "postgresql" | "sqlite" | "mysql" | "mariadb";
  provider: string;
  database: string;
  host?: string | null;
  port?: number | null;
  username?: string | null;
  has_password: boolean;
  ssl_mode: string;
  status: "not_tested" | "connected" | "failed" | "testing";
  last_tested_at?: string | null;
  last_inspected_at?: string | null;
  created_at: string;
  updated_at?: string | null;
  error_message?: string | null;
}

export interface CreateConnectionPayload {
  name: string;
  engine: "postgresql" | "sqlite" | "mysql" | "mariadb";
  database: string;
  provider?: string;
  host?: string | null;
  port?: number | null;
  username?: string | null;
  password?: string | null;
  ssl_mode?: string;
}

export interface UpdateConnectionPayload {
  name?: string;
  database?: string;
  provider?: string;
  host?: string | null;
  port?: number | null;
  username?: string | null;
  password?: string | null;
  ssl_mode?: string;
}

export interface SchemaSummary {
  schema_id: string;
  database_id: string;
  database_name: string;
  engine: string;
  namespace_count: number;
  table_count: number;
  view_count: number;
  foreign_key_count: number;
  completeness: string;
  source_engine: string;
  source_version?: string | null;
  connector_version: string;
  collection_timestamp: string;
}

export interface NamespaceItem {
  namespace_id: string;
  name: string;
  table_count: number;
}

export interface TableSummaryItem {
  table_id: string;
  namespace: string;
  name: string;
  table_type: string;
  column_count: number;
  has_primary_key: boolean;
  foreign_key_count: number;
}

export interface ColumnDetailItem {
  column_id: string;
  table_id: string;
  name: string;
  ordinal_position: number;
  native_type: string;
  canonical_type: string;
  is_nullable: boolean;
  is_primary_key: boolean;
  default_expression?: string | null;
}

export interface PrimaryKeyItem {
  constraint_id: string;
  name: string;
  columns: string[];
}

export interface ForeignKeySummaryItem {
  constraint_id: string;
  name: string;
  source_columns: string[];
  referenced_table_id?: string | null;
  referenced_table_name: string;
  referenced_columns: string[];
  on_delete?: string | null;
  on_update?: string | null;
}

export interface ConstraintSummaryItem {
  constraint_id: string;
  name: string;
  constraint_type: string;
  columns: string[];
  raw_expression?: string | null;
}

export interface IndexSummaryItem {
  index_id: string;
  name: string;
  is_unique: boolean;
  is_primary: boolean;
  columns: string[];
}

export interface TableDetailItem {
  table_id: string;
  namespace: string;
  name: string;
  table_type: string;
  columns: ColumnDetailItem[];
  primary_key?: PrimaryKeyItem | null;
  foreign_keys: ForeignKeySummaryItem[];
  unique_constraints: ConstraintSummaryItem[];
  check_constraints: ConstraintSummaryItem[];
  indexes: IndexSummaryItem[];
}

export interface RelationshipNodeItem {
  table_id: string;
  namespace: string;
  name: string;
}

export interface RelationshipEdgeItem {
  edge_id: string;
  source_table_id: string;
  source_table_name: string;
  target_table_id: string;
  target_table_name: string;
  constraint_name: string;
  source_columns: string[];
  target_columns: string[];
  on_delete?: string | null;
  on_update?: string | null;
}

export interface RelationshipGraphResponse {
  database_name: string;
  engine: string;
  node_count: number;
  edge_count: number;
  nodes: RelationshipNodeItem[];
  edges: RelationshipEdgeItem[];
}

export interface TableRelationshipsResponse {
  table_id: string;
  incoming: RelationshipEdgeItem[];
  outgoing: RelationshipEdgeItem[];
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

  // Database Connections (Phase 7.3)
  async listSupportedEngines(): Promise<ConnectorEngine[]> {
    return this.request<ConnectorEngine[]>("/api/v1/connectors/engines");
  }

  async testRawConnection(payload: ConnectionTestPayload): Promise<ConnectionTestResult> {
    return this.request<ConnectionTestResult>("/api/v1/connections/test", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  }

  async listConnections(workspaceId: string): Promise<ConnectionItem[]> {
    const res = await this.request<{ connections: ConnectionItem[]; total_count: number }>(
      `/api/v1/workspaces/${workspaceId}/connections`,
      {
        headers: { "X-Workspace-Id": workspaceId },
      }
    );
    return res.connections;
  }

  async createConnection(
    workspaceId: string,
    payload: CreateConnectionPayload
  ): Promise<ConnectionItem> {
    return this.request<ConnectionItem>(`/api/v1/workspaces/${workspaceId}/connections`, {
      method: "POST",
      headers: { "X-Workspace-Id": workspaceId },
      body: JSON.stringify(payload),
    });
  }

  async getConnection(workspaceId: string, connectionId: string): Promise<ConnectionItem> {
    return this.request<ConnectionItem>(
      `/api/v1/workspaces/${workspaceId}/connections/${connectionId}`,
      {
        headers: { "X-Workspace-Id": workspaceId },
      }
    );
  }

  async updateConnection(
    workspaceId: string,
    connectionId: string,
    payload: UpdateConnectionPayload
  ): Promise<ConnectionItem> {
    return this.request<ConnectionItem>(
      `/api/v1/workspaces/${workspaceId}/connections/${connectionId}`,
      {
        method: "PATCH",
        headers: { "X-Workspace-Id": workspaceId },
        body: JSON.stringify(payload),
      }
    );
  }

  async deleteConnection(workspaceId: string, connectionId: string): Promise<void> {
    return this.request<void>(
      `/api/v1/workspaces/${workspaceId}/connections/${connectionId}`,
      {
        method: "DELETE",
        headers: { "X-Workspace-Id": workspaceId },
      }
    );
  }

  async testConnection(workspaceId: string, connectionId: string): Promise<ConnectionTestResult> {
    return this.request<ConnectionTestResult>(
      `/api/v1/workspaces/${workspaceId}/connections/${connectionId}/test`,
      {
        method: "POST",
        headers: { "X-Workspace-Id": workspaceId },
      }
    );
  }

  async inspectConnection(
    workspaceId: string,
    connectionId: string
  ): Promise<SchemaSummary> {
    return this.request<SchemaSummary>(
      `/api/v1/workspaces/${workspaceId}/connections/${connectionId}/inspect`,
      {
        method: "POST",
        headers: { "X-Workspace-Id": workspaceId },
      }
    );
  }

  // Schema Explorer (Phase 7.3 & Phase 6.6)
  async listSchemas(workspaceId: string): Promise<SchemaSummary[]> {
    return this.request<SchemaSummary[]>("/api/v1/reverse-engineering/schemas", {
      headers: { "X-Workspace-Id": workspaceId },
    });
  }

  async getSchemaSummary(schemaId: string, workspaceId: string): Promise<SchemaSummary> {
    return this.request<SchemaSummary>(
      `/api/v1/reverse-engineering/schemas/${schemaId}`,
      {
        headers: { "X-Workspace-Id": workspaceId },
      }
    );
  }

  async listNamespaces(schemaId: string, workspaceId: string): Promise<NamespaceItem[]> {
    const res = await this.request<{ namespaces: NamespaceItem[]; total_count: number }>(
      `/api/v1/reverse-engineering/schemas/${schemaId}/namespaces`,
      {
        headers: { "X-Workspace-Id": workspaceId },
      }
    );
    return res.namespaces;
  }

  async listTables(
    schemaId: string,
    workspaceId: string,
    params?: { namespace?: string; table_type?: string; limit?: number; offset?: number }
  ): Promise<{ tables: TableSummaryItem[]; total_count: number }> {
    const searchParams = new URLSearchParams();
    if (params?.namespace) searchParams.set("namespace", params.namespace);
    if (params?.table_type) searchParams.set("table_type", params.table_type);
    if (params?.limit) searchParams.set("limit", String(params.limit));
    if (params?.offset) searchParams.set("offset", String(params.offset));

    const qs = searchParams.toString();
    return this.request<{ tables: TableSummaryItem[]; total_count: number }>(
      `/api/v1/reverse-engineering/schemas/${schemaId}/tables${qs ? `?${qs}` : ""}`,
      {
        headers: { "X-Workspace-Id": workspaceId },
      }
    );
  }

  async getTableDetail(
    schemaId: string,
    tableId: string,
    workspaceId: string
  ): Promise<TableDetailItem> {
    return this.request<TableDetailItem>(
      `/api/v1/reverse-engineering/schemas/${schemaId}/tables/${tableId}`,
      {
        headers: { "X-Workspace-Id": workspaceId },
      }
    );
  }

  async getColumnDetail(
    schemaId: string,
    columnId: string,
    workspaceId: string
  ): Promise<ColumnDetailItem> {
    return this.request<ColumnDetailItem>(
      `/api/v1/reverse-engineering/schemas/${schemaId}/columns/${columnId}`,
      {
        headers: { "X-Workspace-Id": workspaceId },
      }
    );
  }

  // Phase 7.4 Relationship Graph APIs (Phase 6.6)
  async getSchemaRelationships(
    schemaId: string,
    workspaceId: string
  ): Promise<RelationshipGraphResponse> {
    return this.request<RelationshipGraphResponse>(
      `/api/v1/reverse-engineering/schemas/${schemaId}/relationships`,
      {
        headers: { "X-Workspace-Id": workspaceId },
      }
    );
  }

  async getTableRelationships(
    schemaId: string,
    tableId: string,
    workspaceId: string
  ): Promise<TableRelationshipsResponse> {
    return this.request<TableRelationshipsResponse>(
      `/api/v1/reverse-engineering/schemas/${schemaId}/tables/${tableId}/relationships`,
      {
        headers: { "X-Workspace-Id": workspaceId },
      }
    );
  }
}

export const apiClient = new DeraApiClient();

