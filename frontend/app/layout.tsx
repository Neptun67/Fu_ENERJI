import type { Metadata } from "next";

import { NavBar } from "@/components/nav";
import "./globals.css";

export const metadata: Metadata = {
  title: "Liman Yanaşma Planlama",
  description: "Gemilerin rıhtımlara yanaşma planını yöneten operasyon aracı",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="tr">
      <body className="min-h-screen bg-slate-50 text-slate-900">
        <NavBar />
        <main className="mx-auto max-w-6xl px-4 py-8">{children}</main>
      </body>
    </html>
  );
}
