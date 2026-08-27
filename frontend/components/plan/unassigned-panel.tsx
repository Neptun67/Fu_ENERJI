import type { Ship, UnassignedEntry } from "@/lib/types";

/*
  Ships the planner could not place, each with the physical constraint that
  blocked it. Amber rather than red: this is not an application error, it is a
  legitimate outcome that the operator needs to act on.
*/
export function UnassignedPanel({
  entries,
  shipsById,
}: {
  entries: UnassignedEntry[];
  shipsById: Map<number, Ship>;
}) {
  if (entries.length === 0) {
    return (
      <p className="text-sm text-slate-600">Every ship was assigned to a berth.</p>
    );
  }
  return (
    <ul className="divide-y divide-slate-100">
      {entries.map((u) => {
        // Name comes from the entry itself, so a deleted vessel still reads.
        const ship = u.ship_id != null ? shipsById.get(u.ship_id) : undefined;
        const name = u.ship_name || `#${u.ship_id ?? "?"}`;
        return (
          <li
            key={u.id}
            className="flex flex-wrap items-center justify-between gap-x-3 gap-y-1 py-2.5"
          >
            <div className="flex items-baseline gap-2">
              <span className="font-medium text-slate-900">{name}</span>
              {ship && (
                <span className="text-xs tabular-nums text-slate-500">
                  {ship.length_m} m / {ship.draft_m} m draft
                </span>
              )}
            </div>
            <span className="rounded-full bg-amber-50 px-2.5 py-0.5 text-xs font-medium text-amber-900 ring-1 ring-amber-200">
              {u.reason_message}
            </span>
          </li>
        );
      })}
    </ul>
  );
}
