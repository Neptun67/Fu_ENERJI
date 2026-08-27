"use client";

import { useState, useTransition } from "react";
import { useRouter } from "next/navigation";

import { Button } from "@/components/ui/button";
import { Field } from "@/components/ui/field";
import { createBerth, deleteBerth, updateBerth } from "@/lib/api";
import type { Berth } from "@/lib/types";

const EMPTY = { name: "", length_m: "", depth_m: "" };
type FormState = typeof EMPTY;

export function BerthManager({ initialBerths }: { initialBerths: Berth[] }) {
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
      length_m: Number(form.length_m),
      depth_m: Number(form.depth_m),
    };
    try {
      if (editingId == null) await createBerth(payload);
      else await updateBerth(editingId, payload);
      reset();
      startTransition(() => router.refresh());
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not save");
    } finally {
      setBusy(false);
    }
  }

  function edit(berth: Berth) {
    setEditingId(berth.id);
    setConfirmingId(null);
    setError(null);
    setForm({
      name: berth.name,
      length_m: String(berth.length_m),
      depth_m: String(berth.depth_m),
    });
  }

  async function remove(id: number) {
    setError(null);
    setBusy(true);
    try {
      await deleteBerth(id);
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

  const canSubmit = form.name && form.length_m && form.depth_m;
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
          {editing ? "Edit berth" : "New berth"}
        </h2>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          <Field label="Name" value={form.name} onChange={set("name")} required />
          <Field
            label="Length"
            type="number"
            step="0.1"
            min="0"
            suffix="m"
            value={form.length_m}
            onChange={set("length_m")}
            hint="Longest vessel it can take"
            required
          />
          <Field
            label="Depth"
            type="number"
            step="0.1"
            min="0"
            suffix="m"
            value={form.depth_m}
            onChange={set("depth_m")}
            hint="Deepest draft it can take"
            required
          />
        </div>
        <div className="mt-5 flex items-center gap-2">
          <Button type="submit" disabled={!canSubmit || working}>
            {working ? "Saving..." : editing ? "Save changes" : "Add berth"}
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
          <h2 className="text-sm font-semibold text-sea-900">Quay</h2>
          <span className="text-xs text-slate-500">
            {initialBerths.length} {initialBerths.length === 1 ? "berth" : "berths"}
          </span>
        </div>

        {initialBerths.length === 0 ? (
          <div className="px-6 py-12 text-center">
            <p className="text-sm font-medium text-slate-700">No berths yet</p>
            <p className="mx-auto mt-1 max-w-sm text-sm text-slate-500">
              Describe your quay using the form above. A ship can only be placed on a berth
              that is long enough and deep enough for it.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <caption className="sr-only">Berths available in the port</caption>
              <thead>
                <tr className="border-b border-slate-200 text-left text-xs uppercase tracking-wide text-slate-600">
                  <th scope="col" className="px-4 py-2.5 font-medium">Name</th>
                  <th scope="col" className="px-4 py-2.5 text-right font-medium">Length</th>
                  <th scope="col" className="px-4 py-2.5 text-right font-medium">Depth</th>
                  <th scope="col" className="px-4 py-2.5">
                    <span className="sr-only">Actions</span>
                  </th>
                </tr>
              </thead>
              <tbody>
                {initialBerths.map((berth) => {
                  const isEditing = editingId === berth.id;
                  const isConfirming = confirmingId === berth.id;
                  return (
                    <tr
                      key={berth.id}
                      className={`border-b border-slate-100 transition-colors last:border-0 ${
                        isEditing ? "bg-sea-50" : "hover:bg-slate-50"
                      }`}
                    >
                      <td className="px-4 py-2.5 font-medium text-slate-900">{berth.name}</td>
                      <td className="px-4 py-2.5 text-right tabular-nums text-slate-600">
                        {berth.length_m} m
                      </td>
                      <td className="px-4 py-2.5 text-right tabular-nums text-slate-600">
                        {berth.depth_m} m
                      </td>
                      <td className="px-4 py-2.5">
                        {isConfirming ? (
                          <div className="flex items-center justify-end gap-1.5">
                            <span className="text-xs text-slate-600">Delete?</span>
                            <Button
                              size="sm"
                              variant="danger"
                              onClick={() => remove(berth.id)}
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
                            <Button size="sm" variant="ghost" onClick={() => edit(berth)}>
                              Edit
                            </Button>
                            <Button
                              size="sm"
                              variant="danger"
                              onClick={() => setConfirmingId(berth.id)}
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
