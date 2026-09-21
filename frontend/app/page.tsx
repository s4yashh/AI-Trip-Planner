import Link from "next/link";
import { Hero } from "@/components/Hero";

const STEPS = [
  {
    number: "01",
    title: "Tell us your trip",
    detail:
      "A destination, how many days, your budget, and the interests that matter to you.",
  },
  {
    number: "02",
    title: "Three agents plan it",
    detail:
      "A recommendation agent finds places, an itinerary agent schedules your days, a budget agent checks the costs.",
  },
  {
    number: "03",
    title: "See the plan instantly",
    detail:
      "Ranked places with reasons, a day-by-day timetable, and a transparent budget — plus how each agent fared.",
  },
];

const DESTINATIONS = [
  "Jaipur",
  "Paris",
  "Tokyo",
  "New York",
  "Rome",
  "Bali",
  "Dubai",
  "London",
  "Singapore",
];

export default function Home() {
  return (
    <main>
      <Hero />

      <section className="mx-auto max-w-6xl px-4 py-20 sm:px-6">
        <div className="text-center">
          <p className="text-xs font-semibold uppercase tracking-widest text-emerald-700">
            How it works
          </p>
          <h2 className="mt-2 font-display text-4xl font-semibold tracking-tight text-slate-900">
            From a few details to a full trip
          </h2>
        </div>

        <div className="mt-10 grid grid-cols-1 gap-6 md:grid-cols-3">
          {STEPS.map((step) => (
            <div
              key={step.number}
              className="group relative overflow-hidden rounded-2xl border border-slate-200 bg-white p-7 shadow-sm transition-all hover:-translate-y-1 hover:shadow-xl hover:shadow-emerald-900/10"
            >
              <div
                className="absolute -right-6 -top-6 h-24 w-24 rounded-full bg-gradient-to-br from-emerald-500/10 to-teal-500/10 transition-transform duration-500 group-hover:scale-125"
                aria-hidden="true"
              />
              <p className="font-display text-sm font-semibold text-emerald-600">
                {step.number}
              </p>
              <h3 className="mt-2 text-lg font-bold text-slate-900">{step.title}</h3>
              <p className="mt-2 text-sm leading-relaxed text-slate-600">
                {step.detail}
              </p>
            </div>
          ))}
        </div>
      </section>

      <section className="bg-white py-16">
        <div className="mx-auto max-w-6xl px-4 sm:px-6">
          <div className="flex flex-col items-start justify-between gap-4 sm:flex-row sm:items-center">
            <div>
              <p className="text-xs font-semibold uppercase tracking-widest text-emerald-700">
                Destinations
              </p>
              <h2 className="mt-2 font-display text-3xl font-semibold tracking-tight text-slate-900">
                Explore with us
              </h2>
            </div>
            <p className="max-w-sm text-sm text-slate-500">
              Every destination has hand-authored places in the dataset, ready
              to be ranked by the agents.
            </p>
          </div>
          <ul className="mt-8 flex flex-wrap gap-3">
            {DESTINATIONS.map((destination) => (
              <li
                key={destination}
                className="flex items-center gap-2 rounded-full border border-slate-200 bg-slate-50 px-4 py-2 text-sm font-medium text-slate-700 transition-colors hover:border-emerald-500 hover:text-emerald-700"
              >
                <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" aria-hidden="true" />
                {destination}
              </li>
            ))}
          </ul>
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-4 py-20 sm:px-6">
        <div className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-emerald-800 via-emerald-700 to-teal-700 px-8 py-14 text-center text-white">
          <div
            className="pointer-events-none absolute -left-16 -top-16 h-64 w-64 rounded-full bg-white/10 blur-3xl"
            aria-hidden="true"
          />
          <h2 className="relative font-display text-4xl font-semibold tracking-tight">
            Ready to see your plan?
          </h2>
          <p className="relative mx-auto mt-3 max-w-xl text-emerald-100/90">
            Open the planner, choose a destination and interests, and watch the
            agents build your itinerary in seconds.
          </p>
          <Link
            href="/plan"
            className="relative mt-7 inline-flex items-center gap-2 rounded-xl bg-white px-7 py-3.5 font-semibold text-emerald-900 shadow-xl shadow-black/20 transition-transform hover:-translate-y-0.5"
          >
            Open the Planner
            <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
              <path d="M5 12h14M13 6l6 6-6 6" />
            </svg>
          </Link>
        </div>
      </section>
    </main>
  );
}