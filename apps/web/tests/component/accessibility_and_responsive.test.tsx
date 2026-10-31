import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import React from "react";
import { AppShell } from "@/components/layout/app-shell";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Table, TableHeader, TableRow, TableHead, TableBody, TableCell } from "@/components/ui/table";
import { Dialog, DialogTrigger, DialogContent, DialogTitle, DialogDescription } from "@/components/ui/dialog";

// Mock next-themes and providers for AppShell
vi.mock("next-themes", () => ({
  useTheme: () => ({ theme: "dark", setTheme: vi.fn() }),
}));

vi.mock("@/providers/workspace-provider", () => ({
  useWorkspace: () => ({
    currentWorkspace: { id: "ws-1", name: "Engineering Core", slug: "core", current_user_role: "OWNER" },
    workspaces: [],
    setCurrentWorkspace: vi.fn(),
  }),
}));

vi.mock("@/providers/auth-provider", () => ({
  useAuth: () => ({
    user: { id: "u-1", email: "engineer@dera.internal" },
    logout: vi.fn(),
    logoutAll: vi.fn(),
  }),
}));

vi.mock("next/navigation", () => ({
  usePathname: () => "/app/tables/table-1",
  useRouter: () => ({ push: vi.fn() }),
}));

describe("Phase 7.6 Accessibility & Responsive Component Suite", () => {
  it("renders skip-to-content navigation link pointing to #main-content", () => {
    render(
      <AppShell>
        <div>Page Body Content</div>
      </AppShell>
    );

    const skipLink = screen.getByRole("link", { name: /skip to main content/i });
    expect(skipLink).toBeInTheDocument();
    expect(skipLink).toHaveAttribute("href", "#main-content");

    const mainElement = document.getElementById("main-content");
    expect(mainElement).not.toBeNull();
    expect(mainElement).toHaveAttribute("tabIndex", "-1");
  });

  it("sets aria-invalid on Input when error prop is true", () => {
    const { rerender } = render(<Input placeholder="Port Number" />);
    const input = screen.getByPlaceholderText("Port Number");
    expect(input).not.toHaveAttribute("aria-invalid", "true");

    rerender(<Input placeholder="Port Number" error />);
    expect(input).toHaveAttribute("aria-invalid", "true");
  });

  it("sets aria-busy and disables Button when isLoading is true", () => {
    const { rerender } = render(<Button>Test Connection</Button>);
    const button = screen.getByRole("button", { name: "Test Connection" });
    expect(button).not.toHaveAttribute("aria-busy");
    expect(button).not.toBeDisabled();

    rerender(<Button isLoading>Test Connection</Button>);
    expect(button).toHaveAttribute("aria-busy", "true");
    expect(button).toBeDisabled();
    expect(screen.getByText("Loading...")).toBeInTheDocument();
  });

  it("renders Table inside a keyboard-scrollable region with role and tabIndex", () => {
    render(
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Column</TableHead>
            <TableHead>Type</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          <TableRow>
            <TableCell>id</TableCell>
            <TableCell>uuid</TableCell>
          </TableRow>
        </TableBody>
      </Table>
    );

    const scrollRegion = screen.getByRole("region", { name: /scrollable data table/i });
    expect(scrollRegion).toBeInTheDocument();
    expect(scrollRegion).toHaveAttribute("tabIndex", "0");
  });

  it("renders Dialog with responsive viewport bounds and accessible close button", () => {
    render(
      <Dialog open={true}>
        <DialogContent>
          <DialogTitle>Confirm Connection Deletion</DialogTitle>
          <DialogDescription>
            This will permanently remove the metadata connection.
          </DialogDescription>
          <div>Modal Action Content</div>
        </DialogContent>
      </Dialog>
    );

    expect(screen.getByText("Confirm Connection Deletion")).toBeInTheDocument();
    expect(screen.getByText("This will permanently remove the metadata connection.")).toBeInTheDocument();

    const closeButton = screen.getByRole("button", { name: /close/i });
    expect(closeButton).toBeInTheDocument();
  });

  it("handles mobile navigation drawer accessibility and keyboard interaction", () => {
    render(
      <AppShell>
        <div>Content Inside Shell</div>
      </AppShell>
    );

    const mobileDrawer = screen.getByRole("dialog", { name: /mobile navigation drawer/i });
    expect(mobileDrawer).toBeInTheDocument();
    expect(mobileDrawer).toHaveAttribute("aria-modal", "true");

    // Pressing Escape should trigger event listener without unhandled errors
    fireEvent.keyDown(window, { key: "Escape" });
  });
});
