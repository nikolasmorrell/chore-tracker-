"use client";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useState } from "react";
import { api, ApiError } from "@/lib/api";

export default function SignupPage() {
  const router = useRouter();
  const [form, setForm] = useState({
    company_name: "",
    full_name: "",
    email: "",
    password: "",
  });
  const [err, setErr] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  function update<K extends keyof typeof form>(k: K, v: string) {
    setForm((f) => ({ ...f, [k]: v }));
  }

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setErr(null);
    setBusy(true);
    try {
      await api.post("/api/v1/auth/signup", form);
      router.push("/dashboard");
    } catch (e) {
      setErr(e instanceof ApiError ? e.message : "Signup failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="mx-auto max-w-md px-6 py-20">
      <h1 className="text-2xl font-semibold">Start your 14-day trial</h1>
      <form onSubmit={onSubmit} className="mt-6 flex flex-col gap-3">
        <input
          required
          placeholder="Company name"
          value={form.company_name}
          onChange={(e) => update("company_name", e.target.value)}
          className="rounded-md border px-3 py-2"
        />
        <input
          required
          placeholder="Your full name"
          value={form.full_name}
          onChange={(e) => update("full_name", e.target.value)}
          className="rounded-md border px-3 py-2"
          autoComplete="name"
        />
        <input
          type="email"
          required
          placeholder="you@company.com"
          value={form.email}
          onChange={(e) => update("email", e.target.value)}
          className="rounded-md border px-3 py-2"
          autoComplete="email"
        />
        <input
          type="password"
          required
          minLength={8}
          placeholder="Password (min 8 chars)"
          value={form.password}
          onChange={(e) => update("password", e.target.value)}
          className="rounded-md border px-3 py-2"
          autoComplete="new-password"
        />
        {err ? <p className="text-sm text-red-600">{err}</p> : null}
        <button
          disabled={busy}
          className="rounded-md bg-slate-900 px-4 py-2 text-white disabled:opacity-60"
        >
          {busy ? "Creating…" : "Create account"}
        </button>
      </form>
      <p className="mt-4 text-sm text-slate-600">
        Already have an account? <Link href="/login">Log in</Link>
      </p>
    </main>
  );
}
