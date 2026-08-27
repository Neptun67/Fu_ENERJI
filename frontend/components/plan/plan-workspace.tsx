"use client";

import { useMemo, useState } from "react";

import { Button } from "@/components/ui/button";
import { Field } from "@/components/ui/field";
import { generatePlan } from "@/lib/api";
import { formatDateTime } from "@/lib/datetime";
import type { Berth, Plan, Ship } from "@/lib/types";
import { GanttChart } from "./gantt-chart";
import { UnassignedPanel } from "./unassigned-panel";

/*
  Stat tile. `tone` is not decoration: "primary" marks the objective metric the
  plan is optimised for, and "warn" fires only when something needs attention.
  Everything else stays neutral so the two that matter can be found at a glance.
*/
function Stat({
  label,
  value,
  sub,
  tone = "neutral",
}: {
  label: string;
  value: string;
  sub?: string;
  tone?: "neutral" | "primary" | "warn";
}) {
  const tones = {
    neutral: "border-slate-200 bg-white",
    primary: "border-sea-200 bg-sea-50",
    warn: "border-amber-200 bg-amber-50",
  } as const;
  const values = {
    neutral: "text-slate-900",
    primary: "text-sea-900",
    warn: "text-amber-900",
  } as const;
  return (
    <div className={`rounded-xl border px-4 py-3 ${tones[tone]}`}>
      <div className="text-xs font-medium text-slate-600">{label}</div>
      <div className={`mt-1 text-2xl font-semibold tabular-nums ${values[tone]}`}>
        {value}
      </div>
      {sub && <div className="mt-0.5 text-xs text-slate-500">{sub}</div>}
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

  const total = ships.length;
  const unassignedCount = selected?.unassigned_entries.length ?? 0;

  return (
    <div className="space-y-6">
      <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
        <div className="flex flex-wrap items-end gap-4">
          <div className="w-40">
            <Field
              label="Manoeuvring buffer"
              type="number"
              min="1"
              max="1440"
              step="1"
              suffix="min"
              placeholder="60"
              value={buffer}
              onChange={setBuffer}
              hint="Blank uses 60"
            />
          </div>
          <Button onClick={generate} disabled={busy || noData} className="mb-6">
            {busy ? "Generating..." : "Generate plan"}
          </Button>
        </div>

        {noData && (
          <p className="mt-2 rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-900">
            Add at least one ship and one berth before generating a plan.
          </p>
        )}
        {error && (
          <p
            role="alert"
            className="mt-2 rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-800"
          >
            {error}
          </p>
        )}
      </div>

      {plans.length === 0 ? (
        <div className="rounded-xl border border-dashed border-slate-300 bg-white/60 px-6 py-14 text-center">
          <p className="text-sm font-medium text-slate-700">No plan yet</p>
          <p className="mx-auto mt-1 max-w-sm text-sm text-slate-500">
            Generate one above. Each plan is saved, so you can come back and compare it with
            later runs.
          </p>
        </div>
      ) : (
        <>
          <div className="flex flex-wrap items-center gap-2">
            <label htmlFor="plan-history" className="text-sm font-medium text-slate-700">
              Plan
            </label>
            <select
              id="plan-history"
              value={selectedId ?? ""}
              onChange={(e) => setSelectedId(Number(e.target.value))}
              className="rounded-md border border-slate-300 bg-white px-3 py-1.5 text-sm text-slate-900 shadow-sm outline-none focus:border-sea-600 focus:ring-2 focus:ring-sea-100"
            >
              {plans.map((p) => (
                <option key={p.id} value={p.id}>
                  #{p.id} - {formatDateTime(p.created_at)}
                </option>
              ))}
            </select>
            <span className="text-xs text-slate-500">
              {plans.length} {plans.length === 1 ? "run" : "runs"} saved
            </span>
          </div>

          {selected && (
            <>
              <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
                <Stat
                  label="Total waiting"
                  value={`${selected.total_waiting_min} min`}
                  sub="The metric the plan minimises"
                  tone="primary"
                />
                <Stat
                  label="Berthed"
                  value={String(selected.assignments.length)}
                  sub={`of ${total} ${total === 1 ? "ship" : "ships"}`}
                />
                <Stat
                  label="Unassigned"
                  value={String(unassignedCount)}
                  sub={unassignedCount > 0 ? "See reasons below" : "All ships placed"}
                  tone={unassignedCount > 0 ? "warn" : "neutral"}
                />
                <Stat label="Buffer used" value={`${selected.buffer_min} min`} />
              </div>

              <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
                <h2 className="mb-1 text-sm font-semibold text-sea-900">Berthing plan</h2>
                <p className="mb-4 text-xs text-slate-500">
                  Each row is a berth. Bars are assignments; the grey tail after a bar is the
                  manoeuvring buffer.
                </p>
                <GanttChart plan={selected} berths={berths} shipsById={shipsById} />
              </section>

              <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
                <div className="mb-3 flex items-center gap-2">
                  <h2 className="text-sm font-semibold text-sea-900">Unassigned ships</h2>
                  {unassignedCount > 0 && (
                    <span className="rounded-full bg-amber-100 px-2 py-0.5 text-xs font-semibold text-amber-900">
                      {unassignedCount}
                    </span>
                  )}
                </div>
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
