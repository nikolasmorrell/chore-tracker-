"use client";
import { Suspense, useState } from "react";
import { useSearchParams } from "next/navigation";
import { api, ApiError } from "@/lib/api";
import { useApi, formatDate } from "@/lib/hooks";
import type { TenantBillingState } from "@/lib/types";

const PLANS = [
  {
    id: "starter" as const,
    label: "Starter",
    price: "$49 / mo",
    features: ["Up to 5 users", "500 documents/mo", "Voice assistant", "Email alerts"],
  },
  {
    id: "pro" as const,
    label: "Pro",
    price: "$149 / mo",
    features: ["Up to 25 users", "Unlimited documents", "Priority support", "Custom integrations"],
  },
  {
    id: "enterprise" as const,
    label: "Enterprise",
    price: "Custom",
    features: ["Unlimited users", "Dedicated CSM", "SLA", "SSO / SAML"],
  },
];

function BillingContent() {
  const params = useSearchParams();
  const flashStatus = params.get("status");

  const { data: billing, isLoading } = useApi<TenantBillingState>("/api/v1/billing/subscription");
  const [busy, setBusy] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);

  async function startCheckout(plan: "starter" | "pro" | "enterprise") {
    setBusy(plan);
    setErr(null);
    try {
      const res = await api.post<{ url: string }>("/api/v1/billing/checkout-session", { plan });
      window.location.href = res.url;
    } catch (e) {
      setErr(e instanceof ApiError ? e.message : String(e));
      setBusy(null);
    }
  }

  async function openPortal() {
    setBusy("portal");
    setErr(null);
    try {
      const res = await api.post<{ url: string }>("/api/v1/billing/portal-session", {});
      window.location.href = res.url;
    } catch (e) {
      setErr(e instanceof ApiError ? e.message : String(e));
      setBusy(null);
    }
  }

  return (
    <>
      <h1 className="text-2xl font-semibold">Billing</h1>

      {flashStatus === "success" && (
        <div className="mt-4 rounded-md bg-emerald-50 px-4 py-3 text-sm text-emerald-800">
          Subscription activated — welcome aboard!
        </div>
      )}
      {flashStatus === "cancel" && (
        <div className="mt-4 rounded-md bg-amber-50 px-4 py-3 text-sm text-amber-800">
          Checkout cancelled. Your plan was not changed.
        </div>
      )}

      {/* Current plan banner */}
      {!isLoading && billing && (
        <section className="mt-6 flex items-center justify-between rounded-lg border bg-white px-5 py-4">
          <div>
            <p className="text-sm font-semibold capitalize">{billing.plan} plan</p>
            <p className="mt-0.5 text-xs text-slate-500">
              Status:{" "}
              <span
                className={
                  billing.status === "active"
                    ? "text-emerald-700"
                    : billing.status === "past_due"
                      ? "text-red-600"
                      : "text-slate-500"
                }
              >
                {billing.status.replace("_", " ")}
              </span>
              {billing.plan === "trial" && billing.trial_ends_at && (
                <> · Trial ends {formatDate(billing.trial_ends_at)}</>
              )}
              {billing.subscription?.current_period_end && billing.plan !== "trial" && (
                <> · Renews {formatDate(billing.subscription.current_period_end)}</>
              )}
            </p>
          </div>
          {billing.has_payment_method && (
            <button
              onClick={openPortal}
              disabled={busy === "portal"}
              className="rounded-md border px-4 py-2 text-sm disabled:opacity-60"
            >
              {busy === "portal" ? "Redirecting…" : "Manage subscription"}
            </button>
          )}
        </section>
      )}

      {/* Plan cards */}
      <div className="mt-6 grid gap-4 md:grid-cols-3">
        {PLANS.map((plan) => {
          const isCurrent = billing?.plan === plan.id;
          return (
            <div
              key={plan.id}
              className={`rounded-lg border bg-white p-5 flex flex-col ${isCurrent ? "ring-2 ring-slate-900" : ""}`}
            >
              <div className="flex items-center justify-between">
                <h2 className="font-semibold">{plan.label}</h2>
                {isCurrent && (
                  <span className="rounded-full bg-slate-900 px-2 py-0.5 text-xs text-white">
                    Current
                  </span>
                )}
              </div>
              <p className="mt-1 text-2xl font-bold">{plan.price}</p>
              <ul className="mt-4 flex-1 space-y-1.5 text-sm text-slate-600">
                {plan.features.map((f) => (
                  <li key={f} className="flex items-start gap-1.5">
                    <span className="mt-0.5 text-emerald-600">✓</span>
                    {f}
                  </li>
                ))}
              </ul>
              <button
                onClick={() => startCheckout(plan.id)}
                disabled={isCurrent || busy === plan.id || plan.id === "enterprise"}
                className="mt-5 w-full rounded-md bg-slate-900 py-2 text-sm text-white disabled:opacity-50"
              >
                {plan.id === "enterprise"
                  ? "Contact sales"
                  : isCurrent
                    ? "Current plan"
                    : busy === plan.id
                      ? "Redirecting…"
                      : `Upgrade to ${plan.label}`}
              </button>
            </div>
          );
        })}
      </div>

      {err && <p className="mt-4 text-sm text-red-600">{err}</p>}
    </>
  );
}

export default function BillingPage() {
  return (
    <Suspense>
      <BillingContent />
    </Suspense>
  );
}
