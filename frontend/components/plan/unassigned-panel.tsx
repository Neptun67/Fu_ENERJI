import type { Ship, UnassignedEntry } from "@/lib/types";

export function UnassignedPanel({
  entries,
  shipsById,
}: {
  entries: UnassignedEntry[];
  shipsById: Map<number, Ship>;
}) {
  if (entries.length === 0) {
    return (
      <p className="text-sm text-slate-500">Tüm gemiler bir rıhtıma atandı.</p>
    );
  }
  return (
    <ul className="divide-y divide-slate-100">
      {entries.map((u) => {
        const name = shipsById.get(u.ship_id)?.name ?? `#${u.ship_id}`;
        return (
          <li key={u.id} className="flex items-center justify-between gap-3 py-2.5">
            <span className="font-medium text-slate-900">{name}</span>
            <span className="rounded-full bg-amber-50 px-2.5 py-0.5 text-xs font-medium text-amber-700">
              {u.reason_message}
            </span>
          </li>
        );
      })}
    </ul>
  );
}
