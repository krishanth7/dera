import { describe, it, expect } from "vitest";
import { cn, formatDate } from "@/lib/utils";
import { DeraApiError } from "@/lib/api-client";
import { getClientEnv } from "@/lib/env";

describe("Utils & Environment Validation", () => {
  it("cn merges Tailwind class names cleanly", () => {
    const res = cn("px-2 py-1", "bg-blue-600", { "text-white": true, "opacity-50": false });
    expect(res).toContain("px-2");
    expect(res).toContain("bg-blue-600");
    expect(res).toContain("text-white");
    expect(res).not.toContain("opacity-50");
  });

  it("formatDate formats UTC timestamps consistently", () => {
    const formatted = formatDate("2026-10-31T12:00:00Z");
    expect(formatted).toContain("2026");
    expect(formatted).toContain("UTC");
  });

  it("DeraApiError normalizes RFC 7807 problem details", () => {
    const error = new DeraApiError({
      type: "urn:dera:error:not-found",
      title: "Resource Not Found",
      status: 404,
      detail: "Workspace with id ws-123 was not found.",
    });

    expect(error.name).toBe("DeraApiError");
    expect(error.status).toBe(404);
    expect(error.message).toBe("Workspace with id ws-123 was not found.");
    expect(error.problem.type).toBe("urn:dera:error:not-found");
  });

  it("getClientEnv provides safe defaults when env is undefined", () => {
    const clientEnv = getClientEnv();
    expect(clientEnv.NEXT_PUBLIC_DERA_API_URL).toBeDefined();
    expect(clientEnv.NEXT_PUBLIC_APP_URL).toBeDefined();
  });
});
