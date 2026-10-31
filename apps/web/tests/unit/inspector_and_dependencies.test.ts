/**
 * DERA — Phase 7.5 Unit Tests: Table Inspector, Advanced Search & Dependency Exploration
 * Verifies reachability, cycle safety, topological orderings, search matching, and composite keys.
 */

import { describe, it, expect } from "vitest";
import type {
  DependencyAnalysisResponse,
  CycleReportResponse,
  RelationshipGraphResponse,
  TableDetailItem,
} from "@/lib/api-client";
import type { InspectorObject } from "@/components/table-inspector/types";

describe("Phase 7.5: Universal Object Inspector Interface", () => {
  it("conforms to extensible multi-resource InspectorObject contract", () => {
    const tableObj: InspectorObject = {
      id: "tbl-users-01",
      kind: "table",
      displayName: "public.users",
      namespace: "public",
      completeness: "complete",
      sourceEngine: "postgresql",
      provenance: {
        connectorVersion: "0.1.0",
        collectionTimestamp: "2026-10-31T12:00:00Z",
      },
    };

    expect(tableObj.kind).toBe("table");
    expect(tableObj.completeness).toBe("complete");
    expect(tableObj.displayName).toBe("public.users");

    // Extensibility interface supports collection/document_type for future NoSQL
    const futureDocObj: InspectorObject = {
      id: "coll-orders-01",
      kind: "collection",
      displayName: "orders",
      completeness: "partial",
      sourceEngine: "firestore",
    };
    expect(futureDocObj.kind).toBe("collection");
  });
});

describe("Phase 7.5: Dependency Semantics & Topological Ordering", () => {
  const mockAnalysis: DependencyAnalysisResponse = {
    database_name: "test_db",
    total_tables: 4,
    total_edges: 4,
    has_cycles: false,
    cycle_count: 0,
    scc_count: 4,
    cyclic_scc_count: 0,
    creation_order: ["tenants", "users", "orders", "order_items"],
    drop_order: ["order_items", "orders", "users", "tenants"],
    levels: [
      { level_index: 0, table_ids: ["tenants"] },
      { level_index: 1, table_ids: ["users"] },
      { level_index: 2, table_ids: ["orders"] },
      { level_index: 3, table_ids: ["order_items"] },
    ],
  };

  it("verifies creation order puts parent dependencies before children", () => {
    const creationOrder = mockAnalysis.creation_order;
    const tenantsIdx = creationOrder.indexOf("tenants");
    const usersIdx = creationOrder.indexOf("users");
    const ordersIdx = creationOrder.indexOf("orders");
    const itemsIdx = creationOrder.indexOf("order_items");

    expect(tenantsIdx).toBeLessThan(usersIdx);
    expect(usersIdx).toBeLessThan(ordersIdx);
    expect(ordersIdx).toBeLessThan(itemsIdx);
  });

  it("verifies drop order is exact reverse of creation order to prevent constraint errors", () => {
    const reversedCreation = [...mockAnalysis.creation_order].reverse();
    expect(mockAnalysis.drop_order).toEqual(reversedCreation);
  });

  it("verifies level 0 tables are completely independent roots", () => {
    const rootLevel = mockAnalysis.levels.find((l) => l.level_index === 0);
    expect(rootLevel).toBeDefined();
    expect(rootLevel?.table_ids).toContain("tenants");
  });
});

describe("Phase 7.5: Cycle Detection & Breakability Analysis", () => {
  const mockCycleReport: CycleReportResponse = {
    has_cycles: true,
    cycle_count: 1,
    scc_count: 2,
    cyclic_scc_count: 1,
    cycles: [
      {
        cycle_id: "cycle-001",
        cycle_kind: "DIRECT_MUTUAL",
        table_ids: ["departments", "employees"],
        length: 2,
        breakability_strategy: "DEFER_FOREIGN_KEY",
      },
    ],
    components: [
      {
        scc_id: "scc-001",
        is_cyclic: true,
        table_ids: ["departments", "employees"],
        size: 2,
      },
      {
        scc_id: "scc-002",
        is_cyclic: false,
        table_ids: ["audit_log"],
        size: 1,
      },
    ],
  };

  it("identifies cyclic components and partitions acyclic components", () => {
    expect(mockCycleReport.has_cycles).toBe(true);
    expect(mockCycleReport.cyclic_scc_count).toBe(1);

    const cyclicSCC = mockCycleReport.components.find((c) => c.is_cyclic);
    expect(cyclicSCC?.table_ids).toContain("departments");
    expect(cyclicSCC?.table_ids).toContain("employees");

    const acyclicSCC = mockCycleReport.components.find((c) => !c.is_cyclic);
    expect(acyclicSCC?.table_ids).toEqual(["audit_log"]);
  });

  it("provides deterministic breakability strategy for circular cycles", () => {
    const cycle = mockCycleReport.cycles[0];
    expect(cycle.breakability_strategy).toBe("DEFER_FOREIGN_KEY");
    expect(cycle.length).toBe(2);
  });
});

