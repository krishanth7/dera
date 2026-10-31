import { describe, it, expect, vi, beforeEach } from "vitest";
import {
  buildGraphModel,
  computeDeterministicLayout,
  calculateNodeDimensions,
  RawGraphData,
} from "@/components/er-diagram";
import { DeraApiClient } from "@/lib/api-client";

describe("Phase 7.4 ER Diagram Canvas — Unit & Determinism Tests", () => {
  let client: DeraApiClient;
  const mockFetch = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    global.fetch = mockFetch;
    client = new DeraApiClient("http://127.0.0.1:8000");
  });

  describe("API Client Relationship Methods", () => {
    it("fetches complete schema relationship graph", async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => ({
          database_name: "ecommerce_prod",
          engine: "postgresql",
          node_count: 2,
          edge_count: 1,
          nodes: [
            { table_id: "t_customers", namespace: "public", name: "customers" },
            { table_id: "t_orders", namespace: "public", name: "orders" },
          ],
          edges: [
            {
              edge_id: "fk_orders_cust",
              source_table_id: "t_orders",
              source_table_name: "orders",
              target_table_id: "t_customers",
              target_table_name: "customers",
              constraint_name: "fk_orders_customer_id",
              source_columns: ["customer_id"],
              target_columns: ["id"],
              on_delete: "CASCADE",
              on_update: "RESTRICT",
            },
          ],
        }),
      });

      const res = await client.getSchemaRelationships("schema_123", "ws_999");
      expect(mockFetch).toHaveBeenCalledWith(
        "http://127.0.0.1:8000/api/v1/reverse-engineering/schemas/schema_123/relationships",
        expect.objectContaining({
          headers: expect.objectContaining({ "X-Workspace-Id": "ws_999" }),
        })
      );
      expect(res.database_name).toBe("ecommerce_prod");
      expect(res.node_count).toBe(2);
      expect(res.edges[0].constraint_name).toBe("fk_orders_customer_id");
    });

    it("fetches table-specific direct relationships", async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => ({
          table_id: "t_orders",
          incoming: [],
          outgoing: [
            {
              edge_id: "fk_orders_cust",
              source_table_id: "t_orders",
              source_table_name: "orders",
              target_table_id: "t_customers",
              target_table_name: "customers",
              constraint_name: "fk_orders_customer_id",
              source_columns: ["customer_id"],
              target_columns: ["id"],
            },
          ],
        }),
      });

      const res = await client.getTableRelationships("schema_123", "t_orders", "ws_999");
      expect(mockFetch).toHaveBeenCalledWith(
        "http://127.0.0.1:8000/api/v1/reverse-engineering/schemas/schema_123/tables/t_orders/relationships",
        expect.objectContaining({
          headers: expect.objectContaining({ "X-Workspace-Id": "ws_999" }),
        })
      );
      expect(res.table_id).toBe("t_orders");
      expect(res.outgoing).toHaveLength(1);
    });
  });

  describe("Graph Model Transformation", () => {
    const rawData: RawGraphData = {
      database_name: "sales_db",
      engine: "postgresql",
      nodes: [
        {
          table_id: "tbl_orders",
          namespace: "sales",
          name: "orders",
          columns: [
            { name: "id", native_type: "bigint", is_primary_key: true, is_foreign_key: false },
            { name: "tenant_id", native_type: "uuid", is_primary_key: false, is_foreign_key: false },
            { name: "customer_id", native_type: "uuid", is_primary_key: false, is_foreign_key: false },
            { name: "parent_order_id", native_type: "bigint", is_primary_key: false, is_foreign_key: false },
          ],
        },
        {
          table_id: "tbl_customers",
          namespace: "public",
          name: "customers",
          columns: [
            { name: "tenant_id", native_type: "uuid", is_primary_key: true, is_foreign_key: false },
            { name: "id", native_type: "uuid", is_primary_key: true, is_foreign_key: false },
            { name: "name", native_type: "varchar(255)", is_primary_key: false, is_foreign_key: false },
          ],
        },
      ],
      edges: [
        // Composite foreign key
        {
          edge_id: "edge_composite_fk",
          source_table_id: "tbl_orders",
          source_table_name: "orders",
          target_table_id: "tbl_customers",
          target_table_name: "customers",
          constraint_name: "fk_orders_customers_composite",
          source_columns: ["tenant_id", "customer_id"],
          target_columns: ["tenant_id", "id"],
          on_delete: "RESTRICT",
          on_update: "CASCADE",
        },
        // Parallel foreign key
        {
          edge_id: "edge_parallel_fk",
          source_table_id: "tbl_orders",
          source_table_name: "orders",
          target_table_id: "tbl_customers",
          target_table_name: "customers",
          constraint_name: "fk_orders_billing_customer",
          source_columns: ["customer_id"],
          target_columns: ["id"],
          on_delete: "SET NULL",
        },
        // Self-referencing foreign key
        {
          edge_id: "edge_self_loop",
          source_table_id: "tbl_orders",
          source_table_name: "orders",
          target_table_id: "tbl_orders",
          target_table_name: "orders",
          constraint_name: "fk_orders_parent_order",
          source_columns: ["parent_order_id"],
          target_columns: ["id"],
        },
      ],
    };

    it("identifies composite foreign keys and ordered column pair mappings", () => {
      const model = buildGraphModel(rawData);
      const compositeEdge = model.edges.find((e) => e.id === "edge_composite_fk")!;

      expect(compositeEdge.is_composite).toBe(true);
      expect(compositeEdge.column_pairs).toHaveLength(2);
      expect(compositeEdge.column_pairs[0]).toEqual({
        source_column: "tenant_id",
        target_column: "tenant_id",
      });
      expect(compositeEdge.column_pairs[1]).toEqual({
        source_column: "customer_id",
        target_column: "id",
      });
    });

    it("identifies parallel foreign keys between identical tables", () => {
      const model = buildGraphModel(rawData);
      const parallelEdges = model.edges.filter(
        (e) => e.source_table_id === "tbl_orders" && e.target_table_id === "tbl_customers"
      );

      expect(parallelEdges).toHaveLength(2);
      expect(parallelEdges[0].is_parallel).toBe(true);
      expect(parallelEdges[0].parallel_total).toBe(2);
      expect(parallelEdges[0].parallel_index).toBe(0);
      expect(parallelEdges[1].is_parallel).toBe(true);
      expect(parallelEdges[1].parallel_index).toBe(1);
    });

    it("identifies self-referencing foreign keys", () => {
      const model = buildGraphModel(rawData);
      const selfLoop = model.edges.find((e) => e.id === "edge_self_loop")!;

      expect(selfLoop.is_self_loop).toBe(true);
      expect(selfLoop.source_table_id).toBe(selfLoop.target_table_id);
    });

    it("marks participating columns as foreign keys in table nodes", () => {
      const model = buildGraphModel(rawData);
      const ordersNode = model.nodes.find((n) => n.id === "tbl_orders")!;

      const tenantCol = ordersNode.columns.find((c) => c.name === "tenant_id")!;
      const custCol = ordersNode.columns.find((c) => c.name === "customer_id")!;
      const parentCol = ordersNode.columns.find((c) => c.name === "parent_order_id")!;
      const idCol = ordersNode.columns.find((c) => c.name === "id")!;

      expect(tenantCol.is_foreign_key).toBe(true);
      expect(custCol.is_foreign_key).toBe(true);
      expect(parentCol.is_foreign_key).toBe(true);
      expect(idCol.is_foreign_key).toBe(false);
      expect(idCol.is_primary_key).toBe(true);
    });
  });

  describe("Deterministic Layout Engine", () => {
    it("produces strictly identical node coordinates regardless of input array permutations", () => {
      const rawA: RawGraphData = {
        database_name: "test_db",
        engine: "postgresql",
        nodes: [
          { table_id: "node_c", namespace: "public", name: "table_c" },
          { table_id: "node_a", namespace: "auth", name: "table_a" },
          { table_id: "node_b", namespace: "public", name: "table_b" },
        ],
        edges: [
          {
            edge_id: "edge_1",
            source_table_id: "node_a",
            source_table_name: "table_a",
            target_table_id: "node_b",
            target_table_name: "table_b",
            constraint_name: "fk_a_b",
            source_columns: ["b_id"],
            target_columns: ["id"],
          },
          {
            edge_id: "edge_2",
            source_table_id: "node_b",
            source_table_name: "table_b",
            target_table_id: "node_c",
            target_table_name: "table_c",
            constraint_name: "fk_b_c",
            source_columns: ["c_id"],
            target_columns: ["id"],
          },
        ],
      };

      // Inverted order of raw input
      const rawB: RawGraphData = {
        database_name: "test_db",
        engine: "postgresql",
        nodes: [rawA.nodes[2], rawA.nodes[0], rawA.nodes[1]],
        edges: [rawA.edges[1], rawA.edges[0]],
      };

      const modelA = buildGraphModel(rawA);
      const modelB = buildGraphModel(rawB);

      const layoutA = computeDeterministicLayout(modelA.nodes, modelA.edges, {
        orientation: "LR",
        rankSeparation: 100,
        nodeSeparation: 40,
      });

      const layoutB = computeDeterministicLayout(modelB.nodes, modelB.edges, {
        orientation: "LR",
        rankSeparation: 100,
        nodeSeparation: 40,
      });

      // Verify node positions match exactly across runs
      expect(layoutA.positionedNodes.length).toBe(3);
      expect(layoutB.positionedNodes.length).toBe(3);

      for (const nodeA of layoutA.positionedNodes) {
        const nodeB = layoutB.positionedNodes.find((n) => n.id === nodeA.id)!;
        expect(nodeB).toBeDefined();
        expect(nodeB.x).toBe(nodeA.x);
        expect(nodeB.y).toBe(nodeA.y);
      }

      expect(layoutA.bounds).toEqual(layoutB.bounds);
    });

    it("handles cyclic foreign key relationships safely without throwing or looping", () => {
      const cyclicRaw: RawGraphData = {
        database_name: "test_db",
        engine: "postgresql",
        nodes: [
          { table_id: "n1", namespace: "public", name: "table_1" },
          { table_id: "n2", namespace: "public", name: "table_2" },
        ],
        edges: [
          {
            edge_id: "e1",
            source_table_id: "n1",
            source_table_name: "table_1",
            target_table_id: "n2",
            target_table_name: "table_2",
            constraint_name: "fk_1_2",
            source_columns: ["col_2"],
            target_columns: ["id"],
          },
          {
            edge_id: "e2",
            source_table_id: "n2",
            source_table_name: "table_2",
            target_table_id: "n1",
            target_table_name: "table_1",
            constraint_name: "fk_2_1",
            source_columns: ["col_1"],
            target_columns: ["id"],
          },
        ],
      };

      const model = buildGraphModel(cyclicRaw);
      expect(() => {
        computeDeterministicLayout(model.nodes, model.edges);
      }).not.toThrow();

      const { positionedNodes, bounds } = computeDeterministicLayout(model.nodes, model.edges);
      expect(positionedNodes).toHaveLength(2);
      expect(bounds.width).toBeGreaterThan(0);
    });

    it("accurately computes card heights based on column counts", () => {
      const dimsSmall = calculateNodeDimensions(3);
      const dimsLarge = calculateNodeDimensions(15);

      expect(dimsSmall.width).toBe(260);
      expect(dimsLarge.width).toBe(260);
      expect(dimsLarge.height).toBeGreaterThan(dimsSmall.height);
    });
  });
});
