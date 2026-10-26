/**
 * DERA Web — Application Type Definitions.
 */

export * from "@dera/contracts";

export interface SystemMeta {
  name: string;
  version: string;
  environment: string;
  zero_ai_policy: boolean;
  read_only_enforced: boolean;
  supported_dialects: string[];
}

export interface CanvasState {
  selectedTableId: string | null;
  activeView: "diagram" | "diagnostics" | "data-dictionary";
  zoomLevel: number;
}
