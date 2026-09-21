"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const LINKS = [
  { href: "/", label: "Home" },
  { href: "/plan", label: "Plan Trip" },
  { href: "/about", label: "About" },
];

export function Navbar() {
  const pathname = usePathname();

  return (
    <header className="sticky top-0 z-40 border-b border-slate-200/70 bg-[#f8f7f2]/80 backdrop-blur-xl">
      <nav className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3 sm:px-6">
        <Link href="/" className="group flex items-center gap-2.5">
          <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-[#f26b4f] to-[#e04d3b] text-white shadow-lg shadow-orange-900/20 transition-transform group-hover:scale-105">
            <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
              <path d="M12 21s-7-5.1-7-11a7 7 0 0 1 14 0c0 5.9-7 11-7 11z" />
              <circle cx="12" cy="10" r="2.5" fill="currentColor" stroke="none" />
            </svg>
          </span>
          <span className="text-base font-bold tracking-tight text-slate-900">
            AI Trip Planner
          </span>
        </Link>

        <div className="flex items-center gap-1 sm:gap-2">
          {LINKS.map((link) => {
            const active = pathname === link.href;
            return (
              <Link
                key={link.href}
                href={link.href}
                className={`rounded-lg px-3 py-1.5 text-sm font-medium transition-colors ${
                  active
                    ? "bg-[#f26b4f]/10 text-[#c94a37]"
                    : "text-slate-600 hover:bg-slate-900/5 hover:text-slate-900"
                }`}
              >
                {link.label}
              </Link>
            );
          })}
          <Link
            href="/plan"
            className="ml-1 hidden items-center gap-1.5 rounded-lg bg-[#17233d] px-4 py-1.5 text-sm font-semibold text-white shadow-md shadow-slate-900/20 transition-all hover:-translate-y-0.5 hover:bg-[#0b3954] hover:shadow-lg sm:inline-flex"
          >
            Plan My Trip
            <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
              <path d="M5 12h14M13 6l6 6-6 6" />
            </svg>
          </Link>
        </div>
      </nav>
    </header>
  );
}
