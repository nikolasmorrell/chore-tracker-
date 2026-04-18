"use client";
import { useState } from "react";
import { api } from "@/lib/api";
import { useApi, formatDate } from "@/lib/hooks";
import type { CursorPage, Task } from "@/lib/types";

type Filter = "all" | "open" | "in_progress" | "done" | "cancelled";

export default function TasksPage() {
  const [filter, setFilter] = useState<Filter>("open");
  const path =
    filter === "all"
      ? "/api/v1/tasks?limit=200"
      : `/api/v1/tasks?status=${filter}&limit=200`;
  const { data, isLoading, mutate } = useApi<CursorPage<Task>>(path);

  async function setStatus(id: string, status: Task["status"]) {
    await api.patch(`/api/v1/tasks/${id}`, { status });
    await mutate();
  }

  return (
    <>
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Tasks</h1>
        <select
          value={filter}
          onChange={(e) => setFilter(e.target.value as Filter)}
          className="rounded-md border px-3 py-1 text-sm"
        >
          <option value="open">Open</option>
          <option value="in_progress">In progress</option>
          <option value="done">Done</option>
          <option value="cancelled">Cancelled</option>
          <option value="all">All</option>
        </select>
      </div>
      <div className="mt-6 rounded-lg border bg-white">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 text-left text-xs uppercase text-slate-500">
            <tr>
              <th className="px-4 py-2">Title</th>
              <th className="px-4 py-2">Priority</th>
              <th className="px-4 py-2">Due</th>
              <th className="px-4 py-2">Source</th>
              <th className="px-4 py-2">Status</th>
              <th className="px-4 py-2"></th>
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              <tr>
                <td className="px-4 py-4 text-slate-500" colSpan={6}>
                  Loading…
                </td>
              </tr>
            ) : data && data.items.length ? (
              data.items.map((t) => (
                <tr key={t.id} className="border-t">
                  <td className="px-4 py-2 font-medium">{t.title}</td>
                  <td className="px-4 py-2">{t.priority}</td>
                  <td className="px-4 py-2">{formatDate(t.due_at)}</td>
                  <td className="px-4 py-2">{t.source}</td>
                  <td className="px-4 py-2">{t.status}</td>
                  <td className="px-4 py-2 text-right">
                    {t.status === "open" ? (
                      <button
                        onClick={() => setStatus(t.id, "done")}
                        className="text-xs text-emerald-700 underline"
                      >
                        Mark done
                      </button>
                    ) : null}
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td className="px-4 py-4 text-slate-500" colSpan={6}>
                  No tasks.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </>
  );
}
