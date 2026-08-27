"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const links = [
  { href: "/ships", label: "Ships" },
  { href: "/berths", label: "Berths" },
  { href: "/plan", label: "Plan" },
];

export function NavBar() {
  const pathname = usePathname();
  return (
    <header className="sticky top-0 z-40 border-b border-sea-100 bg-white/85 backdrop-blur">
      <nav className="mx-auto flex max-w-6xl items-center gap-8 px-4">
        <Link href="/" className="flex items-center gap-2.5 py-3.5">
          <span aria-hidden="true" className="grid h-8 w-8 place-items-center rounded-lg bg-sea-800">
            {/* Anchor mark */}
            <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="#fff" strokeWidth="1.9" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="12" cy="5" r="2.2" />
              <path d="M12 7.2V21" />
              <path d="M8 10h8" />
              <path d="M4.5 15.5a7.5 7.5 0 0 0 15 0" />
            </svg>
          </span>
          <span className="text-sm font-semibold tracking-tight text-sea-900">
            Port Planning
          </span>
        </Link>
        <ul className="flex items-center gap-1">
          {links.map((link) => {
            const active =
              pathname === link.href || pathname.startsWith(`${link.href}/`);
            return (
              <li key={link.href}>
                <Link
                  href={link.href}
                  aria-current={active ? "page" : undefined}
                  className={`block rounded-md px-3 py-1.5 text-sm font-medium transition-colors ${
                    active
                      ? "bg-sea-100 text-sea-800"
                      : "text-slate-600 hover:bg-slate-100 hover:text-slate-900"
                  }`}
                >
                  {link.label}
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>
    </header>
  );
}
