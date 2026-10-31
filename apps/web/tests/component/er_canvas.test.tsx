import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import React from "react";
import {
  TableNode,
  RelationshipEdge,
  ERToolbar,
  RelationshipDetails,
  AccessibleGraphTable,
  GraphFilters,
  GraphStatus,
  CanvasNode,
  CanvasEdge,
} from "@/components/er-diagram";

describe("Phase 7.4 ER Diagram Canvas Components", () => {
  const mockNode: CanvasNode = {
    id: "tbl_orders",
    name: "orders",
    namespace: "public",
    columns: [
      { name: "id", native_type: "bigint", is_primary_key: true, is_foreign_key: false },
      { name: "customer_id", native_type: "uuid", is_primary_key: false, is_foreign_key: true },
      { name: "total_amount", native_type: "numeric(10,2)", is_primary_key: false, is_foreign_key: false },
    ],
    has_primary_key: true,
    x: 100,
    y: 100,
    width: 260,
    height: 120,
  };

  const mockTargetNode: CanvasNode = {
    id: "tbl_customers",
    name: "customers",
    namespace: "public",
    columns: [
      { name: "id", native_type: "uuid", is_primary_key: true, is_foreign_key: false },
      { name: "name", native_type: "varchar(255)", is_primary_key: false, is_foreign_key: false },
    ],
    has_primary_key: true,
    x: 450,
    y: 100,
    width: 260,
    height: 100,
  };

  const mockEdge: CanvasEdge = {
    id: "edge_orders_customers",
    source_table_id: "tbl_orders",
    source_table_name: "orders",
    target_table_id: "tbl_customers",
    target_table_name: "customers",
    constraint_name: "fk_orders_customer_id",
    source_columns: ["customer_id"],
    target_columns: ["id"],
    column_pairs: [{ source_column: "customer_id", target_column: "id" }],
    on_delete: "CASCADE",
    on_update: "RESTRICT",
    is_composite: false,
    is_self_loop: false,
    is_parallel: false,
    parallel_index: 0,
    parallel_total: 1,
  };

  describe("TableNode Component", () => {
    it("renders table name, namespace, columns, and PK/FK markers inside an SVG container", () => {
      const onSelect = vi.fn();

      render(
        <svg>
          <TableNode node={mockNode} onSelect={onSelect} />
        </svg>
      );

      expect(screen.getByText("orders")).toBeInTheDocument();
      expect(screen.getByText("public")).toBeInTheDocument();
      expect(screen.getByText("id")).toBeInTheDocument();
      expect(screen.getByText("customer_id")).toBeInTheDocument();
      expect(screen.getByText("total_amount")).toBeInTheDocument();
      expect(screen.getByText("PK")).toBeInTheDocument();
      expect(screen.getByText("FK")).toBeInTheDocument();

      // Trigger selection on click
      const nodeEl = screen.getByRole("button", { name: /Table public\.orders/ });
      fireEvent.click(nodeEl);
      expect(onSelect).toHaveBeenCalledWith("tbl_orders");
    });

    it("renders untrusted text safely as inert text to prevent XSS", () => {
      const xssNode: CanvasNode = {
        ...mockNode,
        id: "tbl_xss",
        name: "safe_table_name",
        namespace: "<script>alert(1)</script>",
        columns: [
          {
            name: "safe_col",
            native_type: "text",
            is_primary_key: false,
            is_foreign_key: false,
          },
        ],
      };

      render(
        <svg>
          <TableNode node={xssNode} onSelect={vi.fn()} />
        </svg>
      );

      // Verify that malicious text is rendered as text content, not parsed as HTML elements
      expect(screen.getByText("<script>alert(1)</script>")).toBeInTheDocument();
      expect(document.querySelector("script")).toBeNull();
    });
  });

  describe("RelationshipEdge Component", () => {
    it("renders directed relationship edge connecting source and target nodes", () => {
      const onSelect = vi.fn();

      render(
        <svg>
          <RelationshipEdge
            edge={mockEdge}
            sourceNode={mockNode}
            targetNode={mockTargetNode}
            onSelect={onSelect}
          />
        </svg>
      );

      const edgeEl = screen.getByRole("button", {
        name: /Foreign key fk_orders_customer_id from orders to customers/,
      });
      expect(edgeEl).toBeInTheDocument();

      fireEvent.click(edgeEl);
      expect(onSelect).toHaveBeenCalledWith("edge_orders_customers");
    });

    it("renders composite column count badge when multiple columns mapped", () => {
      const compositeEdge: CanvasEdge = {
        ...mockEdge,
        id: "edge_composite",
        is_composite: true,
        source_columns: ["tenant_id", "customer_id"],
        target_columns: ["tenant_id", "id"],
        column_pairs: [
          { source_column: "tenant_id", target_column: "tenant_id" },
          { source_column: "customer_id", target_column: "id" },
        ],
      };

      render(
        <svg>
          <RelationshipEdge
            edge={compositeEdge}
            sourceNode={mockNode}
            targetNode={mockTargetNode}
            onSelect={vi.fn()}
          />
        </svg>
      );

      expect(screen.getByText("2 cols")).toBeInTheDocument();
    });
  });

  describe("ERToolbar Component", () => {
    it("displays zoom percentage and triggers toolbar actions", () => {
      const onZoomIn = vi.fn();
      const onZoomOut = vi.fn();
      const onFitToView = vi.fn();
      const onResetView = vi.fn();
      const onAutoLayout = vi.fn();
      const onToggleViewMode = vi.fn();

      render(
        <ERToolbar
          zoom={1.25}
          orientation="LR"
          viewMode="canvas"
          showLegend={false}
          showFilters={true}
          onZoomIn={onZoomIn}
          onZoomOut={onZoomOut}
          onFitToView={onFitToView}
          onResetView={onResetView}
          onAutoLayout={onAutoLayout}
          onToggleOrientation={vi.fn()}
          onToggleViewMode={onToggleViewMode}
          onToggleLegend={vi.fn()}
          onToggleFilters={vi.fn()}
        />
      );

      expect(screen.getByText("125%")).toBeInTheDocument();

      fireEvent.click(screen.getByRole("button", { name: "Zoom in" }));
      expect(onZoomIn).toHaveBeenCalledTimes(1);

      fireEvent.click(screen.getByRole("button", { name: "Zoom out" }));
      expect(onZoomOut).toHaveBeenCalledTimes(1);

      fireEvent.click(screen.getByRole("button", { name: "Fit graph to view" }));
      expect(onFitToView).toHaveBeenCalledTimes(1);

      fireEvent.click(screen.getByRole("button", { name: "Reset viewport to 100%" }));
      expect(onResetView).toHaveBeenCalledTimes(1);

      fireEvent.click(screen.getByRole("button", { name: "Recompute deterministic auto-layout" }));
      expect(onAutoLayout).toHaveBeenCalledTimes(1);

      fireEvent.click(
        screen.getByRole("button", { name: "Switch between Visual Canvas and Accessible Table view" })
      );
      expect(onToggleViewMode).toHaveBeenCalledTimes(1);
    });
  });

  describe("RelationshipDetails Drawer", () => {
    it("renders edge constraint metadata, ordered column mapping, and referential actions", () => {
      const onSelectNode = vi.fn();
      const onClose = vi.fn();

      render(
        <RelationshipDetails
          selectedNode={null}
          selectedEdge={mockEdge}
          allNodes={[mockNode, mockTargetNode]}
          allEdges={[mockEdge]}
          schemaId="schema_abc"
          onSelectNode={onSelectNode}
          onSelectEdge={vi.fn()}
          onClose={onClose}
        />
      );

      expect(screen.getByText("fk_orders_customer_id")).toBeInTheDocument();
      expect(screen.getByText("orders")).toBeInTheDocument();
      expect(screen.getByText("customers")).toBeInTheDocument();
      expect(screen.getByText("CASCADE")).toBeInTheDocument();
      expect(screen.getByText("RESTRICT")).toBeInTheDocument();

      // Click referencing table link
      fireEvent.click(screen.getByText("orders"));
      expect(onSelectNode).toHaveBeenCalledWith("tbl_orders");

      // Click close button
      fireEvent.click(screen.getByRole("button", { name: "Close details panel" }));
      expect(onClose).toHaveBeenCalledTimes(1);
    });

    it("renders table entity details when a node is selected", () => {
      render(
        <RelationshipDetails
          selectedNode={mockNode}
          selectedEdge={null}
          allNodes={[mockNode, mockTargetNode]}
          allEdges={[mockEdge]}
          schemaId="schema_abc"
          onSelectNode={vi.fn()}
          onSelectEdge={vi.fn()}
          onClose={vi.fn()}
        />
      );

      expect(screen.getByText("Table Entity Details")).toBeInTheDocument();
      expect(screen.getByText("3 columns")).toBeInTheDocument();
      expect(screen.getByText("Primary Key Defined")).toBeInTheDocument();
      expect(screen.getByText("Inspect Table")).toBeInTheDocument();
      expect(screen.getByText("Dependencies")).toBeInTheDocument();
    });
  });

  describe("AccessibleGraphTable Component", () => {
    it("renders accessible tabular format for screen reader users", () => {
      render(
        <AccessibleGraphTable
          nodes={[mockNode, mockTargetNode]}
          edges={[mockEdge]}
          onSelectNode={vi.fn()}
          onSelectEdge={vi.fn()}
        />
      );

      expect(screen.getByText("Accessible Relationship Directory")).toBeInTheDocument();
      expect(screen.getByRole("columnheader", { name: "Constraint Name" })).toBeInTheDocument();
      expect(screen.getByRole("columnheader", { name: "Referencing (Child)" })).toBeInTheDocument();
      expect(screen.getByRole("columnheader", { name: "Referenced (Parent)" })).toBeInTheDocument();
      expect(screen.getByText("fk_orders_customer_id")).toBeInTheDocument();
    });
  });

  describe("GraphStatus Component", () => {
    it("renders database engine and graph statistics accurately", () => {
      render(
        <GraphStatus
          databaseName="production_db"
          engine="postgresql"
          nodeCount={12}
          edgeCount={8}
          compositeCount={2}
          selfLoopCount={1}
          completeness="complete"
        />
      );

      expect(screen.getByText("production_db")).toBeInTheDocument();
      expect(screen.getByText("postgresql")).toBeInTheDocument();
      expect(screen.getByText("complete")).toBeInTheDocument();
      expect(screen.getByText("12")).toBeInTheDocument();
      expect(screen.getByText("8")).toBeInTheDocument();
      expect(screen.getByText("2")).toBeInTheDocument();
      expect(screen.getByText("1")).toBeInTheDocument();
    });
  });
});
