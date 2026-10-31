"use client";

/**
 * DERA — Advanced Schema Search Route Page
 * Path: /search (and /app/search)
 * Search verified tables, views, columns, constraints, and indexes across schemas.
 */

import React from "react";
import { useSearchParams } from "next/navigation";
import { SchemaSearchStudio } from "@/components/schema-search";

export default function SchemaSearchPage() {
  const searchParams = useSearchParams();
  const query = searchParams.get("q") || "";
  const schemaId = searchParams.get("schemaId") || "";

  return <SchemaSearchStudio initialQuery={query} initialSchemaId={schemaId} />;
}
