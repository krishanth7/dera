"use client";

import { useEffect } from "react";
import { ErrorState } from "@/components/ui/error-state";

export default function ErrorBoundary({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    // Log error to monitoring without exposing internal stack traces
    console.error("Route error boundary triggered:", error);
  }, [error]);

  return (
    <div className="flex min-h-[60vh] items-center justify-center p-6">
      <ErrorState
        title="Application Studio Encountered an Error"
        message={error.message || "An unexpected error occurred in this route."}
        onRetry={() => reset()}
      />
    </div>
  );
}
