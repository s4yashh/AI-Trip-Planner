import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";
import { Navbar } from "@/components/Navbar";

export const metadata: Metadata = {
  title: {
    default: "AI Trip Planner",
    template: "%s | AI Trip Planner",
  },
  description:
    "Plan personalized trips with a multi-agent AI system: recommendations, itineraries, and budgets.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html
      lang="en"
      className="h-full antialiased"
    >
      <body className="flex min-h-full flex-col">
        <Navbar />
        <div className="flex-1">{children}</div>
        <footer className="site-footer">
          <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-3 px-4 text-sm sm:flex-row sm:px-6">
            <p>AI Trip Planner · Your personal travel studio.</p>
            <nav aria-label="Footer" className="flex flex-wrap justify-center gap-x-5 gap-y-1">
              <Link href="/plan">Plan Trip</Link><Link href="/group-plan">Group Trip</Link><Link href="/flights">Flights</Link>
              <Link href="/hotels">Hotels</Link><Link href="/about">About</Link>
            </nav>
          </div>
        </footer>
      </body>
    </html>
  );
}
