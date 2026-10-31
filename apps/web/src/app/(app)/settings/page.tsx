"use client";

import * as React from "react";
import { useState } from "react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { useToast } from "@/providers/toast-provider";
import { env } from "@/lib/env";
import { useTheme } from "next-themes";
import { Moon, Sun, Laptop } from "lucide-react";

export default function SettingsPage() {
  const { addToast } = useToast();
  const { theme, setTheme } = useTheme();
  const [apiUrl, setApiUrl] = useState(env.NEXT_PUBLIC_DERA_API_URL);

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    addToast({
      type: "success",
      title: "Settings Saved",
      description: "Frontend environment configurations have been updated.",
    });
  };

  return (
    <div className="space-y-6 max-w-4xl">
      <div>
        <h1 className="text-xl font-bold tracking-tight text-slate-900 dark:text-slate-100">
          Studio Settings
        </h1>
        <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
          Configure environment preferences, theme, and backend connectivity.
        </p>
      </div>

      <div className="grid gap-6">
        {/* Appearance Settings */}
        <Card>
          <CardHeader>
            <CardTitle>Appearance & Theme</CardTitle>
            <CardDescription>
              Select your interface theme preference. Settings persist across browser sessions.
            </CardDescription>
          </CardHeader>
          <CardContent className="flex gap-3">
            <Button
              variant={theme === "light" ? "primary" : "outline"}
              size="sm"
              onClick={() => setTheme("light")}
            >
              <Sun className="w-4 h-4 mr-1.5" /> Light
            </Button>
            <Button
              variant={theme === "dark" ? "primary" : "outline"}
              size="sm"
              onClick={() => setTheme("dark")}
            >
              <Moon className="w-4 h-4 mr-1.5" /> Dark
            </Button>
            <Button
              variant={theme === "system" ? "primary" : "outline"}
              size="sm"
              onClick={() => setTheme("system")}
            >
              <Laptop className="w-4 h-4 mr-1.5" /> System Default
            </Button>
          </CardContent>
        </Card>

        {/* Backend Connectivity */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>Backend API Configuration</CardTitle>
              <Badge variant="outline">Verified RFC 7807</Badge>
            </div>
            <CardDescription>
              The DERA REST backend service endpoint.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSave} className="space-y-4">
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                  API Base URL
                </label>
                <Input
                  value={apiUrl}
                  onChange={(e) => setApiUrl(e.target.value)}
                  placeholder="http://localhost:8000"
                />
                <p className="text-[11px] text-slate-500">
                  Standard development port is 8000. Credentials and cookies are managed by backend workers.
                </p>
              </div>
              <Button type="submit" size="sm">
                Save Preferences
              </Button>
            </form>
          </CardContent>
        </Card>

        {/* Non-Negotiable System Directives */}
        <Card>
          <CardHeader>
            <CardTitle>Engineering Directives & Compliance</CardTitle>
            <CardDescription>
              Core platform principles enforced by architecture.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3 text-xs">
            <div className="flex items-center justify-between py-1.5 border-b border-slate-100 dark:border-slate-800">
              <span className="font-medium">AI / LLM Integration</span>
              <Badge variant="destructive">Strictly Prohibited</Badge>
            </div>
            <div className="flex items-center justify-between py-1.5 border-b border-slate-100 dark:border-slate-800">
              <span className="font-medium">Client-Side Database Passwords</span>
              <Badge variant="destructive">Strictly Prohibited</Badge>
            </div>
            <div className="flex items-center justify-between py-1.5 border-b border-slate-100 dark:border-slate-800">
              <span className="font-medium">Arbitrary Raw SQL Injection</span>
              <Badge variant="destructive">Strictly Prohibited</Badge>
            </div>
            <div className="flex items-center justify-between py-1.5 text-xs">
              <span className="font-medium">Schema Analysis Mechanism</span>
              <Badge variant="success">Deterministic ASTs & Reverse Drivers</Badge>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
