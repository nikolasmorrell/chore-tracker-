import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Sellable — AI operations for service businesses",
  description:
    "Automate insurance certificates, permits, contracts, and customer calls for roofing, HVAC, plumbing, and contracting companies.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
