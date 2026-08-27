import { formatTime, toMillis } from "@/lib/datetime";
import type { Berth, Plan, Ship } from "@/lib/types";

const TICKS = 6;
const MINUTE = 60_000;

function Gridlines({ lefts }: { lefts: number[] }) {
  return (
    <>
      {lefts.map((left, i) => (
        <div
          key={i}
          aria-hidden="true"
          className="absolute bottom-0 top-0 w-px bg-slate-100"
          style={{ left: `${left}%` }}
        />
      ))}
    </>
  );
}

/*
  Timeline of the plan: one row per berth, time on the horizontal axis.

  Three things are drawn per assignment, in increasing visual weight:
    - waiting   (ETA -> start)  a hatched lane, because this is the cost the plan
                                is trying to minimise and it is otherwise invisible
    - assignment(start -> end)  the solid bar
    - buffer    (end -> +buffer) a grey tail, the manoeuvre before the next ship

  The assignment is the only saturated element, so a berth's occupancy reads first
  and the supporting information stays legible without competing.
*/
export function GanttChart({
  plan,
  berths,
  shipsById,
}: {
  plan: Plan;
  berths: Berth[];
  shipsById: Map<number, Ship>;
}) {
  if (plan.assignments.length === 0) {
    return (
      <p className="rounded-lg border border-dashed border-slate-300 px-6 py-10 text-center text-sm text-slate-500">
        No ships were assigned in this plan. The unassigned ones are listed below with their
        reasons.
      </p>
    );
  }

  const bufferMs = plan.buffer_min * MINUTE;
  // The domain must cover the waiting lanes too, or they would be clipped at the left.
  const starts = plan.assignments.map((a) => toMillis(a.start_time) - a.waiting_min * MINUTE);
  const ends = plan.assignments.map((a) => toMillis(a.end_time) + bufferMs);
  let t0 = Math.min(...starts);
  let t1 = Math.max(...ends);
  const pad = Math.max((t1 - t0) * 0.04, 10 * MINUTE);
  t0 -= pad;
  t1 += pad;
  const span = t1 - t0 || 1;
  const pct = (ms: number) => ((ms - t0) / span) * 100;

  const ticks = Array.from({ length: TICKS }, (_, i) => {
    const left = (i / (TICKS - 1)) * 100;
    const ms = t0 + (span * i) / (TICKS - 1);
    return { left, label: formatTime(new Date(ms).toISOString()) };
  });
  const tickLefts = ticks.map((t) => t.left);

  const byBerth = new Map<number, typeof plan.assignments>();
  for (const b of berths) byBerth.set(b.id, []);
  for (const a of plan.assignments) {
    if (!byBerth.has(a.berth_id)) byBerth.set(a.berth_id, []);
    byBerth.get(a.berth_id)!.push(a);
  }
  const rows = [...berths].sort((a, b) => a.id - b.id);

  return (
    <div>
      <div className="min-w-[36rem]">
        {/* Time axis */}
        <div className="flex">
          <div className="w-36 shrink-0" />
          <div className="relative h-6 flex-1">
            {ticks.map((t, i) => (
              <span
                key={i}
                className="absolute -translate-x-1/2 whitespace-nowrap text-[11px] tabular-nums text-slate-500"
                style={{ left: `${t.left}%` }}
              >
                {t.label}
              </span>
            ))}
          </div>
        </div>

        <div className="border-t border-slate-200">
          {rows.map((berth) => {
            const items = byBerth.get(berth.id) ?? [];
            return (
              <div
                key={berth.id}
                className="flex items-stretch border-b border-slate-100 last:border-0"
              >
                <div className="flex w-36 shrink-0 flex-col justify-center px-3 py-2">
                  <span className="truncate text-sm font-medium text-slate-800">
                    {berth.name}
                  </span>
                  <span className="text-[11px] tabular-nums text-slate-500">
                    {berth.length_m} m / {berth.depth_m} m
                  </span>
                </div>
                <div className="relative h-14 flex-1">
                  <Gridlines lefts={tickLefts} />

                  {items.length === 0 && (
                    <span className="absolute inset-y-0 left-2 flex items-center text-[11px] italic text-slate-400">
                      idle
                    </span>
                  )}

                  {items.map((a) => {
                    const start = toMillis(a.start_time);
                    const end = toMillis(a.end_time);
                    const eta = start - a.waiting_min * MINUTE;
                    const shipName = shipsById.get(a.ship_id)?.name ?? `#${a.ship_id}`;
                    const left = pct(start);
                    const width = Math.max(pct(end) - left, 0.6);
                    const bufWidth = pct(end + bufferMs) - pct(end);
                    const waitWidth = pct(start) - pct(eta);
                    const label = `${shipName}: berthed ${formatTime(a.start_time)} to ${formatTime(a.end_time)} UTC, waited ${a.waiting_min} minutes`;

                    return (
                      <div key={a.id}>
                        {a.waiting_min > 0 && (
                          <div
                            aria-hidden="true"
                            title={`${shipName} waited ${a.waiting_min} min at anchor`}
                            className="absolute bottom-3.5 top-3.5 rounded-l border border-r-0 border-amber-300/70"
                            style={{
                              left: `${pct(eta)}%`,
                              width: `${waitWidth}%`,
                              backgroundImage:
                                "repeating-linear-gradient(45deg, rgba(217,119,6,0.16) 0 4px, transparent 4px 8px)",
                            }}
                          />
                        )}

                        <div
                          aria-hidden="true"
                          title={`Manoeuvring buffer: ${plan.buffer_min} min`}
                          className="absolute bottom-4 top-4 rounded-r bg-slate-200"
                          style={{ left: `${pct(end)}%`, width: `${bufWidth}%` }}
                        />

                        <div
                          role="img"
                          aria-label={label}
                          title={label}
                          className="absolute bottom-3 top-3 flex items-center overflow-hidden rounded-md bg-sea-600 shadow-sm ring-1 ring-sea-700/20"
                          style={{ left: `${left}%`, width: `${width}%` }}
                        >
                          <span className="truncate px-2 text-xs font-medium text-white">
                            {shipName}
                          </span>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      <div className="mt-3 flex flex-wrap items-center gap-x-5 gap-y-2 px-1 text-xs text-slate-600">
        <span className="flex items-center gap-1.5">
          <span aria-hidden="true" className="h-3 w-3 shrink-0 rounded bg-sea-600" /> At berth
          <span className="text-slate-500">(handling)</span>
        </span>
        <span className="flex items-center gap-1.5">
          <span
            aria-hidden="true"
            className="h-3 w-3 rounded border border-amber-300"
            style={{
              backgroundImage:
                "repeating-linear-gradient(45deg, rgba(217,119,6,0.16) 0 4px, transparent 4px 8px)",
            }}
          />
          Waiting <span className="text-slate-500">(at anchor, since ETA)</span>
        </span>
        <span className="flex items-center gap-1.5">
          <span aria-hidden="true" className="h-3 w-3 shrink-0 rounded bg-slate-200" /> Manoeuvring buffer
          <span className="text-slate-500">(berth blocked)</span>
        </span>
        <span className="ml-auto tabular-nums">Times in UTC</span>
      </div>
    </div>
  );
}
