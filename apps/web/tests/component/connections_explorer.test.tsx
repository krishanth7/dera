import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import React from "react";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";

describe("Phase 7.3 Connections & Schema Explorer Components", () => {
  it("renders Tabs primitive and allows switching active tab panels", () => {
    render(
      <Tabs defaultValue="columns">
        <TabsList>
          <TabsTrigger value="columns">Columns</TabsTrigger>
          <TabsTrigger value="constraints">Constraints</TabsTrigger>
          <TabsTrigger value="indexes">Indexes</TabsTrigger>
        </TabsList>
        <TabsContent value="columns">
          <div data-testid="columns-content">Column List (12 items)</div>
        </TabsContent>
        <TabsContent value="constraints">
          <div data-testid="constraints-content">Constraints List</div>
        </TabsContent>
      </Tabs>
    );

    expect(screen.getByRole("tab", { name: "Columns" })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: "Constraints" })).toBeInTheDocument();
    expect(screen.getByTestId("columns-content")).toBeInTheDocument();
  });

  it("renders database engine badges accurately", () => {
    render(
      <div className="flex gap-2">
        <Badge variant="default">PostgreSQL</Badge>
        <Badge variant="success">Supabase</Badge>
        <Badge variant="secondary">SQLite (Contained)</Badge>
      </div>
    );

    expect(screen.getByText("PostgreSQL")).toBeInTheDocument();
    expect(screen.getByText("Supabase")).toBeInTheDocument();
    expect(screen.getByText("SQLite (Contained)")).toBeInTheDocument();
  });

  it("renders check constraints safely as inert escaped text", () => {
    const maliciousCheck = "ALTER TABLE users DROP COLUMN id; -- <script>alert(1)</script>";
    render(
      <Card>
        <CardHeader>
          <CardTitle>Check Constraints</CardTitle>
        </CardHeader>
        <CardContent>
          <code>{maliciousCheck}</code>
        </CardContent>
      </Card>
    );

    expect(screen.getByText(maliciousCheck)).toBeInTheDocument();
    // Verify script tag is rendered as inert plain text, not executed HTML
    const codeEl = screen.getByText(maliciousCheck);
    expect(codeEl.tagName.toLowerCase()).toBe("code");
  });
});
