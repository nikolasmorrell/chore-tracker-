import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = {
  title: "Family Chore Tracker",
  description: "Track chores and earn money!",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <nav className="bg-blue-600 text-white shadow-md">
          <div className="max-w-5xl mx-auto px-4 py-3 flex items-center gap-6">
            <Link href="/" className="text-xl font-bold">
              Chore Tracker
            </Link>
            <Link href="/chores" className="hover:underline">
              Chores
            </Link>
            <Link href="/log" className="hover:underline">
              Weekly Log
            </Link>
            <Link href="/dashboard" className="hover:underline">
              Dad&apos;s Dashboard
            </Link>
          </div>
        </nav>
        <main className="max-w-5xl mx-auto px-4 py-6">{children}</main>
      </body>
    </html>
  );
}
