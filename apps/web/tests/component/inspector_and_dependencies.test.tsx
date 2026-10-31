/**
 * @vitest-environment jsdom
 */

import React from "react";
import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { TableMetadataHeader } from "@/components/table-inspector/TableMetadataHeader";
import { TableSummaryCards } from "@/components/table-inspector/TableSummaryCards";
import { ColumnsTab } from "@/components/table-inspector/ColumnsTab";
import { ConstraintsTab } from "@/components/table-inspector/ConstraintsTab";
import { IndexesTab } from "@/components/table-inspector/IndexesTab";
import { CycleAnalysisPanel } from "@/components/dependency-explorer/CycleAnalysisPanel";
import { ExecutionOrderingPanel } from "@/components/dependency-explorer/ExecutionOrderingPanel";
import { AccessibleDependencyTable } from "@/components/dependency-explorer/AccessibleDependencyTable";
import { SearchResultsList } from "@/components/schema-search/SearchResultsList";
import type { TableDetailItem, CycleReportResponse, DependencyAnalysisResponse, RelationshipGraphResponse } from "@/lib/api-client";
import type { TableInspectorViewModel } from "@/components/table-inspector/types";

const mockTable: TableDetailItem = {
  table_id: "tbl-orders-01",
  namespace: "ecommerce",
  name: "orders",
  table_type: "TABLE",
  columns: [
    {
      column_id: "col-1",
      table_id: "tbl-orders-01",
      name: "id",
      ordinal_position: 1,
      native_type: "uuid",
      canonical_type: "string",
      is_nullable: false,
      is_primary_key: true,
    },
    {
      column_id: "col-2",
      table_id: "tbl-orders-01",
      name: "customer_id",
      ordinal_position: 2,
      native_type: "uuid",
      canonical_type: "string",
      is_nullable: false,
      is_primary_key: false,
    },
    {
      column_id: "col-3",
      table_id: "tbl-orders-01",
      name: "status",
      ordinal_position: 3,
      native_type: "varchar(50)",
      canonical_type: "string",
      is_nullable: true,
      is_primary_key: false,
      default_expression: "'pending'",
    },
  ],
  primary_key: {
    constraint_id: "pk-orders",
    name: "pk_orders",
    columns: ["id"],
  },
  foreign_keys: [
    {
      constraint_id: "fk-orders-customer",
      name: "fk_orders_customer_id",
      source_columns: ["customer_id"],
      referenced_table_id: "tbl-customers",
      referenced_table_name: "customers",
      referenced_columns: ["id"],
      on_delete: "RESTRICT",
      on_update: "CASCADE",
    },
  ],
  unique_constraints: [
    {
      constraint_id: "uq-order-code",
      name: "uq_orders_code",
      constraint_type: "UNIQUE",
      columns: ["order_code"],
      raw_expression: null,
    },
  ],
  check_constraints: [
    {
      constraint_id: "chk-order-status",
      name: "chk_status_valid",
      constraint_type: "CHECK",
      columns: ["status"],
      raw_expression: "status IN ('pending', 'shipped', 'delivered')",
    },
  ],
  indexes: [
    {
      index_id: "idx-orders-cust",
      name: "idx_orders_customer_id",
      is_unique: false,
      is_primary: false,
      columns: ["customer_id"],
    },
  ],
};

const mockViewModel: TableInspectorViewModel = {
  table: mockTable,
  schemaId: "schema-001",
  databaseName: "prod_db",
  sourceEngine: "postgresql",
  completeness: "complete",
};

