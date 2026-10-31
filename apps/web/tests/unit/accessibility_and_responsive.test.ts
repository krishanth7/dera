import { describe, it, expect } from "vitest";

describe("Phase 7.6 Accessibility & Responsive Quality Utilities", () => {
  it("computes WCAG 2.2 AA contrast ratios accurately", () => {
    // Relative luminance calculation helper
    function getLuminance(r: number, g: number, b: number): number {
      const a = [r, g, b].map(v => {
        v /= 255;
        return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4);
      });
      return a[0] * 0.2126 + a[1] * 0.7152 + a[2] * 0.0722;
    }

    function getContrastRatio(rgb1: [number, number, number], rgb2: [number, number, number]): number {
      const lum1 = getLuminance(...rgb1);
      const lum2 = getLuminance(...rgb2);
      const brightest = Math.max(lum1, lum2);
      const darkest = Math.min(lum1, lum2);
      return (brightest + 0.05) / (darkest + 0.05);
    }

    // High contrast black on white: >= 7:1 (AAA)
    const blackOnWhite = getContrastRatio([0, 0, 0], [255, 255, 255]);
    expect(blackOnWhite).toBeGreaterThanOrEqual(7.0);

    // DERA corporate blue (#2563EB = [37, 99, 235]) on white: >= 4.5:1 (AA for normal text)
    const blueOnWhite = getContrastRatio([37, 99, 235], [255, 255, 255]);
    expect(blueOnWhite).toBeGreaterThanOrEqual(4.5);

    // Dark theme foreground (#F8FAFC = [248, 250, 252]) on dark background (#0F172A = [15, 23, 42])
    const darkThemeContrast = getContrastRatio([248, 250, 252], [15, 23, 42]);
    expect(darkThemeContrast).toBeGreaterThanOrEqual(7.0);
  });

  it("classifies responsive viewports correctly across standard breakpoints", () => {
    type Breakpoint = "xs" | "sm" | "md" | "lg" | "xl" | "2xl";

    function getBreakpoint(width: number): Breakpoint {
      if (width < 640) return "xs";
      if (width < 768) return "sm";
      if (width < 1024) return "md";
      if (width < 1280) return "lg";
      if (width < 1536) return "xl";
      return "2xl";
    }

    expect(getBreakpoint(320)).toBe("xs");
    expect(getBreakpoint(375)).toBe("xs");
    expect(getBreakpoint(390)).toBe("xs");
    expect(getBreakpoint(640)).toBe("sm");
    expect(getBreakpoint(768)).toBe("md");
    expect(getBreakpoint(1024)).toBe("lg");
    expect(getBreakpoint(1280)).toBe("xl");
    expect(getBreakpoint(1440)).toBe("xl");
    expect(getBreakpoint(1920)).toBe("2xl");
  });

  it("determines whether multi-panel studio layouts should collapse based on viewport", () => {
    function shouldCollapseInspectorPanels(width: number): boolean {
      // Below 1024px (desktop), side panels should stack or collapse into tabs
      return width < 1024;
    }

    expect(shouldCollapseInspectorPanels(375)).toBe(true);
    expect(shouldCollapseInspectorPanels(768)).toBe(true);
    expect(shouldCollapseInspectorPanels(1024)).toBe(false);
    expect(shouldCollapseInspectorPanels(1440)).toBe(false);
  });

  it("sanitizes untrusted database metadata before display", () => {
    function sanitizeForAnnouncement(text: string): string {
      // Remove control characters and limit length for screen reader speech synthesis
      return text.replace(/[\x00-\x1F\x7F]/g, "").trim().slice(0, 255);
    }

    const untrustedName = "orders_v2\x00\x1B[31m_DROP_TABLE";
    const cleaned = sanitizeForAnnouncement(untrustedName);
    expect(cleaned).toBe("orders_v2[31m_DROP_TABLE");
    expect(cleaned).not.toContain("\x00");
  });

  it("generates accessible column sorting announcements", () => {
    function getSortAnnouncement(columnName: string, isSorted: boolean, sortAsc: boolean): string {
      if (!isSorted) {
        return `Sort by ${columnName}`;
      }
      return `${columnName} sorted ${sortAsc ? "ascending" : "descending"}. Click to sort ${sortAsc ? "descending" : "ascending"}.`;
    }

    expect(getSortAnnouncement("ordinal", false, true)).toBe("Sort by ordinal");
    expect(getSortAnnouncement("ordinal", true, true)).toBe("ordinal sorted ascending. Click to sort descending.");
    expect(getSortAnnouncement("name", true, false)).toBe("name sorted descending. Click to sort ascending.");
  });
});
