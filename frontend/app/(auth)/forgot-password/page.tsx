"use client";
import Link from "next/link";
import { useState } from "react";
import { api } from "@/lib/api";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [sent, setSent] = useState(false);
  const [busy, setBusy] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    try {
      await api.post("/api/v1/auth/forgot-password", { email });
      setSent(true);
    } finally {
      setBusy(false);
    }
  }

  if (sent) {
    return (
      <main className="mx-auto max-w-md px-6 py-20">
        <h1 className="text-2xl font-semibold">Check your email</h1>
        <p className="mt-4 text-sm text-slate-600">
          If an account exists for {email}, a reset link is on its way.
        </p>
        <Link href="/login" className="mt-6 inline-block text-sm">
          Back to log in
        </Link>
      </main>
    );
  }

  return (
    <main className="mx-auto max-w-md px-6 py-20">
      <h1 className="text-2xl font-semibold">Forgot your password?</h1>
      <form onSubmit={onSubmit} className="mt-6 flex flex-col gap-3">
        <input
          type="email"
          required
          placeholder="you@company.com"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className="rounded-md border px-3 py-2"
          autoComplete="email"
        />
        <button
          disabled={busy}
          className="rounded-md bg-slate-900 px-4 py-2 text-white disabled:opacity-60"
        >
          {busy ? "Sending…" : "Send reset link"}
        </button>
      </form>
    </main>
  );
}
