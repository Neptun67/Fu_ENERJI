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
      length_m: Number(form.length_m),
      depth_m: Number(form.depth_m),
    };
    try {
      if (editingId == null) await createBerth(payload);
      else await updateBerth(editingId, payload);
      reset();
      startTransition(() => router.refresh());
    } catch (e) {
      setError(e instanceof Error ? e.message : "Kaydedilemedi");
    }
  }

  function edit(berth: Berth) {
    setEditingId(berth.id);
    setError(null);
    setForm({
      name: berth.name,
      length_m: String(berth.length_m),
      depth_m: String(berth.depth_m),
    });
  }

  async function remove(id: number) {
    setError(null);
    try {
      await deleteBerth(id);
      if (editingId === id) reset();
      startTransition(() => router.refresh());
    } catch (e) {
      setError(e instanceof Error ? e.message : "Silinemedi");
    }
  }

  const canSubmit = form.name && form.length_m && form.depth_m;

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
          {editingId == null ? "Yeni rıhtım" : "Rıhtımı düzenle"}
        </h2>
        <div className="grid grid-cols-2 gap-4 md:grid-cols-3">
          <Field label="Ad" value={form.name} onChange={set("name")} required />
          <Field label="Uzunluk (m)" type="number" step="0.1" min="0" value={form.length_m} onChange={set("length_m")} required />
          <Field label="Derinlik (m)" type="number" step="0.1" min="0" value={form.depth_m} onChange={set("depth_m")} required />
        </div>
        <div className="mt-4 flex items-center gap-2">
          <Button type="submit" disabled={!canSubmit || pending}>
            {editingId == null ? "Rıhtım ekle" : "Değişiklikleri kaydet"}
          </Button>
          {editingId != null && (
            <Button type="button" variant="ghost" onClick={reset}>
              Vazgeç
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
        {initialBerths.length === 0 ? (
          <p className="p-6 text-sm text-slate-500">
            Henüz rıhtım yok. Yukarıdaki formdan ilk rıhtımı ekleyin.
          </p>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-200 text-left text-xs uppercase tracking-wide text-slate-500">
                <th className="px-4 py-3 font-medium">Ad</th>
                <th className="px-4 py-3 font-medium text-right">Uzunluk</th>
                <th className="px-4 py-3 font-medium text-right">Derinlik</th>
                <th className="px-4 py-3" />
              </tr>
            </thead>
            <tbody>
              {initialBerths.map((berth) => (
                <tr key={berth.id} className="border-b border-slate-100 last:border-0 hover:bg-slate-50">
                  <td className="px-4 py-3 font-medium text-slate-900">{berth.name}</td>
                  <td className="px-4 py-3 text-right tabular-nums text-slate-600">{berth.length_m} m</td>
                  <td className="px-4 py-3 text-right tabular-nums text-slate-600">{berth.depth_m} m</td>
                  <td className="px-4 py-3 text-right">
                    <div className="flex justify-end gap-1">
                      <Button variant="ghost" onClick={() => edit(berth)}>Düzenle</Button>
                      <Button variant="danger" onClick={() => remove(berth.id)}>Sil</Button>
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
