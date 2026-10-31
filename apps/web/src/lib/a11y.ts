/**
 * DERA — Accessibility & Responsive Design Utilities
 * Phase 7.6: Frontend Quality & WCAG 2.2 Level AA Verification
 */

export type Breakpoint = "xs" | "sm" | "md" | "lg" | "xl" | "2xl";

/**
 * Calculates relative luminance for an sRGB component per WCAG 2.2 specifications.
 */
export function getLuminance(r: number, g: number, b: number): number {
  const a = [r, g, b].map((v) => {
    const s = v / 255;
    return s <= 0.03928 ? s / 12.92 : Math.pow((s + 0.055) / 1.055, 2.4);
  });
  return a[0] * 0.2126 + a[1] * 0.7152 + a[2] * 0.0722;
}

/**
 * Calculates contrast ratio between two RGB colors (1:1 to 21:1).
 */
export function getContrastRatio(
  rgb1: [number, number, number],
  rgb2: [number, number, number]
): number {
  const lum1 = getLuminance(...rgb1);
  const lum2 = getLuminance(...rgb2);
  const brightest = Math.max(lum1, lum2);
  const darkest = Math.min(lum1, lum2);
  return (brightest + 0.05) / (darkest + 0.05);
}

/**
 * Classifies window viewport width into Tailwind CSS breakpoint names.
 */
export function getBreakpoint(width: number): Breakpoint {
  if (width < 640) return "xs";
  if (width < 768) return "sm";
  if (width < 1024) return "md";
  if (width < 1280) return "lg";
  if (width < 1536) return "xl";
  return "2xl";
}

/**
 * Determines whether multi-panel studio layouts should collapse into tabs/drawer.
 */
export function shouldCollapseInspectorPanels(width: number): boolean {
  return width < 1024;
}

/**
 * Sanitizes untrusted metadata strings for screen reader speech announcements.
 */
export function sanitizeForAnnouncement(text: string): string {
  return text.replace(/[\x00-\x1F\x7F]/g, "").trim().slice(0, 255);
}

/**
 * Formats an accessible announcement string for column sorting state.
 */
export function getSortAnnouncement(
  columnName: string,
  isSorted: boolean,
  sortAsc: boolean
): string {
  if (!isSorted) {
    return `Sort by ${columnName}`;
  }
  return `Sorted by ${columnName}, ${sortAsc ? "ascending" : "descending"}`;
}
