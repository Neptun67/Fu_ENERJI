import type { Metadata } from "next";
import { Inter } from "next/font/google";

import { NavBar } from "@/components/nav";
import "./globals.css";

// Self-hosted at build time, so the page makes no third-party request at runtime.
const inter = Inter({
  subsets: ["latin"],
  display: "swap",
  variable: "--font-sans",
});

export const metadata: Metadata = {
  title: "Port Berth Planning",
  description: "Operations tool for planning ship-to-berth assignments",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={inter.variable}>
      <body className="min-h-screen font-sans text-slate-900">
        {/* Keyboard users can jump past the navigation (WCAG 2.4.1). */}
        <a
          href="#main"
          className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-50 focus:rounded-md focus:bg-white focus:px-4 focus:py-2 focus:text-sm focus:font-medium focus:text-sea-800 focus:shadow-lg"
        >
          Skip to content
        </a>
        <NavBar />
        <main id="main" className="mx-auto max-w-6xl px-4 py-8">
          {children}
        </main>
      </body>
    </html>
  );
}
