"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const links = [
  { href: "/ships", label: "Gemiler" },
  { href: "/berths", label: "Rıhtımlar" },
  { href: "/plan", label: "Plan" },
];

export function NavBar() {
  const pathname = usePathname();
  return (
    <header className="border-b border-slate-200 bg-white">
      <nav className="mx-auto flex max-w-6xl items-center gap-8 px-4">
        <Link href="/" className="flex items-center gap-2 py-4">
          <span className="grid h-7 w-7 place-items-center rounded bg-teal-700 text-xs font-bold text-white">
            L
          </span>
          <span className="text-sm font-semibold tracking-tight text-slate-900">
            Liman Planlama
          </span>
        </Link>
        <div className="flex items-center gap-1">
          {links.map((link) => {
            const active =
              pathname === link.href || pathname.startsWith(`${link.href}/`);
            return (
              <Link
                key={link.href}
                href={link.href}
                className={`rounded-md px-3 py-1.5 text-sm font-medium transition-colors ${
                  active
                    ? "bg-teal-50 text-teal-800"
                    : "text-slate-600 hover:bg-slate-100"
                }`}
              >
                {link.label}
              </Link>
            );
          })}
        </div>
      </nav>
    </header>
  );
}
