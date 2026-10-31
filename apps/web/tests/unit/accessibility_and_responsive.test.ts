import { describe, it, expect } from "vitest";
import {
  getContrastRatio,
  getBreakpoint,
  shouldCollapseInspectorPanels,
  sanitizeForAnnouncement,
  getSortAnnouncement,
} from "@/lib/a11y";

describe("Phase 7.6 Accessibility & Responsive Quality Utilities", () => {
  it("computes WCAG 2.2 AA contrast ratios accurately", () => {
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
    expect(shouldCollapseInspectorPanels(375)).toBe(true);
    expect(shouldCollapseInspectorPanels(768)).toBe(true);
    expect(shouldCollapseInspectorPanels(1024)).toBe(false);
    expect(shouldCollapseInspectorPanels(1440)).toBe(false);
  });

  it("sanitizes untrusted database metadata before display", () => {
    const untrustedName = "orders_v2\x00\x1B[31m_DROP_TABLE";
    const cleaned = sanitizeForAnnouncement(untrustedName);
    expect(cleaned).toBe("orders_v2[31m_DROP_TABLE");
    expect(cleaned).not.toContain("\x00");
  });

  it("generates accessible column sorting announcements", () => {
    expect(getSortAnnouncement("created_at", false, true)).toBe("Sort by created_at");
    expect(getSortAnnouncement("created_at", true, true)).toBe("Sorted by created_at, ascending");
    expect(getSortAnnouncement("created_at", true, false)).toBe("Sorted by created_at, descending");
  });
});
