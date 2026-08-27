"use client";

import { useMemo, useState } from "react";

import { Button } from "@/components/ui/button";
import { generatePlan } from "@/lib/api";
import { formatDateTime } from "@/lib/datetime";
import type { Berth, Plan, Ship } from "@/lib/types";
import { GanttChart } from "./gantt-chart";
import { UnassignedPanel } from "./unassigned-panel";

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white px-4 py-3">
      <div className="text-xs text-slate-500">{label}</div>
      <div className="mt-0.5 text-lg font-semibold tabular-nums text-slate-900">
        {value}
      </div>
    </div>
  );
}

export function PlanWorkspace({
  initialPlans,
  ships,
  berths,
}: {
  initialPlans: Plan[];
  ships: Ship[];
  berths: Berth[];
}) {
  const [plans, setPlans] = useState<Plan[]>(initialPlans);
  const [selectedId, setSelectedId] = useState<number | null>(
    initialPlans[0]?.id ?? null,
  );
  const [buffer, setBuffer] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const shipsById = useMemo(() => new Map(ships.map((s) => [s.id, s])), [ships]);
  const selected = plans.find((p) => p.id === selectedId) ?? null;

  const noData = ships.length === 0 || berths.length === 0;

  async function generate() {
    setBusy(true);
    setError(null);
    try {
      const created = await generatePlan(buffer ? Number(buffer) : undefined);
      setPlans((prev) => [created, ...prev]);
      setSelectedId(created.id);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not generate plan");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-6">
      {/* controls */}
      <div className="flex flex-wrap items-end gap-4 rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
        <label className="flex flex-col gap-1.5 text-sm">
          <span className="font-medium text-slate-600">Manoeuvring buffer (min)</span>
          <input
            type="number"
            min="1"
            max="1440"
            step="1"
            placeholder="60"
            value={buffer}
            onChange={(e) => setBuffer(e.target.value)}
            className="w-32 rounded-md border border-slate-300 px-3 py-2 outline-none focus:border-teal-600 focus:ring-2 focus:ring-teal-100"
          />
        </label>
        <Button onClick={generate} disabled={busy || noData}>
          {busy ? "Generating…" : "Generate plan"}
        </Button>
        <span className="text-xs text-slate-500">
          Leave blank to use the default of 60 min.
        </span>
        {noData && (
          <p className="w-full text-sm text-amber-700">
            Add at least one ship and one berth before generating a plan.
          </p>
        )}
        {error && (
          <p role="alert" className="w-full text-sm text-red-600">
            {error}
          </p>
        )}
      </div>

      {plans.length === 0 ? (
        <p className="rounded-lg border border-dashed border-slate-300 p-8 text-center text-sm text-slate-500">
          No plan generated yet. Use "Generate plan" above to create the first one.
        </p>
      ) : (
        <>
          {/* history + summary */}
          <div className="flex flex-wrap items-center justify-between gap-3">
            <label className="flex items-center gap-2 text-sm text-slate-600">
              Plan history
              <select
                value={selectedId ?? ""}
                onChange={(e) => setSelectedId(Number(e.target.value))}
                className="rounded-md border border-slate-300 bg-white px-3 py-1.5 text-sm outline-none focus:border-teal-600"
              >
                {plans.map((p) => (
                  <option key={p.id} value={p.id}>
                    Plan #{p.id} — {formatDateTime(p.created_at)}
                  </option>
                ))}
              </select>
            </label>
          </div>

          {selected && (
            <>
              <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
                <Stat label="Assigned ships" value={String(selected.assignments.length)} />
                <Stat label="Unassigned" value={String(selected.unassigned_entries.length)} />
                <Stat label="Total waiting" value={`${selected.total_waiting_min} min`} />
                <Stat label="Buffer used" value={`${selected.buffer_min} min`} />
              </div>

              <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
                <h2 className="mb-4 text-sm font-semibold text-slate-900">
                  Berthing plan
                </h2>
                <GanttChart plan={selected} berths={berths} shipsById={shipsById} />
              </section>

              <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
                <h2 className="mb-3 text-sm font-semibold text-slate-900">
                  Unassigned ships
                </h2>
                <UnassignedPanel
                  entries={selected.unassigned_entries}
                  shipsById={shipsById}
                />
              </section>
            </>
          )}
        </>
      )}
    </div>
  );
}
