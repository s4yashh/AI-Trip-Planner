import { Hero } from "@/components/Hero";

export default function Home() {
  return (
    <main>
      <Hero />
      <section className="mx-auto max-w-6xl px-4 pb-20 sm:px-6">
        <div className="rounded-xl border border-amber-200 bg-amber-50 p-5 text-sm text-amber-800">
          <p className="font-semibold">About this prototype</p>
          <p className="mt-1">
            This app demonstrates a multi-agent trip planning pipeline. Trip
            plans are created by real AI agents running server-side &mdash; the
            recommendations, itinerary, and budget you see come from those
            agents, not from placeholders.
          </p>
        </div>
      </section>
    </main>
  );
}