describe("Component: TableMetadataHeader", () => {
  it("renders table name, namespace, engine, and completeness", () => {
    render(<TableMetadataHeader viewModel={mockViewModel} />);
    expect(screen.getByText("orders")).toBeDefined();
    expect(screen.getByText("namespace: ecommerce")).toBeDefined();
    expect(screen.getByText("postgresql")).toBeDefined();
    expect(screen.getByText("complete")).toBeDefined();
  });

  it("renders snapshot banner when viewing snapshot metadata", () => {
    const snapshotViewModel: TableInspectorViewModel = {
      ...mockViewModel,
      isSnapshot: true,
      snapshotFingerprint: "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    };
    render(<TableMetadataHeader viewModel={snapshotViewModel} />);
    expect(screen.getByText(/Immutable Snapshot/i)).toBeDefined();
  });
});

describe("Component: TableSummaryCards", () => {
  it("displays verified counts and handles tab switching", () => {
    const handleTabChange = vi.fn();
    render(
      <TableSummaryCards
        table={mockTable}
        activeTab="columns"
        onTabChange={handleTabChange}
      />
    );

    expect(screen.getByText("Columns")).toBeDefined();
    expect(screen.getByText("Primary Key")).toBeDefined();
    expect(screen.getByText("Foreign Keys")).toBeDefined();
    expect(screen.getByText("Unique Constraints")).toBeDefined();
    expect(screen.getByText("Check Constraints")).toBeDefined();
    expect(screen.getByText("Indexes")).toBeDefined();

    // Click Constraints card
    fireEvent.click(screen.getByText("Foreign Keys"));
    expect(handleTabChange).toHaveBeenCalledWith("constraints");
  });
});

describe("Component: ColumnsTab", () => {
  it("renders columns and handles search filtering", () => {
    render(<ColumnsTab table={mockTable} />);

    expect(screen.getByText("id")).toBeDefined();
    expect(screen.getByText("customer_id")).toBeDefined();
    expect(screen.getByText("status")).toBeDefined();

    // Filter by name
    const searchInput = screen.getByPlaceholderText(/filter columns/i);
    fireEvent.change(searchInput, { target: { value: "cust" } });

    expect(screen.getByText("customer_id")).toBeDefined();
    expect(screen.queryByText("status")).toBeNull();
  });

  it("expands column details on expand button click", () => {
    render(<ColumnsTab table={mockTable} />);

    const expandButtons = screen.getAllByLabelText(/expand column details/i);
    fireEvent.click(expandButtons[0]);

    expect(screen.getByText(/Column Identity/i)).toBeDefined();
    expect(screen.getByText("ID: col-1")).toBeDefined();
  });
});

describe("Component: ConstraintsTab", () => {
  it("renders primary key, composite mapping, referential actions, and inert check expression", () => {
    render(<ConstraintsTab table={mockTable} schemaId="schema-001" />);

    expect(screen.getByText("pk_orders")).toBeDefined();
    expect(screen.getByText("fk_orders_customer_id")).toBeDefined();
    expect(screen.getByText("customers")).toBeDefined();
    expect(screen.getByText("RESTRICT")).toBeDefined();
    expect(screen.getByText("CASCADE")).toBeDefined();
    expect(screen.getByText("uq_orders_code")).toBeDefined();
    expect(screen.getByText("chk_status_valid")).toBeDefined();
    expect(screen.getByText("status IN ('pending', 'shipped', 'delivered')")).toBeDefined();
  });
});

describe("Component: CycleAnalysisPanel", () => {
  const mockCycleReport: CycleReportResponse = {
    has_cycles: true,
    cycle_count: 1,
    scc_count: 2,
    cyclic_scc_count: 1,
    cycles: [
      {
        cycle_id: "c-1",
        cycle_kind: "DIRECT_MUTUAL",
        table_ids: ["orders", "invoices"],
        length: 2,
        breakability_strategy: "DEFER_FOREIGN_KEY",
      },
    ],
    components: [
      {
        scc_id: "scc-1",
        is_cyclic: true,
        table_ids: ["orders", "invoices"],
        size: 2,
      },
      {
        scc_id: "scc-2",
        is_cyclic: false,
        table_ids: ["users"],
        size: 1,
      },
    ],
  };

  it("renders cycle loop, SCC badges, and breakability strategy", () => {
    render(<CycleAnalysisPanel cycleReport={mockCycleReport} schemaId="schema-001" />);

    expect(screen.getByText(/Circular Dependency Cycle Detected/i)).toBeDefined();
    expect(screen.getByText("c-1")).toBeDefined();
    expect(screen.getByText("Strategy: DEFER_FOREIGN_KEY")).toBeDefined();
    expect(screen.getByText("scc-1")).toBeDefined();
    expect(screen.getByText("Cyclic SCC")).toBeDefined();
  });
});

describe("Component: ExecutionOrderingPanel", () => {
  const mockAnalysis: DependencyAnalysisResponse = {
    database_name: "test_db",
    total_tables: 3,
    total_edges: 2,
    has_cycles: false,
    cycle_count: 0,
    scc_count: 3,
    cyclic_scc_count: 0,
    creation_order: ["customers", "orders", "order_items"],
    drop_order: ["order_items", "orders", "customers"],
    levels: [
      { level_index: 0, table_ids: ["customers"] },
      { level_index: 1, table_ids: ["orders"] },
      { level_index: 2, table_ids: ["order_items"] },
    ],
  };

  it("renders parallel levels and switches to creation order", () => {
    render(<ExecutionOrderingPanel analysis={mockAnalysis} />);

    expect(screen.getByText("LEVEL 0")).toBeDefined();
    expect(screen.getByText("Independent Root Tables")).toBeDefined();

    // Switch to Creation Order
    fireEvent.click(screen.getByText(/Topological Creation Order/i));
    expect(screen.getByText("#1")).toBeDefined();
    expect(screen.getByText("#2")).toBeDefined();
    expect(screen.getByText("#3")).toBeDefined();
  });
});

describe("Component: AccessibleDependencyTable", () => {
  const mockAnalysis: DependencyAnalysisResponse = {
    database_name: "test_db",
    total_tables: 2,
    total_edges: 1,
    has_cycles: false,
    cycle_count: 0,
    scc_count: 2,
    cyclic_scc_count: 0,
    creation_order: ["customers", "orders"],
    drop_order: ["orders", "customers"],
    levels: [{ level_index: 0, table_ids: ["customers"] }, { level_index: 1, table_ids: ["orders"] }],
  };

  const mockRelationships: RelationshipGraphResponse = {
    database_name: "test_db",
    engine: "postgresql",
    node_count: 2,
    edge_count: 1,
    nodes: [
      { table_id: "customers", namespace: "public", name: "customers" },
      { table_id: "orders", namespace: "public", name: "orders" },
    ],
    edges: [
      {
        edge_id: "e-1",
        source_table_id: "orders",
        source_table_name: "orders",
        target_table_id: "customers",
        target_table_name: "customers",
        constraint_name: "fk_orders_cust",
        source_columns: ["customer_id"],
        target_columns: ["id"],
      },
    ],
  };

  const mockCycles: CycleReportResponse = {
    has_cycles: false,
    cycle_count: 0,
    scc_count: 2,
    cyclic_scc_count: 0,
    cycles: [],
    components: [
      { scc_id: "scc-1", is_cyclic: false, table_ids: ["customers"], size: 1 },
      { scc_id: "scc-2", is_cyclic: false, table_ids: ["orders"], size: 1 },
    ],
  };

  it("renders semantic accessibility table with correct columns and roles", () => {
    render(
      <AccessibleDependencyTable
        analysis={mockAnalysis}
        relationships={mockRelationships}
        cycles={mockCycles}
        schemaId="schema-001"
      />
    );

    expect(screen.getByRole("table")).toBeDefined();
    expect(screen.getAllByText("customers").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("orders").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("Acyclic").length).toBe(2);
  });
});

describe("Component: SearchResultsList", () => {
  it("renders search results with badges and handles empty results", () => {
    const results = [
      {
        id: "t-1",
        name: "invoices",
        objectType: "table" as const,
        namespace: "billing",
        schemaId: "s-1",
        databaseName: "billing_db",
        engine: "postgresql",
        matchedField: "Table Name",
        snippet: "10 columns",
        completeness: "complete",
      },
    ];

    const pagination = { page: 1, pageSize: 10, totalCount: 1 };

    const { rerender } = render(
      <SearchResultsList
        results={results}
        pagination={pagination}
        onPageChange={vi.fn()}
        onPageSizeChange={vi.fn()}
        query="inv"
      />
    );

    expect(screen.getByText("invoices")).toBeDefined();
    expect(screen.getByText("billing")).toBeDefined();
    expect(screen.getByText("table")).toBeDefined();

    // Rerender empty
    rerender(
      <SearchResultsList
        results={[]}
        pagination={{ page: 1, pageSize: 10, totalCount: 0 }}
        onPageChange={vi.fn()}
        onPageSizeChange={vi.fn()}
        query="nonexistent"
      />
    );

    expect(screen.getByText("No Database Objects Matched")).toBeDefined();
  });
});
