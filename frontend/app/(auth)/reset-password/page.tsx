"use client";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { Suspense, useState } from "react";
import { api, ApiError } from "@/lib/api";

function ResetForm() {
  const router = useRouter();
  const params = useSearchParams();
  const token = params.get("token") ?? "";
  const [pw, setPw] = useState("");
  const [err, setErr] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setErr(null);
    setBusy(true);
    try {
      await api.post("/api/v1/auth/reset-password", {
        token,
        new_password: pw,
      });
      router.push("/login");
    } catch (e) {
      setErr(e instanceof ApiError ? e.message : "Reset failed");
    } finally {
      setBusy(false);
    }
  }

  if (!token) {
    return <p className="mt-4 text-sm text-red-600">Missing reset token.</p>;
  }

  return (
    <form onSubmit={onSubmit} className="mt-6 flex flex-col gap-3">
      <input
        type="password"
        required
        minLength={8}
        placeholder="New password"
        value={pw}
        onChange={(e) => setPw(e.target.value)}
        className="rounded-md border px-3 py-2"
        autoComplete="new-password"
      />
      {err ? <p className="text-sm text-red-600">{err}</p> : null}
      <button
        disabled={busy}
        className="rounded-md bg-slate-900 px-4 py-2 text-white disabled:opacity-60"
      >
        {busy ? "Resetting…" : "Set new password"}
      </button>
    </form>
  );
}

export default function ResetPasswordPage() {
  return (
    <main className="mx-auto max-w-md px-6 py-20">
      <h1 className="text-2xl font-semibold">Reset your password</h1>
      <Suspense fallback={null}>
        <ResetForm />
      </Suspense>
      <Link href="/login" className="mt-4 inline-block text-sm">
        Back to log in
      </Link>
    </main>
  );
}
