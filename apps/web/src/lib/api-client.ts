/**
 * DERA Web — Type-Safe API Client.
 *
 * Connects the web visualizer to the DERA API gateway.
 * Strictly forbids storing or transmitting raw database passwords in client state.
 */

import type { SystemMeta } from "../types/index.js";

declare const process: { env?: Record<string, string | undefined> } | undefined;

export class DeraApiClient {
  private baseUrl: string;

  constructor(baseUrl?: string) {
    const envUrl = typeof process !== "undefined" ? process?.env?.NEXT_PUBLIC_DERA_API_URL : undefined;
    this.baseUrl = baseUrl || envUrl || "http://localhost:8000";
  }

  public async getHealth(): Promise<{ status: string; service: string; version: string }> {
    const res = await fetch(`${this.baseUrl}/health`);
    if (!res.ok) {
      throw new Error(`API health check failed with status ${res.status}`);
    }
    return res.json();
  }

  public async getMeta(): Promise<SystemMeta> {
    const res = await fetch(`${this.baseUrl}/api/v1/meta`);
    if (!res.ok) {
      throw new Error(`API meta retrieval failed with status ${res.status}`);
    }
    return res.json();
  }
}

export const apiClient = new DeraApiClient();
