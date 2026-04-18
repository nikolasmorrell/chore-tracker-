"use client";
import { useState } from "react";
import { api } from "@/lib/api";
import { useApi, formatDate } from "@/lib/hooks";
import type { Customer, CursorPage } from "@/lib/types";

export default function CustomersPage() {
  const { data, isLoading, mutate } =
    useApi<CursorPage<Customer>>("/api/v1/customers?limit=200");
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState({
    name: "",
    phone: "",
    email: "",
    notes: "",
  });
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  async function onCreate(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setErr(null);
    try {
      await api.post("/api/v1/customers", {
        name: form.name,
        phone: form.phone || null,
        email: form.email || null,
        notes: form.notes || null,
      });
      setForm({ name: "", phone: "", email: "", notes: "" });
      setOpen(false);
      await mutate();
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }

  async function onDelete(id: string) {
    if (!confirm("Delete this customer?")) return;
    await api.delete(`/api/v1/customers/${id}`);
    await mutate();
  }

  return (
    <>
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Customers</h1>
        <button
          onClick={() => setOpen((v) => !v)}
          className="rounded-md bg-slate-900 px-4 py-2 text-sm text-white"
        >
          {open ? "Cancel" : "Add customer"}
        </button>
      </div>
      {open ? (
        <form
          onSubmit={onCreate}
          className="mt-4 grid gap-2 rounded-lg border bg-white p-4 md:grid-cols-2"
        >
          <input
            required
            placeholder="Name"
            value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })}
            className="rounded-md border px-3 py-2 text-sm"
          />
          <input
            placeholder="Phone"
            value={form.phone}
            onChange={(e) => setForm({ ...form, phone: e.target.value })}
            className="rounded-md border px-3 py-2 text-sm"
          />
          <input
            type="email"
            placeholder="Email"
            value={form.email}
            onChange={(e) => setForm({ ...form, email: e.target.value })}
            className="rounded-md border px-3 py-2 text-sm"
          />
          <input
            placeholder="Notes"
            value={form.notes}
            onChange={(e) => setForm({ ...form, notes: e.target.value })}
            className="rounded-md border px-3 py-2 text-sm"
          />
          {err ? (
            <p className="md:col-span-2 text-sm text-red-600">{err}</p>
          ) : null}
          <button
            disabled={busy}
            className="md:col-span-2 rounded-md bg-slate-900 px-4 py-2 text-sm text-white disabled:opacity-60"
          >
            {busy ? "Saving…" : "Save"}
          </button>
        </form>
      ) : null}
      <div className="mt-6 rounded-lg border bg-white">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 text-left text-xs uppercase text-slate-500">
            <tr>
              <th className="px-4 py-2">Name</th>
              <th className="px-4 py-2">Phone</th>
              <th className="px-4 py-2">Email</th>
              <th className="px-4 py-2">Added</th>
              <th className="px-4 py-2"></th>
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              <tr>
                <td className="px-4 py-4 text-slate-500" colSpan={5}>
                  Loading…
                </td>
              </tr>
            ) : data && data.items.length ? (
              data.items.map((c) => (
                <tr key={c.id} className="border-t">
                  <td className="px-4 py-2 font-medium">{c.name}</td>
                  <td className="px-4 py-2">{c.phone ?? "—"}</td>
                  <td className="px-4 py-2">{c.email ?? "—"}</td>
                  <td className="px-4 py-2 text-slate-500">
                    {formatDate(c.created_at)}
                  </td>
                  <td className="px-4 py-2 text-right">
                    <button
                      onClick={() => onDelete(c.id)}
                      className="text-xs text-red-600 underline"
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td className="px-4 py-4 text-slate-500" colSpan={5}>
                  No customers yet.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </>
  );
}
