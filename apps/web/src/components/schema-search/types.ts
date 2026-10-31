/**
 * DERA — Advanced Schema Search Types & Contracts
 * Phase 7.5: Table Inspector, Advanced Search & Dependency Visualization
 */

export type SearchObjectType =
  | "all"
  | "table"
  | "view"
  | "column"
  | "constraint"
  | "index"
  | "namespace";

export interface SearchResultItem {
  id: string;
  name: string;
  objectType: SearchObjectType;
  namespace: string;
  parentTableName?: string;
  parentTableId?: string;
  schemaId: string;
  databaseName: string;
  engine: string;
  matchedField: string;
  snippet: string;
  completeness: string;
  metadata?: Record<string, unknown>;
}

export interface SearchFiltersState {
  query: string;
  objectType: SearchObjectType;
  namespace: string;
  constraintType: string;
  completeness: string;
  schemaId: string;
}

export interface SearchPaginationState {
  page: number;
  pageSize: number;
  totalCount: number;
}
