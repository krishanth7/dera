import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import React from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";

describe("Component Primitives", () => {
  it("renders Button with text and handles loading state", () => {
    const { rerender } = render(<Button>Execute Query</Button>);
    expect(screen.getByRole("button", { name: "Execute Query" })).toBeInTheDocument();

    rerender(<Button isLoading>Execute Query</Button>);
    expect(screen.getByText("Loading...")).toBeInTheDocument();
  });

  it("renders Badge variants correctly", () => {
    render(<Badge variant="success">Verified</Badge>);
    expect(screen.getByText("Verified")).toBeInTheDocument();
  });

  it("renders Card with header, title, and content", () => {
    render(
      <Card>
        <CardHeader>
          <CardTitle>Database Diagnostics</CardTitle>
        </CardHeader>
        <CardContent>All systems operational.</CardContent>
      </Card>
    );

    expect(screen.getByText("Database Diagnostics")).toBeInTheDocument();
    expect(screen.getByText("All systems operational.")).toBeInTheDocument();
  });

  it("renders EmptyState with accessible title and description", () => {
    render(
      <EmptyState
        title="No Schema Snapshots"
        description="Capture a new snapshot to begin audit."
      />
    );

    expect(screen.getByText("No Schema Snapshots")).toBeInTheDocument();
    expect(screen.getByText("Capture a new snapshot to begin audit.")).toBeInTheDocument();
  });

  it("renders ErrorState with alert role and message", () => {
    render(<ErrorState title="Connection Failed" message="Dialect probe timed out." />);

    expect(screen.getByRole("alert")).toBeInTheDocument();
    expect(screen.getByText("Connection Failed")).toBeInTheDocument();
    expect(screen.getByText("Dialect probe timed out.")).toBeInTheDocument();
  });
});
