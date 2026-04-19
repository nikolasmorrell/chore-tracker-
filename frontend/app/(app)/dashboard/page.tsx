"use client";
import { useApi } from "@/lib/hooks";
import type { Alert, Call, CursorPage, DocumentItem, Task } from "@/lib/types";

export default function DashboardPage() {
  const docs = useApi<CursorPage<DocumentItem>>("/api/v1/documents?limit=100");
  const alerts = useApi<CursorPage<Alert>>(
    "/api/v1/alerts?status=scheduled&limit=100",
  );
  const calls = useApi<CursorPage<Call>>("/api/v1/calls?limit=100");
  const tasks = useApi<CursorPage<Task>>("/api/v1/tasks?status=open&limit=100");

  const kpis = [
    {
      label: "Documents",
      value: docs.data?.items.length ?? "—",
    },
    {
      label: "Open alerts",
      value: alerts.data?.items.length ?? "—",
    },
    {
      label: "Calls",
      value: calls.data?.items.length ?? "—",
    },
    {
      label: "Open tasks",
      value: tasks.data?.items.length ?? "—",
    },
  ];

  return (
    <>
      <h1 className="text-2xl font-semibold">Dashboard</h1>
      <section className="mt-6 grid grid-cols-2 gap-4 md:grid-cols-4">
        {kpis.map((k) => (
          <div
            key={k.label}
            className="rounded-lg border bg-white p-4 shadow-sm"
          >
            <div className="text-xs uppercase text-slate-500">{k.label}</div>
            <div className="mt-2 text-3xl font-semibold">{k.value}</div>
          </div>
        ))}
      </section>
      <section className="mt-8 grid gap-6 md:grid-cols-2">
        <Panel title="Next 5 alerts">
          {alerts.data?.items.slice(0, 5).map((a) => (
            <div key={a.id} className="flex justify-between py-1 text-sm">
              <span>{a.kind.replace("_", " ")}</span>
              <span className="text-slate-500">
                {new Date(a.due_at).toLocaleDateString()}
              </span>
            </div>
          )) ?? <p className="text-sm text-slate-500">No alerts.</p>}
        </Panel>
        <Panel title="Recent calls">
          {calls.data?.items.slice(0, 5).map((c) => (
            <div key={c.id} className="flex justify-between py-1 text-sm">
              <span>{c.from_number}</span>
              <span className="text-slate-500">{c.intent ?? c.status}</span>
            </div>
          )) ?? <p className="text-sm text-slate-500">No calls yet.</p>}
        </Panel>
      </section>
    </>
  );
}

function Panel({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <div className="rounded-lg border bg-white p-4 shadow-sm">
      <div className="mb-2 text-sm font-semibold">{title}</div>
      {children}
    </div>
  );
}
