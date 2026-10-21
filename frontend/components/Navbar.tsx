"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import { Icon, type IconName } from "@/components/ui/Icon";

const LINKS: { href: string; label: string; icon: IconName }[] = [
  { href: "/", label: "Home", icon: "home" },
  { href: "/plan", label: "Plan Trip", icon: "map" },
  { href: "/group-plan", label: "Group Trip", icon: "users" },
  { href: "/flights", label: "Flights", icon: "plane" },
  { href: "/hotels", label: "Hotels", icon: "bed" },
];

function isActive(pathname: string, href: string) {
  return href === "/" ? pathname === "/" : pathname === href || pathname.startsWith(`${href}/`);
}

export function Navbar() {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);
  const [openedAt, setOpenedAt] = useState(pathname);
  // Close the mobile menu after navigation.
  if (open && openedAt !== pathname) setOpen(false);

  return (
    <header className="site-header">
      <nav className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-4 py-3 sm:px-6" aria-label="Main">
        <Link href="/" className="group flex shrink-0 items-center gap-2.5">
          <span className="brand-mark"><Icon name="pin" className="h-5 w-5" /></span>
          <span className="text-base font-bold tracking-tight text-[var(--ink)]">AI Trip Planner</span>
        </Link>

        <ul className="hidden items-center gap-1 md:flex">
          {LINKS.map((link) => (
            <li key={link.href}>
              <Link href={link.href} aria-current={isActive(pathname, link.href) ? "page" : undefined} className="nav-link">
                <Icon name={link.icon} className="h-4 w-4" />{link.label}
              </Link>
            </li>
          ))}
        </ul>

        <button type="button" className="nav-toggle md:hidden" aria-expanded={open} aria-controls="mobile-menu"
          aria-label={open ? "Close menu" : "Open menu"} onClick={() => { setOpen((value) => !value); setOpenedAt(pathname); }}>
          <Icon name={open ? "close" : "menu"} className="h-5 w-5" />
        </button>
      </nav>

      {open && (
        <ul id="mobile-menu" className="mobile-menu md:hidden">
          {LINKS.map((link) => (
            <li key={link.href}>
              <Link href={link.href} aria-current={isActive(pathname, link.href) ? "page" : undefined} className="nav-link w-full"
                onClick={() => setOpen(false)}>
                <Icon name={link.icon} className="h-5 w-5" />{link.label}
              </Link>
            </li>
          ))}
          <li><Link href="/about" className="nav-link w-full" onClick={() => setOpen(false)}><Icon name="info" className="h-5 w-5" />About</Link></li>
        </ul>
      )}
    </header>
  );
}
