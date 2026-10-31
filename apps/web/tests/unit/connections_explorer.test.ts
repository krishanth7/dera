import { describe, it, expect, vi, beforeEach } from "vitest";
import { DeraApiClient } from "@/lib/api-client";

describe("Phase 7.3 Connections & Schema Explorer API Client", () => {
  let client: DeraApiClient;
  const mockFetch = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    global.fetch = mockFetch;
    client = new DeraApiClient("http://127.0.0.1:8000");
  });

  it("lists supported database engines and provider distributions", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => [
        {
          engine: "postgresql",
          display_name: "PostgreSQL",
          default_port: 5432,
          is_experimental: false,
          supported_providers: ["generic", "supabase"],
        },
        {
          engine: "sqlite",
          display_name: "SQLite (Contained)",
          default_port: null,
          is_experimental: false,
          supported_providers: ["generic"],
        },
      ],
    });

    const engines = await client.listSupportedEngines();
    expect(mockFetch).toHaveBeenCalledWith(
      "http://127.0.0.1:8000/api/v1/connectors/engines",
      expect.objectContaining({ credentials: "include" })
    );
    expect(engines).toHaveLength(2);

    expect(engines[0].engine).toBe("postgresql");
    expect(engines[1].default_port).toBeNull();
  });

  it("performs diagnostic connection test without saving credentials", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => ({
        success: true,
        latency_ms: 14.2,
        engine: "postgresql",
        server_version: "PostgreSQL 16.2 on x86_64",
      }),
    });

    const res = await client.testRawConnection({
      engine: "postgresql",
      database: "analytics_db",
      host: "localhost",
      port: 5432,
      username: "reader",
      password: "secret_password",
    });

    expect(mockFetch).toHaveBeenCalledWith(
      "http://127.0.0.1:8000/api/v1/connections/test",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({
          engine: "postgresql",
          database: "analytics_db",
          host: "localhost",
          port: 5432,
          username: "reader",
          password: "secret_password",
        }),
      })
    );
    expect(res.success).toBe(true);
    expect(res.latency_ms).toBe(14.2);
  });

  it("creates and manages workspace connections with boundary headers", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 201,
      json: async () => ({
        id: "conn-123",
        workspace_id: "ws-456",
        name: "Staging Replica",
        engine: "postgresql",
        provider: "supabase",
        database: "postgres",
        host: "db.example.supabase.co",
        port: 5432,
        username: "postgres",
        has_password: true,
        ssl_mode: "require",
        status: "not_tested",
        created_at: new Date().toISOString(),
      }),
    });

    const conn = await client.createConnection("ws-456", {
      name: "Staging Replica",
      engine: "postgresql",
      provider: "supabase",
      database: "postgres",
      host: "db.example.supabase.co",
      port: 5432,
      username: "postgres",
      password: "vault_password",
      ssl_mode: "require",
    });

    expect(mockFetch).toHaveBeenCalledWith(
      "http://127.0.0.1:8000/api/v1/workspaces/ws-456/connections",
      expect.objectContaining({
        method: "POST",
        headers: expect.objectContaining({ "X-Workspace-Id": "ws-456" }),
      })
    );
    expect(conn.id).toBe("conn-123");
    expect(conn.has_password).toBe(true);
  });

  it("retrieves schema representation summary and table listings", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => ({
        schema_id: "schema-1",
        database_id: "schema-1",
        database_name: "production_db",
        engine: "postgresql",
        namespace_count: 2,
        table_count: 24,
        view_count: 3,
        foreign_key_count: 18,
        completeness: "complete",
        source_engine: "PostgreSQL",
        connector_version: "0.1.0-dev",
        collection_timestamp: new Date().toISOString(),
      }),
    });

    const summary = await client.getSchemaSummary("schema-1", "ws-456");
    expect(mockFetch).toHaveBeenCalledWith(
      "http://127.0.0.1:8000/api/v1/reverse-engineering/schemas/schema-1",
      expect.objectContaining({
        headers: expect.objectContaining({ "X-Workspace-Id": "ws-456" }),
      })
    );
    expect(summary.database_name).toBe("production_db");
    expect(summary.table_count).toBe(24);
  });

  it("retrieves granular table detail including primary key and foreign keys", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => ({
        table_id: "tbl-users",
        namespace: "public",
        name: "users",
        table_type: "TABLE",
        columns: [
          {
            column_id: "col-1",
            table_id: "tbl-users",
            name: "id",
            ordinal_position: 1,
            native_type: "uuid",
            canonical_type: "UUID",
            is_nullable: false,
            is_primary_key: true,
            default_expression: "gen_random_uuid()",
          },
          {
            column_id: "col-2",
            table_id: "tbl-users",
            name: "email",
            ordinal_position: 2,
            native_type: "text",
            canonical_type: "STRING",
            is_nullable: false,
            is_primary_key: false,
            default_expression: null,
          },
        ],
        primary_key: {
          constraint_id: "pk-users",
          name: "pk_users",
          columns: ["id"],
        },
        foreign_keys: [],
        unique_constraints: [
          {
            constraint_id: "uq-users-email",
            name: "uq_users_email",
            constraint_type: "UNIQUE",
            columns: ["email"],
          },
        ],
        check_constraints: [],
        indexes: [
          {
            index_id: "idx-users-id",
            name: "pk_users",
            is_unique: true,
            is_primary: true,
            columns: ["id"],
          },
        ],
      }),
    });

    const detail = await client.getTableDetail("schema-1", "tbl-users", "ws-456");
    expect(detail.name).toBe("users");
    expect(detail.columns).toHaveLength(2);
    expect(detail.columns[0].is_primary_key).toBe(true);
    expect(detail.primary_key?.columns).toEqual(["id"]);
    expect(detail.unique_constraints).toHaveLength(1);
  });
});
