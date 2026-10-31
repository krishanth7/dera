"use client";

/**
 * DERA — Advanced Schema Search Studio
 * Coordinates cross-schema discovery, multi-criteria filtering, debounced input,
 * and paginated object inspection.
 */

import React, { useState, useEffect, useMemo, useCallback } from "react";
import { Search, Sparkles, RefreshCw, X, Database } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { SearchFiltersPanel } from "./SearchFiltersPanel";
import { SearchResultsList } from "./SearchResultsList";
import type { SearchFiltersState, SearchResultItem, SearchPaginationState } from "./types";
import { apiClient, type SchemaSummary, type NamespaceItem } from "@/lib/api-client";
import { useWorkspace } from "@/providers/workspace-provider";

interface SchemaSearchStudioProps {
  initialSchemaId?: string;
  initialQuery?: string;
}

export function SchemaSearchStudio({
  initialSchemaId = "",
  initialQuery = "",
}: SchemaSearchStudioProps) {
  const { currentWorkspace } = useWorkspace();
  const [schemas, setSchemas] = useState<SchemaSummary[]>([]);
  const [namespaces, setNamespaces] = useState<NamespaceItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [filters, setFilters] = useState<SearchFiltersState>({
    query: initialQuery,
    objectType: "all",
    namespace: "",
    constraintType: "",
    completeness: "",
    schemaId: initialSchemaId,
  });

  const [pagination, setPagination] = useState<SearchPaginationState>({
    page: 1,
    pageSize: 10,
    totalCount: 0,
  });

  const [rawResults, setRawResults] = useState<SearchResultItem[]>([]);

  // 1. Load schemas and namespaces on workspace change
  useEffect(() => {
    let cancelled = false;

    async function loadWorkspaceMetadata() {
      if (!currentWorkspace?.id) return;
      try {
        const schemaList = await apiClient.listSchemas(currentWorkspace.id);
        if (!cancelled) {
          setSchemas(schemaList);
          if (filters.schemaId) {
            const nsList = await apiClient.listNamespaces(filters.schemaId, currentWorkspace.id);
            if (!cancelled) setNamespaces(nsList);
          }
        }
      } catch (err: unknown) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Failed to load workspace schemas");
        }
      }
    }

    loadWorkspaceMetadata();
    return () => {
      cancelled = true;
    };
  }, [currentWorkspace?.id, filters.schemaId]);

  // 2. Perform cross-schema search with debouncing
  useEffect(() => {
    let cancelled = false;
    const timeoutId = setTimeout(async () => {
      if (!currentWorkspace?.id || schemas.length === 0) return;

      try {
        setLoading(true);
        setError(null);

        const targetSchemas = filters.schemaId
          ? schemas.filter((s) => s.schema_id === filters.schemaId)
          : schemas;

        const collected: SearchResultItem[] = [];

        // Query tables across target schemas
        for (const s of targetSchemas) {
          const { tables } = await apiClient.listTables(s.schema_id, currentWorkspace.id, {
            namespace: filters.namespace || undefined,
            limit: 100,
          });

          for (const t of tables) {
            // Check table match
            const matchesTable =
              (filters.objectType === "all" || filters.objectType === "table") &&
              (!filters.query || t.name.toLowerCase().includes(filters.query.toLowerCase()));

            if (matchesTable) {
              collected.push({
                id: t.table_id,
                name: t.name,
                objectType: t.table_type?.toUpperCase() === "VIEW" ? "view" : "table",
                namespace: t.namespace,
                schemaId: s.schema_id,
                databaseName: s.database_name,
                engine: s.engine,
                matchedField: "Table Name",
                snippet: `${t.column_count} columns, ${t.foreign_key_count} relationships`,
                completeness: s.completeness,
              });
            }

            // If query is present, inspect details for matching columns and constraints
            if (filters.query && filters.query.length >= 2) {
              try {
                const detail = await apiClient.getTableDetail(s.schema_id, t.table_id, currentWorkspace.id);

                // Column search
                if (filters.objectType === "all" || filters.objectType === "column") {
                  for (const col of detail.columns) {
                    if (
                      col.name.toLowerCase().includes(filters.query.toLowerCase()) ||
                      col.native_type.toLowerCase().includes(filters.query.toLowerCase())
                    ) {
                      collected.push({
                        id: col.column_id,
                        name: col.name,
                        objectType: "column",
                        namespace: t.namespace,
                        parentTableName: t.name,
                        parentTableId: t.table_id,
                        schemaId: s.schema_id,
                        databaseName: s.database_name,
                        engine: s.engine,
                        matchedField: col.name.toLowerCase().includes(filters.query.toLowerCase())
                          ? "Column Name"
                          : "Column Data Type",
                        snippet: `${col.native_type} (${col.canonical_type}) ${col.is_nullable ? "NULL" : "NOT NULL"}`,
                        completeness: s.completeness,
                      });
                    }
                  }
                }

                // Constraint search
                if (filters.objectType === "all" || filters.objectType === "constraint") {
                  // Foreign keys
                  for (const fk of detail.foreign_keys) {
                    if (
                      (!filters.constraintType || filters.constraintType === "FOREIGN_KEY") &&
                      (fk.name.toLowerCase().includes(filters.query.toLowerCase()) ||
                        fk.referenced_table_name.toLowerCase().includes(filters.query.toLowerCase()))
                    ) {
                      collected.push({
                        id: fk.constraint_id,
                        name: fk.name,
                        objectType: "constraint",
                        namespace: t.namespace,
                        parentTableName: t.name,
                        parentTableId: t.table_id,
                        schemaId: s.schema_id,
                        databaseName: s.database_name,
                        engine: s.engine,
                        matchedField: "Foreign Key Name",
                        snippet: `FK to ${fk.referenced_table_name}(${fk.referenced_columns.join(", ")})`,
                        completeness: s.completeness,
                      });
                    }
                  }

                  // Primary key
                  if (
                    detail.primary_key &&
                    (!filters.constraintType || filters.constraintType === "PRIMARY_KEY") &&
                    detail.primary_key.name.toLowerCase().includes(filters.query.toLowerCase())
                  ) {
                    collected.push({
                      id: detail.primary_key.constraint_id,
                      name: detail.primary_key.name,
                      objectType: "constraint",
                      namespace: t.namespace,
                      parentTableName: t.name,
                      parentTableId: t.table_id,
                      schemaId: s.schema_id,
                      databaseName: s.database_name,
                      engine: s.engine,
                      matchedField: "Primary Key Name",
                      snippet: `PK (${detail.primary_key.columns.join(", ")})`,
                      completeness: s.completeness,
                    });
                  }
                }

                // Index search
                if (filters.objectType === "all" || filters.objectType === "index") {
                  for (const idx of detail.indexes) {
                    if (
                      idx.name.toLowerCase().includes(filters.query.toLowerCase()) ||
                      idx.columns.some((c) => c.toLowerCase().includes(filters.query.toLowerCase()))
                    ) {
                      collected.push({
                        id: idx.index_id,
                        name: idx.name,
                        objectType: "index",
                        namespace: t.namespace,
                        parentTableName: t.name,
                        parentTableId: t.table_id,
                        schemaId: s.schema_id,
                        databaseName: s.database_name,
                        engine: s.engine,
                        matchedField: "Index Name / Columns",
                        snippet: `INDEX ON (${idx.columns.join(", ")}) ${idx.is_unique ? "[UNIQUE]" : ""}`,
                        completeness: s.completeness,
                      });
                    }
                  }
                }
              } catch {
                // Ignore detail fetch errors during bulk traversal
              }
            }
          }
        }

        if (!cancelled) {
          setRawResults(collected);
          setPagination((prev) => ({
            ...prev,
            page: 1,
            totalCount: collected.length,
          }));
        }
      } catch (err: unknown) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Failed to execute schema search");
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }, 300);

    return () => {
      cancelled = true;
      clearTimeout(timeoutId);
    };
  }, [
    filters.query,
    filters.objectType,
    filters.namespace,
    filters.constraintType,
    filters.schemaId,
    schemas,
    currentWorkspace?.id,
  ]);

  // Paginated slice
  const paginatedResults = useMemo(() => {
    const start = (pagination.page - 1) * pagination.pageSize;
    return rawResults.slice(start, start + pagination.pageSize);
  }, [rawResults, pagination.page, pagination.pageSize]);

  return (
    <div className="space-y-6">
      {/* Search Header */}
      <div className="border-b border-slate-200 dark:border-slate-800 pb-5 space-y-3">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <h1 className="text-xl font-bold tracking-tight text-slate-900 dark:text-slate-100 flex items-center gap-2">
              <Search className="w-5 h-5 text-indigo-500" />
              Advanced Schema Search
            </h1>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
              Cross-schema discovery for tables, views, columns, foreign keys, unique constraints, and indexes.
            </p>
          </div>
          <div className="text-xs font-mono text-slate-400 self-start sm:self-center">
            {schemas.length} Schemas Available
          </div>
        </div>

        {/* Search Input Bar */}
        <div className="relative">
          <Search className="w-4 h-4 absolute left-3.5 top-3 text-slate-400" />
          <Input
            value={filters.query}
            onChange={(e) => setFilters({ ...filters, query: e.target.value })}
            placeholder="Search tables, columns, foreign keys, indexes (press '/' to focus)..."
            className="pl-10 pr-10 h-10 text-sm font-mono"
            autoFocus
          />
          {filters.query && (
            <button
              type="button"
              onClick={() => setFilters({ ...filters, query: "" })}
              aria-label="Clear search input"
              className="absolute right-3 top-2.5 p-1 rounded-md text-slate-400 hover:text-slate-700 dark:hover:text-slate-200"
            >
              <X className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>

      {/* Filters Panel */}
      <SearchFiltersPanel
        filters={filters}
        onChange={setFilters}
        schemas={schemas}
        namespaces={namespaces}
      />

      {/* Results Section */}
      {loading ? (
        <div className="p-12 text-center space-y-3">
          <RefreshCw className="w-6 h-6 animate-spin mx-auto text-indigo-500" />
          <p className="text-xs text-slate-500 font-mono">Searching schema catalog...</p>
        </div>
      ) : error ? (
        <div className="p-4 rounded-xl border border-rose-500/20 bg-rose-500/10 text-rose-700 dark:text-rose-400 text-xs">
          {error}
        </div>
      ) : (
        <SearchResultsList
          results={paginatedResults}
          pagination={pagination}
          onPageChange={(newPage) => setPagination((prev) => ({ ...prev, page: newPage }))}
          onPageSizeChange={(newPageSize) =>
            setPagination((prev) => ({ ...prev, pageSize: newPageSize, page: 1 }))
          }
          query={filters.query}
        />
      )}
    </div>
  );
}
