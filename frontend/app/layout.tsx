import type { Metadata } from "next";
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
        <footer className="border-t border-[#e9e2d3] bg-white/60 py-8">
          <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-2 px-4 text-sm text-slate-500 sm:flex-row sm:px-6">
            <p>AI Trip Planner · Your personal travel studio.</p>
            <p>Live information. Local intelligence.</p>
          </div>
        </footer>
      </body>
    </html>
  );
}
