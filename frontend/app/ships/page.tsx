import { ShipManager } from "@/components/ship-manager";
import { listShips } from "@/lib/api";
import type { Ship } from "@/lib/types";

export const dynamic = "force-dynamic";

export default async function ShipsPage() {
  let ships: Ship[] = [];
  let error: string | null = null;
  try {
    ships = await listShips();
  } catch {
    error = "Could not load ships. Is the backend running?";
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold tracking-tight text-slate-900">Ships</h1>
        <p className="mt-1 text-sm text-slate-600">Manage the ships arriving at the port.</p>
      </div>
      {error ? (
        <p role="alert" className="rounded-md border border-red-200 bg-red-50 p-4 text-sm text-red-700">
          {error}
        </p>
      ) : (
        <ShipManager initialShips={ships} />
      )}
    </div>
  );
}
