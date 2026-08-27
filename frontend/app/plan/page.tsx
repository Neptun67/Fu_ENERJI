import { PlanWorkspace } from "@/components/plan/plan-workspace";
import { listBerths, listPlans, listShips } from "@/lib/api";
import type { Berth, Plan, Ship } from "@/lib/types";

export const dynamic = "force-dynamic";

export default async function PlanPage() {
  let ships: Ship[] = [];
  let berths: Berth[] = [];
  let plans: Plan[] = [];
  let error: string | null = null;
  try {
    [ships, berths, plans] = await Promise.all([
      listShips(),
      listBerths(),
      listPlans(),
    ]);
  } catch {
    error = "Veriler yüklenemedi. Backend çalışıyor mu?";
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold tracking-tight text-slate-900">Plan</h1>
        <p className="mt-1 text-sm text-slate-600">
          Kurallara uygun yanaşma planını üretin ve zaman çizelgesinde görün.
        </p>
      </div>
      {error ? (
        <p role="alert" className="rounded-md border border-red-200 bg-red-50 p-4 text-sm text-red-700">
          {error}
        </p>
      ) : (
        <PlanWorkspace initialPlans={plans} ships={ships} berths={berths} />
      )}
    </div>
  );
}
