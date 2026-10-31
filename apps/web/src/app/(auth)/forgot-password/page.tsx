import * as React from "react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Info, ArrowLeft } from "lucide-react";
import Link from "next/link";

export default function ForgotPasswordPage() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50 dark:bg-slate-950 p-4">
      <Card className="w-full max-w-md shadow-lg border-slate-200 dark:border-slate-800">
        <CardHeader className="space-y-1 text-center">
          <div className="mx-auto flex h-10 w-10 items-center justify-center rounded bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 mb-2">
            <Info className="w-5 h-5" />
          </div>
          <CardTitle className="text-xl font-bold tracking-tight">
            Account Recovery Notice
          </CardTitle>
          <CardDescription>
            Self-Hosted & Enterprise Identity Governance
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3 text-xs text-slate-600 dark:text-slate-300">
          <p>
            In Phase 7.2 of DERA, self-service password reset tokens via email are disabled to protect enterprise deployment boundaries and prevent email enumeration.
          </p>
          <p>
            To reset your credentials, please contact your workspace <strong>Owner</strong> or <strong>System Administrator</strong>, or use the administrative command-line utilities.
          </p>
        </CardContent>
        <CardFooter className="flex justify-center">
          <Link href="/login">
            <Button variant="outline" size="sm">
              <ArrowLeft className="w-4 h-4 mr-1.5" /> Return to Sign In
            </Button>
          </Link>
        </CardFooter>
      </Card>
    </div>
  );
}
