"use client";

import * as React from "react";
import { useState } from "react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { useToast } from "@/providers/toast-provider";
import { ShieldCheck, Lock } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";

export default function LoginPage() {
  const router = useRouter();
  const { addToast } = useToast();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);

    try {
      // In Phase 7.1, demonstrates contract-aligned session authentication flow
      // Actual full auth state management and credential submission lands in Phase 7.2
      addToast({
        type: "info",
        title: "Phase 7.1 Preview",
        description: "Redirecting to workspace overview. Full multi-tenant authentication UI will be implemented in Phase 7.2.",
      });

      setTimeout(() => {
        router.push("/app/overview");
      }, 800);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50 dark:bg-slate-950 p-4">
      <Card className="w-full max-w-md shadow-lg border-slate-200 dark:border-slate-800">
        <CardHeader className="space-y-1 text-center">
          <div className="mx-auto flex h-10 w-10 items-center justify-center rounded bg-blue-600 text-white font-bold text-sm shadow-sm mb-2">
            D
          </div>
          <CardTitle className="text-xl font-bold tracking-tight">
            DERA Studio
          </CardTitle>
          <CardDescription>
            Database Engineering & Reverse Analysis
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                Work Email
              </label>
              <Input
                type="email"
                required
                placeholder="engineer@enterprise.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </div>
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                Password
              </label>
              <Input
                type="password"
                required
                placeholder="••••••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </div>
            <Button type="submit" className="w-full" isLoading={isLoading}>
              <Lock className="w-4 h-4 mr-1.5" /> Sign In to Studio
            </Button>
          </form>
        </CardContent>
        <CardFooter className="flex flex-col gap-2 text-center text-xs text-slate-500">
          <div className="flex items-center justify-center gap-1.5 text-emerald-600 dark:text-emerald-400 font-medium">
            <ShieldCheck className="w-4 h-4" /> Secure Cookie Session Authentication
          </div>
          <p className="text-[10px]">
            Zero credentials stored in browser localStorage.
          </p>
        </CardFooter>
      </Card>
    </div>
  );
}