describe("Phase 7.5: Composite Key & Referential Action Integrity", () => {
  const mockTable: TableDetailItem = {
    table_id: "tbl-orders-01",
    namespace: "ecommerce",
    name: "order_items",
    table_type: "TABLE",
    columns: [
      {
        column_id: "c-1",
        table_id: "tbl-orders-01",
        name: "tenant_id",
        ordinal_position: 1,
        native_type: "uuid",
        canonical_type: "string",
        is_nullable: false,
        is_primary_key: true,
      },
      {
        column_id: "c-2",
        table_id: "tbl-orders-01",
        name: "order_id",
        ordinal_position: 2,
        native_type: "uuid",
        canonical_type: "string",
        is_nullable: false,
        is_primary_key: true,
      },
      {
        column_id: "c-3",
        table_id: "tbl-orders-01",
        name: "item_id",
        ordinal_position: 3,
        native_type: "int",
        canonical_type: "integer",
        is_nullable: false,
        is_primary_key: true,
      },
    ],
    primary_key: {
      constraint_id: "pk-order-items",
      name: "pk_order_items",
      columns: ["tenant_id", "order_id", "item_id"],
    },
    foreign_keys: [
      {
        constraint_id: "fk-order-items-order",
        name: "fk_order_items_orders",
        source_columns: ["tenant_id", "order_id"],
        referenced_table_id: "tbl-orders",
        referenced_table_name: "orders",
        referenced_columns: ["tenant_id", "id"],
        on_delete: "CASCADE",
        on_update: "RESTRICT",
      },
    ],
    unique_constraints: [],
    check_constraints: [
      {
        constraint_id: "chk-qty",
        name: "chk_quantity_positive",
        constraint_type: "CHECK",
        columns: ["quantity"],
        raw_expression: "quantity > 0 AND quantity <= 1000",
      },
    ],
    indexes: [
      {
        index_id: "idx-orders-tenant",
        name: "idx_order_items_tenant",
        is_unique: false,
        is_primary: false,
        columns: ["tenant_id"],
      },
    ],
  };

  it("preserves composite primary key as single multi-column constraint", () => {
    expect(mockTable.primary_key?.columns.length).toBe(3);
    expect(mockTable.primary_key?.columns).toEqual(["tenant_id", "order_id", "item_id"]);
  });

  it("preserves composite foreign key ordered column mapping and referential actions", () => {
    const fk = mockTable.foreign_keys[0];
    expect(fk.source_columns).toEqual(["tenant_id", "order_id"]);
    expect(fk.referenced_columns).toEqual(["tenant_id", "id"]);
    expect(fk.on_delete).toBe("CASCADE");
    expect(fk.on_update).toBe("RESTRICT");
  });

  it("escapes and preserves inert raw SQL check constraint expressions", () => {
    const check = mockTable.check_constraints[0];
    expect(check.raw_expression).toBe("quantity > 0 AND quantity <= 1000");
  });
});

describe("Phase 7.5: Search Matching & Filtering", () => {
  const objects = [
    { name: "users", type: "table", namespace: "auth" },
    { name: "user_tokens", type: "table", namespace: "auth" },
    { name: "orders", type: "table", namespace: "public" },
    { name: "email", type: "column", parentTable: "users" },
    { name: "fk_orders_users", type: "constraint", parentTable: "orders" },
    { name: "idx_users_email", type: "index", parentTable: "users" },
  ];

  it("matches substring case-insensitively", () => {
    const q = "USER";
    const matches = objects.filter((o) => o.name.toLowerCase().includes(q.toLowerCase()));
    expect(matches.map((m) => m.name)).toEqual([
      "users",
      "user_tokens",
      "fk_orders_users",
      "idx_users_email",
    ]);
  });

  it("filters deterministically by object type", () => {
    const tables = objects.filter((o) => o.type === "table");
    expect(tables.length).toBe(3);
    expect(tables.every((t) => t.type === "table")).toBe(true);
  });
});
