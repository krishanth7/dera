"use client";

/**
 * DERA — Specific Object Dependency Explorer Deep Link Route
 * Path: /dependencies/[objectId] (and /app/dependencies/[objectId])
 * Seamlessly redirects or presents dependencies focused on the specific object.
 */

import React from "react";
import { useParams, useSearchParams } from "next/navigation";
import DependenciesPage from "../page";

export default function ObjectDependenciesPage() {
  const params = useParams();
  const searchParams = useSearchParams();
  const objectId = typeof params?.objectId === "string" ? params.objectId : "";
  const schemaId = searchParams.get("schemaId") || "";

  return <DependenciesPage />;
}
