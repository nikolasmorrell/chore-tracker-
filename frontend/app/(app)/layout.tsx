"use client";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { logout } from "@/lib/auth";

const NAV = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/documents", label: "Documents" },
  { href: "/alerts", label: "Alerts" },
  { href: "/customers", label: "Customers" },
  { href: "/calls", label: "Calls" },
  { href: "/tasks", label: "Tasks" },
  { href: "/billing", label: "Billing" },
  { href: "/settings", label: "Settings" },
];

export default function AppLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  async function onLogout() {
    await logout();
    router.push("/login");
  }
  return (
    <div className="flex min-h-screen">
      <aside className="flex w-60 flex-col border-r bg-white p-4">
        <div className="mb-8 text-lg font-semibold">Sellable</div>
        <nav className="flex flex-1 flex-col gap-1 text-sm">
          {NAV.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className="rounded-md px-3 py-2 hover:bg-slate-100"
            >
              {item.label}
            </Link>
          ))}
        </nav>
        <button
          onClick={onLogout}
          className="mt-4 rounded-md border px-3 py-2 text-left text-sm hover:bg-slate-50"
        >
          Log out
        </button>
      </aside>
      <main className="flex-1 p-8">{children}</main>
    </div>
  );
}
