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
  const [confirmingId, setConfirmingId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [pending, startTransition] = useTransition();
  const [busy, setBusy] = useState(false);

  const set = (key: keyof FormState) => (value: string) =>
    setForm((f) => ({ ...f, [key]: value }));

  function reset() {
    setForm(EMPTY);
    setEditingId(null);
    setError(null);
  }

  async function submit() {
    setError(null);
    setBusy(true);
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
    } finally {
      setBusy(false);
    }
  }

  function edit(ship: Ship) {
    setEditingId(ship.id);
    setConfirmingId(null);
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
    setBusy(true);
    try {
      await deleteShip(id);
      if (editingId === id) reset();
      setConfirmingId(null);
      startTransition(() => router.refresh());
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not delete");
      setConfirmingId(null);
    } finally {
      setBusy(false);
    }
  }

  const canSubmit =
    form.name && form.eta && form.length_m && form.draft_m && form.handling_time_min;
  const editing = editingId != null;
  const working = busy || pending;

  return (
    <div className="space-y-6">
      <form
        onSubmit={(e) => {
          e.preventDefault();
          if (canSubmit) submit();
        }}
        className={`rounded-xl border bg-white p-5 shadow-sm transition-colors ${
          editing ? "border-sea-300 ring-1 ring-sea-100" : "border-slate-200"
        }`}
      >
        <h2 className="mb-4 text-sm font-semibold text-sea-900">
          {editing ? "Edit ship" : "New ship"}
        </h2>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <Field label="Name" value={form.name} onChange={set("name")} required />
          <Field
            label="Arrival (ETA)"
            type="datetime-local"
            value={form.eta}
            onChange={set("eta")}
            hint="Estimated time of arrival, in UTC"
            required
          />
          <Field
            label="Length"
            type="number"
            step="0.1"
            min="0"
            suffix="m"
            value={form.length_m}
            onChange={set("length_m")}
            required
          />
          <Field
            label="Draft"
            type="number"
            step="0.1"
            min="0"
            suffix="m"
            value={form.draft_m}
            onChange={set("draft_m")}
            hint="Must not exceed the berth depth"
            required
          />
          <Field
            label="Handling time"
            type="number"
            step="1"
            min="0"
            suffix="min"
            value={form.handling_time_min}
            onChange={set("handling_time_min")}
            hint="Time at the berth, excluding manoeuvres"
            required
          />
        </div>
        <div className="mt-5 flex items-center gap-2">
          <Button type="submit" disabled={!canSubmit || working}>
            {working ? "Saving..." : editing ? "Save changes" : "Add ship"}
          </Button>
          {editing && (
            <Button type="button" variant="ghost" onClick={reset} disabled={working}>
              Cancel
            </Button>
          )}
        </div>
        {error && (
          <p
            role="alert"
            className="mt-4 rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-800"
          >
            {error}
          </p>
        )}
      </form>

      <div className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
        <div className="flex items-baseline justify-between border-b border-slate-200 px-4 py-3">
          <h2 className="text-sm font-semibold text-sea-900">Fleet</h2>
          <span className="text-xs text-slate-500">
            {initialShips.length} {initialShips.length === 1 ? "ship" : "ships"}
          </span>
        </div>

        {initialShips.length === 0 ? (
          <div className="px-6 py-12 text-center">
            <p className="text-sm font-medium text-slate-700">No ships yet</p>
            <p className="mx-auto mt-1 max-w-sm text-sm text-slate-500">
              Add the first vessel using the form above. At least one ship and one berth are
              needed before a plan can be generated.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <caption className="sr-only">Ships arriving at the port</caption>
              <thead>
                <tr className="border-b border-slate-200 text-left text-xs uppercase tracking-wide text-slate-600">
                  <th scope="col" className="px-4 py-2.5 font-medium">Name</th>
                  <th scope="col" className="px-4 py-2.5 font-medium">Arrival (UTC)</th>
                  <th scope="col" className="px-4 py-2.5 text-right font-medium">Length</th>
                  <th scope="col" className="px-4 py-2.5 text-right font-medium">Draft</th>
                  <th scope="col" className="px-4 py-2.5 text-right font-medium">Handling</th>
                  <th scope="col" className="px-4 py-2.5">
                    <span className="sr-only">Actions</span>
                  </th>
                </tr>
              </thead>
              <tbody>
                {initialShips.map((ship) => {
                  const isEditing = editingId === ship.id;
                  const isConfirming = confirmingId === ship.id;
                  return (
                    <tr
                      key={ship.id}
                      className={`border-b border-slate-100 transition-colors last:border-0 ${
                        isEditing ? "bg-sea-50" : "hover:bg-slate-50"
                      }`}
                    >
                      <td className="px-4 py-2.5 font-medium text-slate-900">{ship.name}</td>
                      <td className="px-4 py-2.5 text-slate-600">{formatDateTime(ship.eta)}</td>
                      <td className="px-4 py-2.5 text-right tabular-nums text-slate-600">
                        {ship.length_m} m
                      </td>
                      <td className="px-4 py-2.5 text-right tabular-nums text-slate-600">
                        {ship.draft_m} m
                      </td>
                      <td className="px-4 py-2.5 text-right tabular-nums text-slate-600">
                        {ship.handling_time_min} min
                      </td>
                      <td className="px-4 py-2.5">
                        {isConfirming ? (
                          <div className="flex items-center justify-end gap-1.5">
                            <span className="text-xs text-slate-600">Delete?</span>
                            <Button
                              size="sm"
                              variant="danger"
                              onClick={() => remove(ship.id)}
                              disabled={working}
                            >
                              Confirm
                            </Button>
                            <Button size="sm" variant="ghost" onClick={() => setConfirmingId(null)}>
                              Keep
                            </Button>
                          </div>
                        ) : (
                          <div className="flex items-center justify-end gap-1">
                            <Button size="sm" variant="ghost" onClick={() => edit(ship)}>
                              Edit
                            </Button>
                            <Button
                              size="sm"
                              variant="danger"
                              onClick={() => setConfirmingId(ship.id)}
                            >
                              Delete
                            </Button>
                          </div>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
