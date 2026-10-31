"use client";

import * as React from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  ArrowLeft,
  CheckCircle2,
  Database,
  Lock,
  RefreshCw,
  Server,
  ShieldAlert,
  ShieldCheck,
  XCircle,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { useWorkspace } from "@/providers/workspace-provider";
import {
  apiClient,
  ConnectionTestPayload,
  ConnectionTestResult,
  CreateConnectionPayload,
} from "@/lib/api-client";

type EngineType = "postgresql" | "sqlite" | "mysql" | "mariadb";

interface EngineCard {
  id: EngineType;
  provider: string;
  name: string;
  badge: string;
  description: string;
  defaultPort: number | null;
}

const ENGINES: EngineCard[] = [
  {
    id: "postgresql",
    provider: "generic",
    name: "PostgreSQL",
    badge: "Production Ready",
    description: "Connect to standard PostgreSQL 12–16+ instances.",
    defaultPort: 5432,
  },
  {
    id: "postgresql",
    provider: "supabase",
    name: "Supabase PostgreSQL",
    badge: "Cloud Dialect",
    description: "Connect via direct port 5432 or transaction pooler port 6543.",
    defaultPort: 5432,
  },
  {
    id: "mysql",
    provider: "generic",
    name: "MySQL",
    badge: "Production Ready",
    description: "Connect to MySQL 8.x network database instances.",
    defaultPort: 3306,
  },
  {
    id: "mariadb",
    provider: "generic",
    name: "MariaDB",
    badge: "Production Ready",
    description: "Connect to MariaDB 10.x/11.x server deployments.",
    defaultPort: 3306,
  },
  {
    id: "sqlite",
    provider: "generic",
    name: "SQLite (Contained)",
    badge: "Filesystem Isolated",
    description: "Inspect local or workspace-isolated SQLite embedded files.",
    defaultPort: null,
  },
];

