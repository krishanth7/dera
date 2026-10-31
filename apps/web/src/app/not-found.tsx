import Link from "next/link";
import { Button } from "@/components/ui/button";
import { FileQuestion } from "lucide-react";

export default function NotFound() {
  return (
    <div className="flex min-h-[70vh] flex-col items-center justify-center p-6 text-center">
      <div className="flex h-12 w-12 items-center justify-center rounded-full bg-slate-100 dark:bg-slate-800 text-slate-500 mb-4">
        <FileQuestion className="h-6 w-6" />
      </div>
      <h2 className="text-xl font-bold text-slate-900 dark:text-slate-100">
        Page Not Found
      </h2>
      <p className="mt-2 text-xs text-slate-500 dark:text-slate-400 max-w-sm">
        The requested studio route does not exist or has not been provisioned in Phase 7.1.
      </p>
      <div className="mt-6">
        <Link href="/app/overview">
          <Button size="sm">Return to Studio Overview</Button>
        </Link>
      </div>
    </div>
  );
}
