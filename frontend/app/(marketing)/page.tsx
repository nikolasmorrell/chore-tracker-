import Link from "next/link";

export default function LandingPage() {
  return (
    <main className="mx-auto max-w-5xl px-6 py-20">
      <header className="mb-16 flex items-center justify-between">
        <span className="text-xl font-semibold">Serva</span>
        <nav className="flex gap-6 text-sm">
          <Link href="/login">Log in</Link>
          <Link
            href="/signup"
            className="rounded-md bg-brand px-4 py-2 text-white hover:bg-brand-accent"
          >
            Start free trial
          </Link>
        </nav>
      </header>

      <section className="mb-20">
        <h1 className="text-5xl font-bold tracking-tight">
          AI that runs the office work your crew hates.
        </h1>
        <p className="mt-6 max-w-2xl text-lg text-slate-600">
          Serva reads insurance certificates, tracks permit deadlines,
          answers incoming calls, and follows up with customers so your team
          can spend their day on the job — not on paperwork.
        </p>
        <div className="mt-8 flex gap-3">
          <Link
            href="/signup"
            className="rounded-md bg-brand-accent px-5 py-3 text-white"
          >
            Start 14-day trial
          </Link>
          <Link href="#features" className="rounded-md border px-5 py-3">
            See how it works
          </Link>
        </div>
      </section>

      <section id="features" className="grid gap-6 sm:grid-cols-2">
        {FEATURES.map((f) => (
          <div key={f.title} className="rounded-lg border bg-white p-6 shadow-sm">
            <h3 className="text-lg font-semibold">{f.title}</h3>
            <p className="mt-2 text-sm text-slate-600">{f.body}</p>
          </div>
        ))}
      </section>
    </main>
  );
}

const FEATURES = [
  {
    title: "Document automation",
    body: "Upload any PDF or scan. Claude extracts company, policy #, expiration, and flags missing signatures.",
  },
  {
    title: "Expiration alerts",
    body: "Automatic reminders at 30, 14, 7, and 0 days by email + SMS so compliance never lapses.",
  },
  {
    title: "AI phone assistant",
    body: "Answers inbound calls, schedules appointments, transfers emergencies, and logs every transcript.",
  },
  {
    title: "Automated follow-up",
    body: "Generates customer emails, assigns tasks to staff, and summarizes the day for the owner.",
  },
];
