"use client";

import { useState, useTransition } from "react";
import { useRouter } from "next/navigation";

import { Button } from "@/components/ui/button";
import { Field } from "@/components/ui/field";
import { createShip, deleteShip, updateShip } from "@/lib/api";
import { formatDateTime, inputToIso, isoToInput } from "@/lib/datetime";
import type { Ship } from "@/lib/types";

const EMPTY = { name: "", eta: "", length_m: "", draft_m: "", handling_time_min: "" };
type FormState = typeof EMPTY;

export function ShipManager({ initialShips }: { initialShips: Ship[] }) {
  const router = useRouter();
  const [form, setForm] = useState<FormState>(EMPTY);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [pending, startTransition] = useTransition();

  const set = (key: keyof FormState) => (value: string) =>
    setForm((f) => ({ ...f, [key]: value }));

  function reset() {
    setForm(EMPTY);
    setEditingId(null);
    setError(null);
  }

  async function submit() {
    setError(null);
    const payload = {
      name: form.name.trim(),
      eta: inputToIso(form.eta),
      length_m: Number(form.length_m),
      draft_m: Number(form.draft_m),
      handling_time_min: Number(form.handling_time_min),
    };
    try {
      if (editingId == null) await createShip(payload);
      else await updateShip(editingId, payload);
      reset();
      startTransition(() => router.refresh());
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not save");
    }
  }

  function edit(ship: Ship) {
    setEditingId(ship.id);
    setError(null);
    setForm({
      name: ship.name,
      eta: isoToInput(ship.eta),
      length_m: String(ship.length_m),
      draft_m: String(ship.draft_m),
      handling_time_min: String(ship.handling_time_min),
    });
  }

  async function remove(id: number) {
    setError(null);
    try {
      await deleteShip(id);
      if (editingId === id) reset();
      startTransition(() => router.refresh());
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not delete");
    }
  }

  const canSubmit =
    form.name && form.eta && form.length_m && form.draft_m && form.handling_time_min;

  return (
    <div className="space-y-6">
      <form
        onSubmit={(e) => {
          e.preventDefault();
          if (canSubmit) submit();
        }}
        className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm"
      >
        <h2 className="mb-4 text-sm font-semibold text-slate-900">
          {editingId == null ? "New ship" : "Edit ship"}
        </h2>
        <div className="grid grid-cols-2 gap-4 md:grid-cols-3">
          <Field label="Name" value={form.name} onChange={set("name")} required />
          <Field label="ETA (UTC)" type="datetime-local" value={form.eta} onChange={set("eta")} required />
          <Field label="Length (m)" type="number" step="0.1" min="0" value={form.length_m} onChange={set("length_m")} required />
          <Field label="Draft (m)" type="number" step="0.1" min="0" value={form.draft_m} onChange={set("draft_m")} required />
          <Field label="Handling (min)" type="number" step="1" min="0" value={form.handling_time_min} onChange={set("handling_time_min")} required />
        </div>
        <div className="mt-4 flex items-center gap-2">
          <Button type="submit" disabled={!canSubmit || pending}>
            {editingId == null ? "Add ship" : "Save changes"}
          </Button>
          {editingId != null && (
            <Button type="button" variant="ghost" onClick={reset}>
              Cancel
            </Button>
          )}
        </div>
        {error && (
          <p role="alert" className="mt-3 text-sm text-red-600">
            {error}
          </p>
        )}
      </form>

      <div className="overflow-hidden rounded-lg border border-slate-200 bg-white shadow-sm">
        {initialShips.length === 0 ? (
          <p className="p-6 text-sm text-slate-500">
            No ships yet. Add the first one using the form above.
          </p>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-200 text-left text-xs uppercase tracking-wide text-slate-500">
                <th className="px-4 py-3 font-medium">Name</th>
                <th className="px-4 py-3 font-medium">ETA</th>
                <th className="px-4 py-3 font-medium text-right">Length</th>
                <th className="px-4 py-3 font-medium text-right">Draft</th>
                <th className="px-4 py-3 font-medium text-right">Handling</th>
                <th className="px-4 py-3" />
              </tr>
            </thead>
            <tbody>
              {initialShips.map((ship) => (
                <tr key={ship.id} className="border-b border-slate-100 last:border-0 hover:bg-slate-50">
                  <td className="px-4 py-3 font-medium text-slate-900">{ship.name}</td>
                  <td className="px-4 py-3 text-slate-600">{formatDateTime(ship.eta)}</td>
                  <td className="px-4 py-3 text-right tabular-nums text-slate-600">{ship.length_m} m</td>
                  <td className="px-4 py-3 text-right tabular-nums text-slate-600">{ship.draft_m} m</td>
                  <td className="px-4 py-3 text-right tabular-nums text-slate-600">{ship.handling_time_min} min</td>
                  <td className="px-4 py-3 text-right">
                    <div className="flex justify-end gap-1">
                      <Button variant="ghost" onClick={() => edit(ship)}>Edit</Button>
                      <Button variant="danger" onClick={() => remove(ship.id)}>Delete</Button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
