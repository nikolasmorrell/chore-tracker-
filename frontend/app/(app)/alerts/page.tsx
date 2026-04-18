"use client";
import { useState } from "react";
import { api } from "@/lib/api";
import { useApi, formatDate } from "@/lib/hooks";
import type { Alert, CursorPage } from "@/lib/types";

export default function AlertsPage() {
  const [filter, setFilter] = useState<"all" | "scheduled" | "sent" | "dismissed">(
    "scheduled",
  );
  const path =
    filter === "all"
      ? "/api/v1/alerts?limit=200"
      : `/api/v1/alerts?status=${filter}&limit=200`;
  const { data, isLoading, mutate } = useApi<CursorPage<Alert>>(path);

  async function dismiss(id: string) {
    await api.post(`/api/v1/alerts/${id}/dismiss`);
    await mutate();
  }

  return (
    <>
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Alerts</h1>
        <select
          value={filter}
          onChange={(e) =>
            setFilter(e.target.value as typeof filter)
          }
          className="rounded-md border px-3 py-1 text-sm"
        >
          <option value="scheduled">Scheduled</option>
          <option value="sent">Sent</option>
          <option value="dismissed">Dismissed</option>
          <option value="all">All</option>
        </select>
      </div>
      <div className="mt-6 rounded-lg border bg-white">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 text-left text-xs uppercase text-slate-500">
            <tr>
              <th className="px-4 py-2">Kind</th>
              <th className="px-4 py-2">Channel</th>
              <th className="px-4 py-2">Due</th>
              <th className="px-4 py-2">Status</th>
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
              data.items.map((a) => (
                <tr key={a.id} className="border-t">
                  <td className="px-4 py-2">{a.kind.replace("_", " ")}</td>
                  <td className="px-4 py-2">{a.channel}</td>
                  <td className="px-4 py-2">{formatDate(a.due_at)}</td>
                  <td className="px-4 py-2">{a.status}</td>
                  <td className="px-4 py-2 text-right">
                    {a.status !== "dismissed" ? (
                      <button
                        onClick={() => dismiss(a.id)}
                        className="text-xs text-slate-600 underline"
                      >
                        Dismiss
                      </button>
                    ) : null}
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td className="px-4 py-4 text-slate-500" colSpan={5}>
                  No alerts.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </>
  );
}
