"use client";
import { useEffect, useState } from "react";
import { api, ApiError } from "@/lib/api";
import { useApi, formatDate } from "@/lib/hooks";
import type { CursorPage, Tenant, User } from "@/lib/types";

export default function SettingsPage() {
  const { data: tenant, mutate: refreshTenant } =
    useApi<Tenant>("/api/v1/tenants/me");
  const { data: users, mutate: refreshUsers } =
    useApi<CursorPage<User>>("/api/v1/users?limit=100");

  const [name, setName] = useState("");
  const [phone, setPhone] = useState("");
  const [savedAt, setSavedAt] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [inviteEmail, setInviteEmail] = useState("");
  const [inviteRole, setInviteRole] = useState<"admin" | "staff">("staff");
  const [inviteMsg, setInviteMsg] = useState<string | null>(null);

  useEffect(() => {
    if (tenant) {
      setName(tenant.name);
      setPhone(tenant.twilio_phone_number ?? "");
    }
  }, [tenant]);

  async function onSaveTenant(e: React.FormEvent) {
    e.preventDefault();
    setErr(null);
    try {
      await api.patch("/api/v1/tenants/me", {
        name,
        twilio_phone_number: phone || null,
      });
      setSavedAt(new Date().toLocaleTimeString());
      await refreshTenant();
    } catch (e) {
      setErr(e instanceof ApiError ? e.message : String(e));
    }
  }

  async function onInvite(e: React.FormEvent) {
    e.preventDefault();
    setInviteMsg(null);
    try {
      await api.post("/api/v1/users/invite", {
        email: inviteEmail,
        role: inviteRole,
      });
      setInviteMsg(`Invited ${inviteEmail}`);
      setInviteEmail("");
      await refreshUsers();
    } catch (e) {
      setInviteMsg(e instanceof ApiError ? e.message : String(e));
    }
  }

  return (
    <>
      <h1 className="text-2xl font-semibold">Settings</h1>
      <section className="mt-6 max-w-xl rounded-lg border bg-white p-4">
        <h2 className="text-sm font-semibold">Company</h2>
        <form onSubmit={onSaveTenant} className="mt-3 flex flex-col gap-3">
          <label className="text-xs text-slate-500">
            Name
            <input
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="mt-1 w-full rounded-md border px-3 py-2 text-sm"
            />
          </label>
          <label className="text-xs text-slate-500">
            Twilio phone number (E.164)
            <input
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
              placeholder="+15551234567"
              className="mt-1 w-full rounded-md border px-3 py-2 text-sm"
            />
          </label>
          <div className="flex items-center gap-3">
            <button className="rounded-md bg-slate-900 px-4 py-2 text-sm text-white">
              Save
            </button>
            {savedAt ? (
              <span className="text-xs text-slate-500">Saved at {savedAt}</span>
            ) : null}
            {err ? <span className="text-xs text-red-600">{err}</span> : null}
          </div>
        </form>
        {tenant ? (
          <p className="mt-3 text-xs text-slate-500">
            Plan: {tenant.plan} · Trial ends: {formatDate(tenant.trial_ends_at)}
          </p>
        ) : null}
      </section>
      <section className="mt-6 max-w-3xl rounded-lg border bg-white p-4">
        <h2 className="text-sm font-semibold">Team</h2>
        <form onSubmit={onInvite} className="mt-3 flex gap-2">
          <input
            type="email"
            required
            placeholder="teammate@company.com"
            value={inviteEmail}
            onChange={(e) => setInviteEmail(e.target.value)}
            className="flex-1 rounded-md border px-3 py-2 text-sm"
          />
          <select
            value={inviteRole}
            onChange={(e) =>
              setInviteRole(e.target.value as "admin" | "staff")
            }
            className="rounded-md border px-3 py-2 text-sm"
          >
            <option value="staff">Staff</option>
            <option value="admin">Admin</option>
          </select>
          <button className="rounded-md bg-slate-900 px-4 py-2 text-sm text-white">
            Invite
          </button>
        </form>
        {inviteMsg ? (
          <p className="mt-2 text-xs text-slate-500">{inviteMsg}</p>
        ) : null}
        <table className="mt-4 w-full text-sm">
          <thead className="text-left text-xs uppercase text-slate-500">
            <tr>
              <th className="py-1">Email</th>
              <th className="py-1">Name</th>
              <th className="py-1">Role</th>
              <th className="py-1">Status</th>
            </tr>
          </thead>
          <tbody>
            {users?.items.map((u) => (
              <tr key={u.id} className="border-t">
                <td className="py-1">{u.email}</td>
                <td className="py-1">{u.full_name}</td>
                <td className="py-1">{u.role}</td>
                <td className="py-1">{u.is_active ? "active" : "disabled"}</td>
              </tr>
            )) ?? null}
          </tbody>
        </table>
      </section>
    </>
  );
}
