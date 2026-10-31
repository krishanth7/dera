"use client";

import * as React from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import {
  ArrowLeft,
  CheckCircle2,
  Clock,
  Database,
  ExternalLink,
  Layers,
  Pencil,
  RefreshCw,
  Server,
  ShieldCheck,
  Trash2,
  XCircle,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { ErrorState } from "@/components/ui/error-state";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import { useWorkspace } from "@/providers/workspace-provider";
import {
  apiClient,
  ConnectionItem,
  ConnectionTestResult,
  DeraApiError,
  UpdateConnectionPayload,
} from "@/lib/api-client";

export default function ConnectionDetailPage() {
  const params = useParams<{ connectionId: string }>();
  const router = useRouter();
  const { currentWorkspace } = useWorkspace();
  const connectionId = params.connectionId;

  const [connection, setConnection] = React.useState<ConnectionItem | null>(null);
  const [loading, setLoading] = React.useState<boolean>(true);
  const [error, setError] = React.useState<string | null>(null);

  // Testing & Inspection
  const [testing, setTesting] = React.useState<boolean>(false);
  const [testResult, setTestResult] = React.useState<ConnectionTestResult | null>(null);
  const [inspecting, setInspecting] = React.useState<boolean>(false);

  // Edit Modal State
  const [editOpen, setEditOpen] = React.useState<boolean>(false);
  const [editName, setEditName] = React.useState<string>("");
  const [editDatabase, setEditDatabase] = React.useState<string>("");
  const [editHost, setEditHost] = React.useState<string>("");
  const [editPort, setEditPort] = React.useState<string>("");
  const [editUsername, setEditUsername] = React.useState<string>("");
  const [editPassword, setEditPassword] = React.useState<string>("");
  const [editSslMode, setEditSslMode] = React.useState<string>("prefer");
  const [editSaving, setEditSaving] = React.useState<boolean>(false);

  // Delete Modal State
  const [deleteOpen, setDeleteOpen] = React.useState<boolean>(false);
  const [deleting, setDeleting] = React.useState<boolean>(false);

  const loadConnection = React.useCallback(async () => {
    if (!currentWorkspace?.id || !connectionId) return;
    setLoading(true);
    setError(null);
    try {
      const data = await apiClient.getConnection(currentWorkspace.id, connectionId);
      setConnection(data);
      setEditName(data.name);
      setEditDatabase(data.database);
      setEditHost(data.host || "");
      setEditPort(data.port ? String(data.port) : "");
      setEditUsername(data.username || "");
      setEditSslMode(data.ssl_mode || "prefer");
    } catch (err) {
      if (err instanceof DeraApiError) {
        setError(err.problem.detail || err.message);
      } else {
        setError("Failed to load connection details.");
      }
    } finally {
      setLoading(false);
    }
  }, [currentWorkspace?.id, connectionId]);

  React.useEffect(() => {
    loadConnection();
  }, [loadConnection]);

  const handleTest = async () => {
    if (!currentWorkspace?.id || !connection) return;
    setTesting(true);
    setTestResult(null);
    try {
      const res = await apiClient.testConnection(currentWorkspace.id, connection.id);
      setTestResult(res);
      await loadConnection();
    } catch (err) {
      setTestResult({
        success: false,
        latency_ms: 0,
        engine: connection.engine,
        error_code: "TEST_FAILED",
        error_message: err instanceof Error ? err.message : "Test failed",
      });
    } finally {
      setTesting(false);
    }
  };

  const handleInspect = async () => {
    if (!currentWorkspace?.id || !connection) return;
    setInspecting(true);
    try {
      const summary = await apiClient.inspectConnection(currentWorkspace.id, connection.id);
      router.push(`/schemas/${summary.schema_id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Inspection failed.");
      setInspecting(false);
    }
  };

  const handleEditSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!currentWorkspace?.id || !connection) return;
    setEditSaving(true);
    try {
      const payload: UpdateConnectionPayload = {
        name: editName.trim(),
        database: editDatabase.trim(),
        host: editHost.trim() || undefined,
        port: editPort ? parseInt(editPort, 10) : undefined,
        username: editUsername.trim() || undefined,
        password: editPassword ? editPassword : undefined,
        ssl_mode: editSslMode,
      };
      await apiClient.updateConnection(currentWorkspace.id, connection.id, payload);
      setEditOpen(false);
      setEditPassword("");
      await loadConnection();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update connection.");
    } finally {
      setEditSaving(false);
    }
  };

  const handleDelete = async () => {
    if (!currentWorkspace?.id || !connection) return;
    setDeleting(true);
    try {
      await apiClient.deleteConnection(currentWorkspace.id, connection.id);
      router.push("/connections");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete connection.");
      setDeleting(false);
    }
  };

  if (loading) {
    return (
      <div className="space-y-6 max-w-4xl">
        <Skeleton className="h-6 w-32" />
        <Skeleton className="h-40 w-full" />
      </div>
    );
  }

  if (error || !connection) {
    return (
      <div className="space-y-6 max-w-4xl">
        <Link href="/connections">
          <Button variant="ghost" size="sm" className="gap-1 text-xs">
            <ArrowLeft className="w-3.5 h-3.5" />
            Back to Connections
          </Button>
        </Link>
        <ErrorState
          title="Connection Not Found"
          description={error || "Could not retrieve the requested database connection."}
          onRetry={loadConnection}
        />
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-4xl">
      {/* Top Navigation */}
      <div className="flex items-center justify-between">
        <Link href="/connections">
          <Button variant="ghost" size="sm" className="gap-1 text-xs">
            <ArrowLeft className="w-3.5 h-3.5" />
            Back to Connections
          </Button>
        </Link>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={handleTest}
            disabled={testing || inspecting}
            className="gap-1.5 text-xs"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${testing ? "animate-spin" : ""}`} />
            {testing ? "Probing..." : "Test Diagnostic Probe"}
          </Button>
          <Button
            size="sm"
            onClick={handleInspect}
            disabled={testing || inspecting}
            className="gap-1.5 text-xs"
          >
            <Layers className={`w-3.5 h-3.5 ${inspecting ? "animate-spin" : ""}`} />
            {inspecting ? "Extracting..." : "Inspect Schema"}
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setEditOpen(true)}
            className="gap-1.5 text-xs"
          >
            <Pencil className="w-3.5 h-3.5" />
            Edit
          </Button>
          <Button
            variant="destructive"
            size="sm"
            onClick={() => setDeleteOpen(true)}
            className="gap-1.5 text-xs"
          >
            <Trash2 className="w-3.5 h-3.5" />
            Delete
          </Button>
        </div>
      </div>

      {/* Header Info */}
      <div className="border-b border-slate-200 dark:border-slate-800 pb-5">
        <div className="flex items-center gap-3">
          <h1 className="text-xl font-bold tracking-tight text-slate-900 dark:text-slate-100">
            {connection.name}
          </h1>
          <Badge variant="outline" className="uppercase font-mono text-[10px]">
            {connection.engine}
          </Badge>
          <Badge
            variant={
              connection.status === "connected"
                ? "success"
                : connection.status === "failed"
                ? "destructive"
                : "secondary"
            }
          >
            {connection.status}
          </Badge>
        </div>
        <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
          Connection ID: <code className="font-mono text-[11px]">{connection.id}</code>
        </p>
      </div>

      {/* Diagnostic Probe Result Banner */}
      {testResult && (
        <div
          className={`p-3.5 rounded-md text-xs border ${
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
                ? `Diagnostic probe verified in ${testResult.latency_ms}ms${
                    testResult.server_version ? ` — Server: ${testResult.server_version}` : ""
                  }`
                : `Diagnostic probe failed [${testResult.error_code || "ERROR"}]: ${
                    testResult.error_message || "Unknown error"
                  }`}
            </span>
          </div>
        </div>
      )}

      {/* Connection Coordinates Card */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Connection Configuration & Boundaries</CardTitle>
          <CardDescription className="text-xs">
            Sanitized network parameters and credential isolation status.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <dl className="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-4 text-xs">
            <div>
              <dt className="text-slate-500 font-medium">Database Engine</dt>
              <dd className="mt-1 font-semibold text-slate-900 dark:text-slate-100 uppercase">
                {connection.engine}
              </dd>
            </div>
            <div>
              <dt className="text-slate-500 font-medium">Cloud Distribution</dt>
              <dd className="mt-1 font-semibold text-slate-900 dark:text-slate-100">
                {connection.provider}
              </dd>
            </div>
            <div>
              <dt className="text-slate-500 font-medium">Target Database / Catalog</dt>
              <dd className="mt-1 font-mono text-slate-900 dark:text-slate-100">
                {connection.database}
              </dd>
            </div>
            {connection.host && (
              <div>
                <dt className="text-slate-500 font-medium">Network Host & Port</dt>
                <dd className="mt-1 font-mono text-slate-900 dark:text-slate-100">
                  {connection.host}:{connection.port || "default"}
                </dd>
              </div>
            )}
            {connection.username && (
              <div>
                <dt className="text-slate-500 font-medium">Database Username</dt>
                <dd className="mt-1 font-mono text-slate-900 dark:text-slate-100">
                  {connection.username}
                </dd>
              </div>
            )}
            <div>
              <dt className="text-slate-500 font-medium">Transport Security (TLS)</dt>
              <dd className="mt-1 text-slate-900 dark:text-slate-100">{connection.ssl_mode}</dd>
            </div>
            <div>
              <dt className="text-slate-500 font-medium">Credential Vault Status</dt>
              <dd className="mt-1 flex items-center gap-1.5 text-emerald-600 dark:text-emerald-400 font-medium">
                <ShieldCheck className="w-3.5 h-3.5" />
                {connection.has_password ? "Password Stored in Vault" : "No Password Set"}
              </dd>
            </div>
            <div>
              <dt className="text-slate-500 font-medium">Last Metadata Inspection</dt>
              <dd className="mt-1 text-slate-900 dark:text-slate-100">
                {connection.last_inspected_at
                  ? new Date(connection.last_inspected_at).toLocaleString()
                  : "Never Inspected"}
              </dd>
            </div>
          </dl>
        </CardContent>
      </Card>

      {/* Edit Connection Dialog */}
      <Dialog open={editOpen} onOpenChange={setEditOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Edit Database Connection</DialogTitle>
            <DialogDescription>
              Update connection parameters for {connection.name}.
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={handleEditSubmit} className="space-y-3">
            <div>
              <label htmlFor="edit-name" className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                Display Name
              </label>
              <Input
                id="edit-name"
                value={editName}
                onChange={(e) => setEditName(e.target.value)}
                className="h-9 text-xs"
                required
              />
            </div>
            {connection.engine !== "sqlite" && (
              <>
                <div className="grid grid-cols-3 gap-2">
                  <div className="col-span-2">
                    <label htmlFor="edit-host" className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                      Host
                    </label>
                    <Input
                      id="edit-host"
                      value={editHost}
                      onChange={(e) => setEditHost(e.target.value)}
                      className="h-9 text-xs font-mono"
                    />
                  </div>
                  <div>
                    <label htmlFor="edit-port" className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                      Port
                    </label>
                    <Input
                      id="edit-port"
                      value={editPort}
                      onChange={(e) => setEditPort(e.target.value)}
                      className="h-9 text-xs font-mono"
                    />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <label htmlFor="edit-db" className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                      Database
                    </label>
                    <Input
                      id="edit-db"
                      value={editDatabase}
                      onChange={(e) => setEditDatabase(e.target.value)}
                      className="h-9 text-xs font-mono"
                      required
                    />
                  </div>
                  <div>
                    <label htmlFor="edit-user" className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                      Username
                    </label>
                    <Input
                      id="edit-user"
                      value={editUsername}
                      onChange={(e) => setEditUsername(e.target.value)}
                      className="h-9 text-xs font-mono"
                    />
                  </div>
                </div>
                <div>
                  <label htmlFor="edit-pass" className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                    New Password (leave blank to retain current)
                  </label>
                  <Input
                    id="edit-pass"
                    type="password"
                    value={editPassword}
                    onChange={(e) => setEditPassword(e.target.value)}
                    placeholder="••••••••"
                    className="h-9 text-xs font-mono"
                  />
                </div>
              </>
            )}
            <DialogFooter className="pt-2">
              <Button type="button" variant="outline" size="sm" onClick={() => setEditOpen(false)}>
                Cancel
              </Button>
              <Button type="submit" size="sm" disabled={editSaving}>
                {editSaving ? "Saving..." : "Save Changes"}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteOpen} onOpenChange={setDeleteOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete Connection</DialogTitle>
            <DialogDescription>
              Are you sure you want to delete &ldquo;{connection.name}&rdquo;?
              This operation cannot be undone. Target database data will remain untouched.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setDeleteOpen(false)}
              disabled={deleting}
            >
              Cancel
            </Button>
            <Button
              variant="destructive"
              size="sm"
              onClick={handleDelete}
              disabled={deleting}
            >
              {deleting ? "Deleting..." : "Confirm Deletion"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
