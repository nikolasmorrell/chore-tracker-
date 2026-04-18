"use client";
import { useState } from "react";
import { useApi, formatDate } from "@/lib/hooks";
import type { Call, CallDetail, CursorPage } from "@/lib/types";

export default function CallsPage() {
  const { data, isLoading } =
    useApi<CursorPage<Call>>("/api/v1/calls?limit=100");
  const [selected, setSelected] = useState<string | null>(null);
  const { data: detail } = useApi<CallDetail>(
    selected ? `/api/v1/calls/${selected}` : null,
  );

  return (
    <>
      <h1 className="text-2xl font-semibold">Calls</h1>
      <div className="mt-6 grid gap-6 md:grid-cols-[2fr_3fr]">
        <div className="rounded-lg border bg-white">
          <table className="w-full text-sm">
            <thead className="bg-slate-50 text-left text-xs uppercase text-slate-500">
              <tr>
                <th className="px-4 py-2">From</th>
                <th className="px-4 py-2">Intent</th>
                <th className="px-4 py-2">Started</th>
              </tr>
            </thead>
            <tbody>
              {isLoading ? (
                <tr>
                  <td className="px-4 py-4 text-slate-500" colSpan={3}>
                    Loading…
                  </td>
                </tr>
              ) : data && data.items.length ? (
                data.items.map((c) => (
                  <tr
                    key={c.id}
                    onClick={() => setSelected(c.id)}
                    className={`cursor-pointer border-t hover:bg-slate-50 ${selected === c.id ? "bg-slate-100" : ""}`}
                  >
                    <td className="px-4 py-2 font-medium">{c.from_number}</td>
                    <td className="px-4 py-2">{c.intent ?? c.status}</td>
                    <td className="px-4 py-2 text-slate-500">
                      {formatDate(c.started_at ?? null)}
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td className="px-4 py-4 text-slate-500" colSpan={3}>
                    No calls yet.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
        <div className="rounded-lg border bg-white p-4">
          {detail ? (
            <>
              <div className="mb-2 text-sm font-semibold">
                {detail.from_number} → {detail.to_number}
              </div>
              <div className="mb-4 text-xs text-slate-500">
                Intent: {detail.intent ?? "—"} · Status: {detail.status}
              </div>
              {detail.summary ? (
                <p className="mb-4 rounded-md bg-slate-50 p-3 text-sm">
                  {detail.summary}
                </p>
              ) : null}
              <div className="space-y-2">
                {detail.turns.map((t) => (
                  <div
                    key={t.id}
                    className={`rounded-md p-2 text-sm ${
                      t.speaker === "assistant"
                        ? "bg-slate-100"
                        : "bg-emerald-50"
                    }`}
                  >
                    <div className="text-xs uppercase text-slate-500">
                      {t.speaker}
                    </div>
                    <div>{t.text}</div>
                  </div>
                ))}
              </div>
            </>
          ) : (
            <p className="text-sm text-slate-500">
              Select a call to see the transcript.
            </p>
          )}
        </div>
      </div>
    </>
  );
}