export default function NewConnectionPage() {
  const router = useRouter();
  const { currentWorkspace } = useWorkspace();

  const [selectedEngine, setSelectedEngine] = React.useState<EngineCard>(ENGINES[0]);
  const [name, setName] = React.useState<string>("");
  const [database, setDatabase] = React.useState<string>("");
  const [host, setHost] = React.useState<string>("localhost");
  const [port, setPort] = React.useState<string>("5432");
  const [username, setUsername] = React.useState<string>("postgres");
  const [password, setPassword] = React.useState<string>("");
  const [sslMode, setSslMode] = React.useState<string>("prefer");

  // Diagnostics & submission
  const [testing, setTesting] = React.useState<boolean>(false);
  const [testResult, setTestResult] = React.useState<ConnectionTestResult | null>(null);
  const [saving, setSaving] = React.useState<boolean>(false);
  const [error, setError] = React.useState<string | null>(null);

  // Switch engine defaults
  const handleSelectEngine = (engine: EngineCard) => {
    setSelectedEngine(engine);
    setTestResult(null);
    setError(null);
    if (engine.id === "sqlite") {
      setHost("");
      setPort("");
      setUsername("");
      setPassword("");
      setDatabase("workspace/sample.db");
    } else {
      setPort(String(engine.defaultPort || 5432));
      if (engine.provider === "supabase") {
        setHost("db.xxxxxxxxxxxx.supabase.co");
        setUsername("postgres");
        setDatabase("postgres");
        setSslMode("require");
      } else if (engine.id === "mysql" || engine.id === "mariadb") {
        setHost("localhost");
        setUsername("root");
        setDatabase("app_db");
        setSslMode("prefer");
      } else {
        setHost("localhost");
        setUsername("postgres");
        setDatabase("postgres");
        setSslMode("prefer");
      }
    }
  };

  const getTestPayload = (): ConnectionTestPayload => {
    return {
      engine: selectedEngine.id,
      database: database.trim(),
      host: selectedEngine.id !== "sqlite" ? host.trim() || undefined : undefined,
      port: selectedEngine.id !== "sqlite" && port ? parseInt(port, 10) : undefined,
      username: selectedEngine.id !== "sqlite" ? username.trim() || undefined : undefined,
      password: selectedEngine.id !== "sqlite" && password ? password : undefined,
      ssl_mode: sslMode,
    };
  };

  const handleTestConnection = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setTestResult(null);
    setTesting(true);

    try {
      const payload = getTestPayload();
      const res = await apiClient.testRawConnection(payload);
      setTestResult(res);
    } catch (err) {
      setTestResult({
        success: false,
        latency_ms: 0,
        engine: selectedEngine.id,
        error_code: "NETWORK_ERROR",
        error_message: err instanceof Error ? err.message : "Diagnostic probe failed.",
      });
    } finally {
      setTesting(false);
    }
  };

  const handleSaveConnection = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!currentWorkspace?.id) {
      setError("Active workspace context required to save connection.");
      return;
    }
    if (!name.trim()) {
      setError("Please provide a connection name.");
      return;
    }
    if (!database.trim()) {
      setError("Please specify target database name.");
      return;
    }

    setSaving(true);
    setError(null);

    const payload: CreateConnectionPayload = {
      name: name.trim(),
      engine: selectedEngine.id,
      provider: selectedEngine.provider,
      database: database.trim(),
      host: selectedEngine.id !== "sqlite" ? host.trim() || undefined : undefined,
      port: selectedEngine.id !== "sqlite" && port ? parseInt(port, 10) : undefined,
      username: selectedEngine.id !== "sqlite" ? username.trim() || undefined : undefined,
      password: selectedEngine.id !== "sqlite" && password ? password : undefined,
      ssl_mode: sslMode,
    };

    try {
      await apiClient.createConnection(currentWorkspace.id, payload);
      router.push("/connections");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to persist database connection.");
      setSaving(false);
    }
  };

  return (
    <div className="space-y-6 max-w-4xl">
      {/* Breadcrumb / Back */}
      <div className="flex items-center gap-2">
        <Link href="/connections">
          <Button variant="ghost" size="sm" className="gap-1 text-xs">
            <ArrowLeft className="w-3.5 h-3.5" />
            Back to Connections
          </Button>
        </Link>
      </div>

      {/* Header */}
      <div className="border-b border-slate-200 dark:border-slate-800 pb-5">
        <h1 className="text-xl font-bold tracking-tight text-slate-900 dark:text-slate-100">
          Add Database Connection
        </h1>
        <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
          Configure an authorized target database for deterministic structural introspection.
        </p>
      </div>

      {/* Step 1: Engine Selection */}
      <div className="space-y-3">
        <label className="text-xs font-semibold text-slate-900 dark:text-slate-100">
          1. Select Supported Database Engine
        </label>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {ENGINES.map((eng) => {
            const isSelected =
              selectedEngine.name === eng.name && selectedEngine.provider === eng.provider;
            return (
              <button
                key={`${eng.name}-${eng.provider}`}
                type="button"
                onClick={() => handleSelectEngine(eng)}
                className={`p-4 rounded-lg border text-left transition-all relative ${
                  isSelected
                    ? "border-blue-600 bg-blue-50/40 dark:bg-blue-950/20 dark:border-blue-500 ring-1 ring-blue-600"
                    : "border-slate-200 dark:border-slate-800 hover:border-slate-300 dark:hover:border-slate-700 bg-white dark:bg-slate-900"
                }`}
                aria-pressed={isSelected}
              >
                <div className="flex items-center justify-between gap-2 mb-1.5">
                  <span className="font-semibold text-sm text-slate-900 dark:text-slate-100 flex items-center gap-1.5">
                    <Database className="w-4 h-4 text-slate-500" />
                    {eng.name}
                  </span>
                  <Badge variant="outline" className="text-[10px]">
                    {eng.badge}
                  </Badge>
                </div>
                <p className="text-xs text-slate-500 dark:text-slate-400">{eng.description}</p>
              </button>
            );
          })}
        </div>
      </div>

      {/* Security Notice */}
      <div className="flex items-start gap-3 p-3.5 rounded-lg border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900/40 text-xs text-slate-600 dark:text-slate-400">
        <ShieldCheck className="w-5 h-5 text-emerald-600 shrink-0 mt-0.5" />
        <div className="space-y-1">
          <strong className="font-medium text-slate-900 dark:text-slate-100">
            Read-Only & Credential Isolation Guarantees
          </strong>
          <p>
            DERA connectors enforce read-only transaction semantics. Passwords are never saved in browser storage or logged. The browser connects exclusively to the DERA API.
          </p>
        </div>
      </div>

      {/* Form Error */}
      {error && (
        <div className="p-3 bg-red-50 text-red-800 border border-red-200 dark:bg-red-950/40 dark:text-red-300 dark:border-red-800 rounded-md text-xs flex items-center gap-2">
          <XCircle className="w-4 h-4 text-red-600 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Step 2: Connection Parameters Form */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm">2. Connection Parameters ({selectedEngine.name})</CardTitle>
          <CardDescription className="text-xs">
            Enter network coordinates and authentication credentials.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form className="space-y-4" onSubmit={handleSaveConnection}>
            {/* Connection Name */}
            <div>
              <label htmlFor="conn-name" className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                Connection Display Name <span className="text-red-500">*</span>
              </label>
              <Input
                id="conn-name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g. Production Analytics Database"
                className="h-9 text-xs"
                required
              />
            </div>

            {/* Network Engines Fields */}
            {selectedEngine.id !== "sqlite" ? (
              <>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                  <div className="sm:col-span-2">
                    <label htmlFor="conn-host" className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                      Host / Server Endpoint <span className="text-red-500">*</span>
                    </label>
                    <Input
                      id="conn-host"
                      value={host}
                      onChange={(e) => setHost(e.target.value)}
                      placeholder="e.g. localhost or postgres.example.com"
                      className="h-9 text-xs font-mono"
                      required
                    />
                  </div>
                  <div>
                    <label htmlFor="conn-port" className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                      Port <span className="text-red-500">*</span>
                    </label>
                    <Input
                      id="conn-port"
                      type="number"
                      value={port}
                      onChange={(e) => setPort(e.target.value)}
                      placeholder="5432"
                      className="h-9 text-xs font-mono"
                      required
                    />
                  </div>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div>
                    <label htmlFor="conn-db" className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                      Target Database Name <span className="text-red-500">*</span>
                    </label>
                    <Input
                      id="conn-db"
                      value={database}
                      onChange={(e) => setDatabase(e.target.value)}
                      placeholder="e.g. postgres, analytics"
                      className="h-9 text-xs font-mono"
                      required
                    />
                  </div>
                  <div>
                    <label htmlFor="conn-user" className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                      Database Username <span className="text-red-500">*</span>
                    </label>
                    <Input
                      id="conn-user"
                      value={username}
                      onChange={(e) => setUsername(e.target.value)}
                      placeholder="e.g. postgres, reader_user"
                      className="h-9 text-xs font-mono"
                      required
                    />
                  </div>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div>
                    <label htmlFor="conn-password" className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                      Password
                    </label>
                    <Input
                      id="conn-password"
                      type="password"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      placeholder="••••••••••••"
                      className="h-9 text-xs font-mono"
                      autoComplete="new-password"
                    />
                  </div>
                  <div>
                    <label htmlFor="conn-ssl" className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                      TLS / SSL Mode
                    </label>
                    <select
                      id="conn-ssl"
                      value={sslMode}
                      onChange={(e) => setSslMode(e.target.value)}
                      className="w-full h-9 px-2 text-xs border border-slate-200 dark:border-slate-800 rounded-md bg-white dark:bg-slate-900 text-slate-700 dark:text-slate-300 focus:outline-none focus:ring-1 focus:ring-slate-900 dark:focus:ring-slate-100"
                    >
                      <option value="prefer">prefer (Default)</option>
                      <option value="require">require (Enforce TLS)</option>
                      <option value="verify-ca">verify-ca (Verify Certificate)</option>
                      <option value="verify-full">verify-full (Verify Hostname)</option>
                      <option value="disable">disable (Plaintext - Insecure)</option>
                    </select>
                  </div>
                </div>
              </>
            ) : (
              /* SQLite Contained Field */
              <div className="space-y-3">
                <div>
                  <label htmlFor="conn-sqlite-path" className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                    Contained SQLite Database Path <span className="text-red-500">*</span>
                  </label>
                  <Input
                    id="conn-sqlite-path"
                    value={database}
                    onChange={(e) => setDatabase(e.target.value)}
                    placeholder="e.g. workspace/chinook.db or :memory:"
                    className="h-9 text-xs font-mono"
                    required
                  />
                  <p className="text-[11px] text-slate-500 mt-1">
                    Path must reside within approved storage roots (e.g. <code>workspace/</code> or <code>demo/</code>). Arbitrary server filesystem paths are rejected.
                  </p>
                </div>
              </div>
            )}

            {/* Test Results Display */}
            {testResult && (
              <div
                className={`p-3 rounded-md text-xs border ${
                  testResult.success
                    ? "bg-emerald-50 text-emerald-800 border-emerald-200 dark:bg-emerald-950/30 dark:text-emerald-300 dark:border-emerald-800"
                    : "bg-red-50 text-red-800 border-red-200 dark:bg-red-950/30 dark:text-red-300 dark:border-red-800"
                }`}
              >
                <div className="flex items-center gap-2">
                  {testResult.success ? (
                    <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                  ) : (
                    <XCircle className="w-4 h-4 text-red-600 shrink-0" />
                  )}
                  <span className="font-medium">
                    {testResult.success
                      ? `Verified in ${testResult.latency_ms}ms${
                          testResult.server_version ? ` — Server: ${testResult.server_version}` : ""
                        }`
                      : `Probe failed [${testResult.error_code || "ERROR"}]: ${testResult.error_message || "Unknown error"}`}
                  </span>
                </div>
              </div>
            )}

            {/* Actions */}
            <div className="flex items-center justify-between pt-4 border-t border-slate-100 dark:border-slate-800">
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={handleTestConnection}
                disabled={testing || saving}
                className="gap-1.5 text-xs"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${testing ? "animate-spin" : ""}`} />
                {testing ? "Probing..." : "Test Diagnostic Probe"}
              </Button>
              <div className="flex items-center gap-2">
                <Link href="/connections">
                  <Button type="button" variant="ghost" size="sm" className="text-xs">
                    Cancel
                  </Button>
                </Link>
                <Button type="submit" size="sm" disabled={saving || testing} className="text-xs">
                  {saving ? "Saving..." : "Save Connection"}
                </Button>
              </div>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
