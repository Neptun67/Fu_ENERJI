import { formatTime, toMillis } from "@/lib/datetime";
import type { Berth, Plan, Ship } from "@/lib/types";

const TICKS = 6;

function Gridlines({ lefts }: { lefts: number[] }) {
  return (
    <>
      {lefts.map((left, i) => (
        <div
          key={i}
          className="absolute bottom-0 top-0 w-px bg-slate-100"
          style={{ left: `${left}%` }}
        />
      ))}
    </>
  );
}

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
      <p className="p-6 text-sm text-slate-500">
        Bu planda atanmış gemi yok — atanamayanlar aşağıda listeleniyor.
      </p>
    );
  }

  const bufferMs = plan.buffer_min * 60_000;
  const starts = plan.assignments.map((a) => toMillis(a.start_time));
  const ends = plan.assignments.map((a) => toMillis(a.end_time) + bufferMs);
  let t0 = Math.min(...starts);
  let t1 = Math.max(...ends);
  const pad = Math.max((t1 - t0) * 0.04, 10 * 60_000);
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
      {/* zaman ekseni */}
      <div className="flex">
        <div className="w-28 shrink-0" />
        <div className="relative h-6 flex-1">
          {ticks.map((t, i) => (
            <span
              key={i}
              className="absolute -translate-x-1/2 whitespace-nowrap text-[11px] text-slate-400"
              style={{ left: `${t.left}%` }}
            >
              {t.label}
            </span>
          ))}
        </div>
      </div>

      {/* satırlar */}
      <div className="border-t border-slate-200">
        {rows.map((berth) => {
          const items = byBerth.get(berth.id) ?? [];
          return (
            <div key={berth.id} className="flex items-stretch border-b border-slate-100 last:border-0">
              <div className="flex w-28 shrink-0 items-center px-3 py-2 text-sm font-medium text-slate-700">
                {berth.name}
              </div>
              <div className="relative h-12 flex-1">
                <Gridlines lefts={tickLefts} />
                {items.map((a) => {
                  const start = toMillis(a.start_time);
                  const end = toMillis(a.end_time);
                  const shipName = shipsById.get(a.ship_id)?.name ?? `#${a.ship_id}`;
                  const left = pct(start);
                  const width = Math.max(pct(end) - left, 0.5);
                  const bufWidth = pct(end + bufferMs) - pct(end);
                  return (
                    <div key={a.id}>
                      {/* manevra tamponu */}
                      <div
                        className="absolute bottom-2 top-2 rounded-r bg-slate-200"
                        style={{ left: `${pct(end)}%`, width: `${bufWidth}%` }}
                        title={`Manevra tamponu: ${plan.buffer_min} dk`}
                      />
                      {/* atama */}
                      <div
                        className="absolute bottom-2 top-2 flex items-center overflow-hidden rounded bg-teal-600 shadow-sm"
                        style={{ left: `${left}%`, width: `${width}%` }}
                        title={`${shipName}\n${formatTime(a.start_time)} – ${formatTime(a.end_time)}\nBekleme: ${a.waiting_min} dk`}
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

      {/* açıklama */}
      <div className="mt-3 flex items-center gap-4 px-1 text-xs text-slate-500">
        <span className="flex items-center gap-1.5">
          <span className="h-3 w-3 rounded bg-teal-600" /> Atama
        </span>
        <span className="flex items-center gap-1.5">
          <span className="h-3 w-3 rounded bg-slate-200" /> Manevra tamponu
        </span>
        <span className="ml-auto">Saatler UTC</span>
      </div>
    </div>
  );
}
