import { BerthManager } from "@/components/berth-manager";
import { listBerths } from "@/lib/api";
import type { Berth } from "@/lib/types";

export const dynamic = "force-dynamic";

export default async function BerthsPage() {
  let berths: Berth[] = [];
  let error: string | null = null;
  try {
    berths = await listBerths();
  } catch {
    error = "Could not load berths. Is the backend running?";
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold tracking-tight text-slate-900">Berths</h1>
        <p className="mt-1 text-sm text-slate-600">Manage the berths in the port.</p>
      </div>
      {error ? (
        <p role="alert" className="rounded-md border border-red-200 bg-red-50 p-4 text-sm text-red-700">
          {error}
        </p>
      ) : (
        <BerthManager initialBerths={berths} />
      )}
    </div>
  );
}
